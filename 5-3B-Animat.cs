// Assets/Scripts/FSM/Animat.cs
using System.Collections.Generic;
using UnityEngine;

public class Animat : MonoBehaviour
{
    [Header("Initial Beliefs (Inspector)")]
    public float hunger = 10f;
    public float thirst = 10f;
    public float fatigue = 5f;
    public float temperature = 37f;
    public float boredom = 0f;

    [Header("Action Timing (seconds)")]
    public float planExecutionDuration = 3.0f; // how long a plan takes to execute (tunable)
    public float afterActionCoolDown = 0.5f;    // short pause after an action completed

    [Header("Debug")]
    public bool enableDebugLogs = false;
    public string currentIntention;
    public string currentPlan;

    private AnimatBDI bdi;

    // execution state
    private bool actionInProgress = false;
    private float actionTimer = 0f;
    private List<string> currentPlanSteps = null;
    private string currentFinalAction = null;
    private float cooldownTimer = 0f;

    void Start()
    {
        var beliefs = new List<Dictionary<string, float>>
        {
            new Dictionary<string, float>
            {
                { "hunger", hunger },
                { "thirst", thirst },
                { "fatigue", fatigue },
                { "temperature", temperature },
                { "boredom", boredom }
            }
        };

        bdi = new AnimatBDI(beliefs);
    }

    void Update()
    {
        if (bdi == null) return;

        // Natural metabolism always ticks every update
        bdi.MetabolismTick();

        // If an action is in progress, count down
        if (actionInProgress)
        {
            actionTimer -= Time.deltaTime;

            if (enableDebugLogs)
                Debug.Log($"[Animat] Executing {currentFinalAction}, time left {actionTimer:F2}s");

            if (actionTimer <= 0f)
            {
                // Action completed -> apply effect ONCE
                if (!string.IsNullOrEmpty(currentFinalAction))
                {
                    bdi.ApplyFinalActionEffect(currentFinalAction);
                }

                // finish action and start cooldown
                actionInProgress = false;
                cooldownTimer = afterActionCoolDown;
                // clear current intention so deliberation can re-evaluate next frame
                bdi.currentIntention = null;
            }

            // Update inspector view
            SyncFromBeliefsToInspector();
            return; // skip deliberation while action executing
        }

        // If in cooldown after action, count down and skip deliberation
        if (cooldownTimer > 0f)
        {
            cooldownTimer -= Time.deltaTime;
            SyncFromBeliefsToInspector();
            return;
        }

        // Normal BDI cycle (no action in progress)
        var desires = bdi.GenerateDesires();
        var intention = bdi.Deliberate(desires);
        var plan = bdi.MeansEnds(intention);

        // If there's a plan and it's different from currentPlanSteps, start it
        if (plan != null && plan.Count > 0)
        {
            // start executing the plan (we only simulate the final action effect after duration)
            currentPlanSteps = plan;
            currentFinalAction = plan[plan.Count - 1];
            StartActionExecution(currentFinalAction);
        }
        else
        {
            // no plan -> idle or explore behavior could be implemented here
            currentPlanSteps = null;
            currentFinalAction = null;
        }

        // Update debug UI info
        currentIntention = (bdi.currentIntention != null) ? bdi.GetActionName((int)bdi.currentIntention.representation["action"]) : "None";
        currentPlan = plan != null ? string.Join(" -> ", plan) : "None";

        SyncFromBeliefsToInspector();

        if (enableDebugLogs)
        {
            // helpful diagnostics
            Debug.Log($"[Animat] desires:{desires.Count} intention:{currentIntention} plan:{currentPlan} hunger:{bdi.beliefs[0]["hunger"]:F1} thirst:{bdi.beliefs[0]["thirst"]:F1} fatigue:{bdi.beliefs[0]["fatigue"]:F1} boredom:{bdi.beliefs[0]["boredom"]:F1}");
        }
    }

    void StartActionExecution(string finalAction)
    {
        if (string.IsNullOrEmpty(finalAction)) return;
        actionInProgress = true;
        actionTimer = planExecutionDuration;
        if (enableDebugLogs)
            Debug.Log($"[Animat] Starting action '{finalAction}' for {planExecutionDuration} seconds");
    }

    void SyncFromBeliefsToInspector()
    {
        var m = bdi.beliefs[0];
        hunger = m["hunger"];
        thirst = m["thirst"];
        fatigue = m["fatigue"];
        temperature = m["temperature"];
        boredom = m["boredom"];
    }
}
