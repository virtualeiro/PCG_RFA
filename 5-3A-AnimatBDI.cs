using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using System;

public class BDI
{
    public List<Dictionary<string, float>> beliefs;
    public List<Attitude> desires;
    public List<Attitude> intentions;

    public BDI(List<Dictionary<string, float>> beliefs)
    {
        this.beliefs = beliefs;
        this.desires = new List<Attitude>();
        this.intentions = new List<Attitude>();
    }
}

[Serializable]
public class Attitude
{
    public Enum label;
    public Dictionary<string, float> representation;

    public Attitude(Enum label, Dictionary<string, float> representation)
    {
        this.label = label;
        this.representation = representation;
    }
}

public enum IntentionType
{
    PerformPlan
}
//-----------------------------------------------

public class AnimatBDI : BDI
{
    public Attitude currentIntention;

    // --- Thresholds (tune these)
    public float thirstOn = 40;
    public float thirstOff = 25;

    public float hungerOn = 30;
    public float hungerOff = 15;

    public float fatigueOn = 30;
    public float fatigueOff = 15;

    // --- Metabolic targets ---
    public Dictionary<string, float> targets;

    // --- Priority weights ---
    public Dictionary<string, float> priority;

    // --- Plans for each intention ---
    public Dictionary<string, List<string>> plans;

    // --- Execution guard (so effects are not applied every frame) ---
    // The brain itself does not hold timers — the MonoBehaviour will control timing.
    public AnimatBDI(List<Dictionary<string, float>> beliefs) : base(beliefs)
    {
        currentIntention = null;

        priority = new Dictionary<string, float>
        {
            { "Drink", 4 },
            { "Eat", 4 },
            { "Rest", 2 },
            { "CoolDown", 5 },
            { "WarmUp", 3 },
            { "Explore", 0.4f }
        };

        plans = new Dictionary<string, List<string>>
        {
            { "Eat", new List<string>{ "GoToKitchen", "EatFood" } },
            { "Drink", new List<string>{ "GoToWater", "DrinkWater" } },
            { "Rest", new List<string>{ "GoToBed", "LieDown", "Sleep" } },
            { "CoolDown", new List<string>{ "MoveToShade", "CoolDownBody" } },
            { "WarmUp", new List<string>{ "FindHeatSource", "WarmBody" } },
            { "Explore", new List<string>{ "LookAround", "WalkRandomly" } }
        };

        targets = new Dictionary<string, float>
        {
            { "hunger", 20 },
            { "thirst", 20 },
            { "fatigue", 10 },
            { "temperature", 37 }
        };
    }

    // ------------------------------------------------
    // Helper
    // ------------------------------------------------
    public float Drive(float current, float target)
    {
        return Mathf.Max(0f, current - target);
    }

    // ------------------------------------------------
    // DESIRE GENERATION
    // ------------------------------------------------
    public List<Dictionary<string, float>> GenerateDesires()
    {
        Dictionary<string, float> m = beliefs[0];
        List<Dictionary<string, float>> desires = new List<Dictionary<string, float>>();

        // --- Hunger ---
        float hungerDrive = Drive(m["hunger"], targets["hunger"]);
        if (m["hunger"] > hungerOn || (currentIntention != null && currentIntention.representation["action"] == 0 && m["hunger"] > hungerOff))
        {
            desires.Add(new Dictionary<string, float>
            {
                { "action", 0 },
                { "urgency", hungerDrive * priority["Eat"] }
            });
        }

        // --- Thirst ---
        float thirstDrive = Drive(m["thirst"], targets["thirst"]);
        if (m["thirst"] > thirstOn || (currentIntention != null && currentIntention.representation["action"] == 1 && m["thirst"] > thirstOff))
        {
            desires.Add(new Dictionary<string, float>
            {
                { "action", 1 },
                { "urgency", thirstDrive * priority["Drink"] }
            });
        }

        // --- Fatigue ---
        float fatigueDrive = Drive(m["fatigue"], targets["fatigue"]);
        if (m["fatigue"] > fatigueOn || (currentIntention != null && currentIntention.representation["action"] == 2 && m["fatigue"] > fatigueOff))
        {
            desires.Add(new Dictionary<string, float>
            {
                { "action", 2 },
                { "urgency", fatigueDrive * priority["Rest"] }
            });
        }

        // --- Temperature ---
        if (m["temperature"] > 38f)
        {
            desires.Add(new Dictionary<string, float>
            {
                { "action", 3 },  // CoolDown
                { "urgency", (m["temperature"] - targets["temperature"]) * priority["CoolDown"] }
            });
        }
        else if (m["temperature"] < 36f)
        {
            desires.Add(new Dictionary<string, float>
            {
                { "action", 4 },  // WarmUp
                { "urgency", (targets["temperature"] - m["temperature"]) * priority["WarmUp"] }
            });
        }

        // --- Explore ---
        if (m["boredom"] > 40f)
        {
            desires.Add(new Dictionary<string, float>
            {
                { "action", 5 },
                { "urgency", m["boredom"] * priority["Explore"] }
            });
        }

        return desires;
    }

    // ------------------------------------------------
    // DELIBERATE
    // ------------------------------------------------
    public Attitude Deliberate(List<Dictionary<string, float>> desires)
    {
        if (desires == null || desires.Count == 0)
        {
            currentIntention = null;
            return null;
        }

        // If current intention still present, update its urgency and keep it
        if (currentIntention != null)
        {
            float actionID = currentIntention.representation["action"];
            foreach (var d in desires)
            {
                if (d["action"] == actionID)
                {
                    currentIntention.representation["urgency"] = d["urgency"];
                    return currentIntention;
                }
            }
        }

        // Pick strongest desire
        var strongest = desires.OrderByDescending(d => d["urgency"]).First();

        currentIntention = new Attitude(
            IntentionType.PerformPlan,
            new Dictionary<string, float>
            {
                { "action", strongest["action"] },
                { "urgency", strongest["urgency"] }
            }
        );

        return currentIntention;
    }

    // ------------------------------------------------
    // MEANS-END REASONING
    // ------------------------------------------------
    public List<string> MeansEnds(Attitude intention)
    {
        if (intention == null) return null;
        string actionName = GetActionName((int)intention.representation["action"]);
        return plans[actionName];
    }

    // ------------------------------------------------
    // EXECUTION EFFECTS (called once at completion of an action)
    // ------------------------------------------------
    public void ApplyFinalActionEffect(string finalAction)
    {
        Dictionary<string, float> m = beliefs[0];

        if (finalAction == "DrinkWater")
            m["thirst"] = Mathf.Max(0f, m["thirst"] - 180f);
        else if (finalAction == "EatFood")
            m["hunger"] = Mathf.Max(0f, m["hunger"] - 180f);
        else if (finalAction == "Sleep")
            m["fatigue"] = Mathf.Max(0f, m["fatigue"] - 60f);
        else if (finalAction == "CoolDownBody")
            m["temperature"] -= 3.0f;
        else if (finalAction == "WarmBody")
            m["temperature"] += 3.0f;

        // clamp after action effect
        m["hunger"] = Mathf.Clamp(m["hunger"], 0f, 200f);
        m["thirst"] = Mathf.Clamp(m["thirst"], 0f, 200f);
        m["fatigue"] = Mathf.Clamp(m["fatigue"], 0f, 200f);
        m["temperature"] = Mathf.Clamp(m["temperature"], 34f, 42f);
        m["boredom"] = Mathf.Clamp(m["boredom"], 0f, 200f);
    }

    // ------------------------------------------------
    // Natural metabolism (called every update)
    // ------------------------------------------------
    public void MetabolismTick()
    {
        Dictionary<string, float> m = beliefs[0];

        m["hunger"] += 0.05f;   // slower increase
        m["thirst"] += 0.06f;
        m["fatigue"] += 0.025f;
        m["temperature"] += 0.0005f;
        m["boredom"] += 0.02f;

        // clamp
        m["hunger"] = Mathf.Clamp(m["hunger"], 0f, 200f);
        m["thirst"] = Mathf.Clamp(m["thirst"], 0f, 200f);
        m["fatigue"] = Mathf.Clamp(m["fatigue"], 0f, 200f);
        m["temperature"] = Mathf.Clamp(m["temperature"], 34f, 42f);
        m["boredom"] = Mathf.Clamp(m["boredom"], 0f, 200f);
    }

    // ------------------------------------------------
    public string GetActionName(int actionIndex)
    {
        return new string[]
        {
            "Eat",      //0
            "Drink",    //1
            "Rest",     //2
            "CoolDown", //3
            "WarmUp",   //4
            "Explore"   //5
        }[actionIndex];
    }
}
