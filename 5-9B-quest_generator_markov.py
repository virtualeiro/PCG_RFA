import random

# ---------------------------
# CITY GRAPH
# ---------------------------

city = {
    "Tavern": ["Market", "Temple", "Alley"],
    "Market": ["Tavern", "Gate", "Alley"],
    "Temple": ["Tavern", "Garden"],
    "Alley": ["Market", "Warehouse"],
    "Warehouse": ["Alley", "Harbor"],
    "Harbor": ["Warehouse", "Gate"],
    "Gate": ["Market", "Harbor"],
    "Garden": ["Temple"]
}

# ---------------------------
# MARKOV QUEST STATES
# ---------------------------

markov_chain = {
    "start": ["travel", "talk"],
    "travel": ["talk", "explore", "fight"],
    "talk": ["travel", "investigate", "fight"],
    "explore": ["find", "fight"],
    "investigate": ["travel", "fight", "find"],
    "fight": ["find", "travel"],
    "find": ["return"],
    "return": ["end"]
}

# ---------------------------
# NARRATIVE TEMPLATES
# ---------------------------

narrative = {
    "travel": [
        "You travel to the {}.",
        "You make your way through the streets to the {}."
    ],
    "talk": [
        "You talk to a suspicious stranger in the {}.",
        "A local informant shares rumors in the {}."
    ],
    "explore": [
        "You explore the shadows of the {}.",
        "You search carefully around the {}."
    ],
    "investigate": [
        "You investigate clues hidden in the {}.",
        "You examine strange signs in the {}."
    ],
    "fight": [
        "A fight breaks out in the {}!",
        "Enemies ambush you in the {}."
    ],
    "find": [
        "You discover the missing artifact in the {}.",
        "You find an important clue in the {}."
    ],
    "return": [
        "You return to the Tavern to report your findings."
    ]
}

# ---------------------------
# MARKOV TRANSITION
# ---------------------------

def next_state(state):
    return random.choice(markov_chain[state])

# ---------------------------
# QUEST GENERATOR
# ---------------------------

def generate_quest(max_steps=10):

    state = "start"
    location = "Tavern"

    print("\n--- Procedural Quest ---\n")
    print("Quest begins at the Tavern.\n")

    steps = 0

    while state != "end" and steps < max_steps:

        state = next_state(state)

        if state == "travel":
            location = random.choice(city[location])

        if state in narrative:
            line = random.choice(narrative[state]).format(location)
            print(line)

        steps += 1

    print("\nQuest complete.\n")

# ---------------------------
# RUN
# ---------------------------

generate_quest()