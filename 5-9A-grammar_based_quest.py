import random

grammar = {
    "Quest": [["Hero", "Mission", "Reward"]],

    "Hero": [["Knight"], ["Scientist"], ["Explorer"]],

    "Mission": [["Travel", "Task", "Return"]],

    "Travel": [["Go to", "Location"]],

    "Task": [["FightEnemy"], ["SolvePuzzle"], ["RetrieveItem"]],

    "Return": [["Return to", "King"]],

    "Reward": [["Receive", "Treasure"]],

    "Location": [["the forest"], ["the ruins"], ["the cave"]],

    "FightEnemy": [["defeat the dragon"]],
    "SolvePuzzle": [["solve the ancient puzzle"]],
    "RetrieveItem": [["recover the lost artifact"]],

    "Treasure": [["gold"], ["a magic sword"], ["ancient knowledge"]]
}

def expand(symbol):
    if symbol not in grammar:
        return symbol

    rule = random.choice(grammar[symbol])
    return " ".join(expand(s) for s in rule)

print(expand("Quest"))