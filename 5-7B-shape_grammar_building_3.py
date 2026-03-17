import pygame
import random

pygame.init()

WIDTH = 900
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shape Grammar Interpreter")

clock = pygame.time.Clock()

# -------------------------------------------------
# Grammar definition (THIS is the editable grammar)
# -------------------------------------------------

GRAMMAR = [
    "B -> B + Floor",
    "Floor -> Floor + Windows",
    "B -> B + Roof"
]
"""
B	Building
Floor	A floor rectangle
Windows	Window grid
Roof	Roof
"""


"""
[B]
one building
B → B + Floor

[B, Floor]
Building
 └ one floor added

B → B + Floor
Floor → Floor + Windows
[B, Floor, Floor, Windows]
Building
 ├ Floor
 │   └ Windows
 └ Floor

B → B + Floor
Floor → Floor + Windows
[B, Floor, Floor, Windows, Floor, Windows, Windows]
Building
 ├ Floor
 │   └ Windows Windows
 ├ Floor
 │   └ Windows
 └ Floor

 B → B + Roof
 [B, Floor, Floor, Windows, Floor, Windows, Windows]
[B, Roof]
 Building
 ├ Floor
 │   └ Windows
 ├ Floor
 │   └ Windows
 ├ Floor
 └ Roof
----
Core:
sequence = ["B"]

repeat N times:
    new_sequence = []

    for symbol in sequence:
        if rule exists:
            replace symbol with rule result
        else:
            keep symbol

    sequence = new_sequence
---
Floor 1 → rectangle
Floor 2 → rectangle
Floor 3 → rectangle 

B
│
├── Floor
│   └── Windows
│
├── Floor
│   └── Windows
│
├── Floor
│
└── Roof
"""
# -------------------------------------------------
# Parse grammar rules
# -------------------------------------------------
##1-
#Reads the text rules like "B -> B + Floor".
#It converts them into a dictionary:
#RULES = {
#    "B": [["B", "Floor"], ["B", "Roof"]],
#    "Floor": [["Floor", "Windows"]]
#}
def parse_rules(grammar):

    rules = {}

    for rule in grammar:

        left, right = rule.split("->")

        left = left.strip()
        right = [x.strip() for x in right.split("+")]

        rules.setdefault(left, []).append(right)

    return rules


RULES = parse_rules(GRAMMAR)


# -------------------------------------------------
# Grammar expansion
# -------------------------------------------------
#The program looks at each symbol in the sequence.
#If there’s a rule for it, it randomly picks one of the possible rules.
#Then it replaces the symbol with the things on the right side.
#If there’s no rule, it just keeps the symbol.
#Example
#sequence = ["B"]
#expand(sequence) -> maybe ["B", "Floor"]
def expand(symbols):

    new_symbols = []

    for s in symbols:

        if s in RULES:

            rule = random.choice(RULES[s])
            new_symbols.extend(rule)

        else:
            new_symbols.append(s)

    return new_symbols


# -------------------------------------------------
# Generate building sequence
# -------------------------------------------------
#3-
# Starts with one building.
#Randomly chooses 3 to 6 times to add floors (this is why buildings have different heights each time).
#Expands the sequence that many times.
#At the end, it always adds a roof.
#Example result:
#["B", "Floor", "Floor", "Windows2", "Floor", "Windows4", "Roof"]
def generate_sequence():

    seq = ["B"]

    # grow floors
    num_floors = random.randint(3, 6)
    for i in range(num_floors):
        seq = expand(seq)

    # force roof rule at end
    seq.append("Roof")

    return seq


# -------------------------------------------------
# Geometry generation
# -------------------------------------------------
#base_y is the bottom of the building.
#Each floor is 50 pixels tall, and the building is centered on the screen.
#
#Each "Floor" in the sequence becomes a rectangle drawn on the screen.
#Floors are stacked from bottom to top.
#
# Each floor gets some windows.
#Columns are random, so each floor looks a bit different.
#Windows are rectangles inside the floor rectangle.  
# 
# The roof is a triangle above the top floor.
#top - 40 makes the triangle point upwards.  
def build_geometry(sequence):

    floors = []
    windows = []

    base_y = HEIGHT - 80
    floor_h = 50
    width = 160
    x = WIDTH // 2 - width // 2
    
    floor_count = sequence.count("Floor")

    for i in range(floor_count):

        y = base_y - (i + 1) * floor_h

        rect = pygame.Rect(x, y, width, floor_h)
        floors.append(rect)

        # windows
        cols = random.randint(3, 5)
        margin = 10

        w = (width - margin * (cols + 1)) / cols
        h = floor_h / 2

        for c in range(cols):

            wx = x + margin + c * (w + margin)
            wy = y + floor_h / 4

            windows.append(pygame.Rect(wx, wy, w, h))

    roof = None

    if "Roof" in sequence and floors:

        top = floors[-1].top

        roof = [
            (x, top),
            (x + width/2, top - 40),
            (x + width, top)
        ]

    return floors, windows, roof


# -------------------------------------------------
# Generate first building
# -------------------------------------------------

sequence = generate_sequence()
floors, windows, roof = build_geometry(sequence)


# -------------------------------------------------
# Drawing
# -------------------------------------------------
#Clears the screen.
#Draws floors first.
#Draws windows on top.
#Draws the roof last so it appears on top.
def draw():

    screen.fill((30,30,40))

    for f in floors:
        pygame.draw.rect(screen, (180,180,200), f)

    for w in windows:
        pygame.draw.rect(screen, (255,220,120), w)

    if roof:
        pygame.draw.polygon(screen, (160,80,80), roof)

    pygame.display.flip()


# -------------------------------------------------
# Main loop
# -------------------------------------------------

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:

                sequence = generate_sequence()
                floors, windows, roof = build_geometry(sequence)

    draw()
    clock.tick(60)

pygame.quit()