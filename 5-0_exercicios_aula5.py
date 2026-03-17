#EXERCÍCIO 2 
# LSYSTEMS 
#1-Change the axiom 
#2- and rules to create different patterns.
"""
import turtle

def lsystem(axiom, rules, iterations):
    current = axiom
    
    for i in range(iterations):
        next_string = ""
        for char in current:
            next_string += rules.get(char, char)
        current = next_string
    
    return current

axiom = "F"
rules = {
    "F": "F+F-F-F+F"
}

LSystem_result = lsystem(axiom, rules, 4)


def draw_lsystem(commands, angle=90, step=6):
    for c in commands:
        if c == "F":
            turtle.forward(step)
        elif c == "+":
            turtle.right(angle)
        elif c == "-":
            turtle.left(angle)

commands = LSystem_result

turtle.speed(0)
turtle.penup()
turtle.goto(-250, 150)
turtle.pendown()
draw_lsystem(commands)
turtle.done()
"""

#SHAPES
"""
import random
import pygame

def subdivide(square):
    x, y, size = square

    if random.random() < 0.5:
        return [
            (x, y, size/2),
            (x+size/2, y, size/2),
            (x, y+size/2, size/2),
            (x+size/2, y+size/2, size/2)
        ]
    else:
        return [square]

squares = [(0, 0, 100)]

for i in range(3):
    new_squares = []
    for s in squares:
        new_squares.extend(subdivide(s))
    squares = new_squares

# Draw with pygame
pygame.init()
win_size = 200
win = pygame.display.set_mode((win_size, win_size))
win.fill((255, 255, 255))

for x, y, size in squares:
    rect = pygame.Rect(int(x), int(y), int(size), int(size))
    pygame.draw.rect(win, (0, 0, 0), rect, 1)

pygame.display.flip()

# Wait until window is closed
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
"""
#LOOT
"""
#1.	Generate loot for every treasure room
#2.	Track how many legendary items appear

import random

loot = {
    "Gold": 50,
    "Potion": 30,
    "Sword": 15,
    "Legendary Sword": 5
}

items = list(loot.keys())
weights = list(loot.values())

def get_loot():
    return random.choices(items, weights)[0]

for i in range(10):
    print(get_loot())
"""

"""
#Chest
import random

common = ["Gold", "Potion", "Arrow"]
rare = ["Magic Sword", "Magic Staff"]
epic = ["Dragon Armor"]

def open_chest():
    r = random.random()
    
    if r < 0.70:
        return random.choice(common)
    elif r < 0.95:
        return random.choice(rare)
    else:
        return random.choice(epic)

for i in range(20):
    print(open_chest())
"""


#Dungeon
#1.	Add loot tables to treasure rooms.
#2.	Generate quests with grammar rules.
#Example output:
#Room 1: monster
#Room 2: empty
#Room 3: treasure (gold)
#Room 4: puzzle
#tasks
#3.	Ensure only one boss room
#4.	Guarantee at least 2 treasure rooms
#5.	Add entrance and exit

"""
#3Create a procedural fantasy generator that outputs:
#Quest: The wizard must defeat the dragon
#Dungeon: 12 rooms
#Boss loot: Legendary sword
#Map: procedurally generated
import random

grammar = {
    "S": [["Room", "Corridor", "Room"]],
    "Room": [["treasure room"], ["monster room"], ["puzzle room"], ["empty room"]],
    "Corridor": [["straight corridor"], ["left turn corridor"], ["right turn corridor"]]
}

def generate(symbol):
    if symbol not in grammar:
        return symbol
    
    rule = random.choice(grammar[symbol])
    return " ".join(generate(s) for s in rule)

for i in range(5):
    print(generate("S"))
"""

#PASSO2 DUNGEON C LOOT
"""
import random

grammar = {
    "S": [["Room", "Corridor", "Room"]],
    "Room": [["treasure room"], ["monster room"], ["puzzle room"], ["empty room"]],
    "Corridor": [["straight corridor"], ["left turn corridor"], ["right turn corridor"]]
}

loot_tables = {
    "treasure room": ["Gold", "Magic Sword", "Legendary Armor"],
    "monster room": ["Gold", "Potion", "Iron Sword"],
    "puzzle room": ["Ancient Scroll", "Gem", "Gold"],
    "empty room": []
}

def generate(symbol):
    if symbol not in grammar:
        return symbol
    
    rule = random.choice(grammar[symbol])
    return " ".join(generate(s) for s in rule)

def get_room_loot(room_type):
    loot = loot_tables.get(room_type, [])
    return random.choice(loot) if loot else "nothing"

for i in range(5):
    room = generate("S")
    # Extract room type for loot lookup
    room_types = [rt for rt in loot_tables.keys() if rt in room]
    if room_types:
        loot = get_room_loot(room_types[0])
        print(f"{room} - Loot: {loot}")
    else:
        print(room)
"""


#QUEST
"""
import random

grammar = {
    "S": [["Hero", "Action", "Creature"]],
    "Hero": [["The knight"], ["The wizard"], ["The rogue"]],
    "Action": [["defeats"], ["escapes from"], ["befriends"]],
    "Creature": [["a dragon"], ["an orc"], ["a giant spider"]]
}

def generate(symbol):
    if symbol not in grammar:
        return symbol
    
    rule = random.choice(grammar[symbol])
    return " ".join(generate(s) for s in rule)

for i in range(5):
    print(generate("S"))
"""




"""
#EXERCICIO 3 CONTEXT FREE GRAMMAR QUEST GENERATOR 
#Example output
# tasks
#1.	Add locations (forest, dungeon, castle)
#2.	Add quest rewards
#3.	Generate 5 different quests
import random

grammar = {
    "S": [["Hero", "must", "Action", "the", "Enemy"]],
 #RFA   "S": [["Hero", "must", "Action", "the", "Enemy", "in", "the", "Location", "for", "Reward"]],
    "Hero": [["knight"], ["wizard"], ["rogue"], ["ranger"]],
    "Action": [["defeat"], ["rescue"], ["find"], ["protect"]],
    "Enemy": [["dragon"], ["necromancer"], ["goblin king"], ["giant spider"]]
    
    #RFA
    #"Location": [["forest"], ["dungeon"], ["castle"], ["ancient ruins"], ["mountain pass"]],
    #
    #"Reward": [
    #    ["gold"],
    #    ["a powerful artifact"],
    #    ["the king's favor"],
    #    ["ancient knowledge"],
    #    ["a legendary weapon"]
    #]
}

def generate(symbol):
    if symbol not in grammar:
        return symbol

    rule = random.choice(grammar[symbol])
    return " ".join(generate(s) for s in rule)

print("Quest:", generate("S"))
"""

"""
#QUEST GENERATOR WITH CONTEXT-SENSITIVITY
import random

grammar = {
    "S": [["Hero", "must", "Action", "the", "Enemy"]],
    "Hero": [["knight"], ["wizard"], ["rogue"], ["ranger"]],
    "Enemy": [["dragon"], ["necromancer"], ["goblin king"], ["giant spider"]],
    "Action": [["defeat"], ["slay"], ["investigate"], ["negotiate"], ["avoid"]]
}

action_constraints = {
    "dragon": ["defeat", "slay"],
    "necromancer": ["defeat", "investigate"],
    "goblin king": ["defeat", "negotiate"],
    "giant spider": ["defeat", "avoid"]
}

def generate(symbol, context):
    if symbol not in grammar:
        return symbol

    # Special handling for Enemy
    # We want to store the chosen enemy in the context for later use in Action
    # This allows us to ensure that the Action is appropriate for the chosen Enemy
    # For example, if we choose "dragon" as the Enemy, 
    # we want to ensure that the Action is either "defeat" or "slay"
    # We can achieve this by first generating the Enemy, 
    # storing it in the context, and then when we generate the Action, 
    # we can look up the valid actions for that enemy and choose from them
    if symbol == "Enemy":
        # Randomly choose an enemy and store it in the context
        choice = random.choice(grammar["Enemy"])[0]
        context["Enemy"] = choice
        return choice

    # Special handling for Action (depends on Enemy)
    if symbol == "Action":
        # Look up the chosen enemy in the context and 
        # get the valid actions for that enemy
        enemy = context.get("Enemy", None)
        # If we have an enemy and it has constraints, 
        # choose a valid action   
        if enemy and enemy in action_constraints:
            valid = action_constraints[enemy]
            return random.choice(valid)
    # For all other symbols, we can just choose randomly from the grammar
    rule = random.choice(grammar[symbol])
    return " ".join(generate(s, context) for s in rule)


print("Quest:", generate("S", {}))
"""






