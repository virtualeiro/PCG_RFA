import pygame
import random

pygame.init()

WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Explicit Grammar City")

AVENUE_WIDTH = 36
STREET_WIDTH = 16
MIN_BLOCK = 40
MIN_PARCEL = 40

BG = (20,20,20)
BUILDING = (140,170,210)
PARK = (80,250,80)
STREET = (150,150,150)
COMMERCIAL = (250,250,80)

# --------------------------------
# Explicit Grammar
# --------------------------------

GRAMMAR = {
    "city": [("split", "block", "block")],
    "block": [ ("become", "streetblock"), ("split", "block", "block")],
    "streetblock": [("split", "parcel", "parcel"), ("become", "building")],
    "parcel": [("become", "building")],
    "building": [("type", ["res","com","park"])]
}

class Node:
    def __init__(self, rect, symbol):
        self.rect = rect
        self.symbol = symbol
        self.children = []
        self.type = None

    # -------------------------
    # Apply grammar rule
    # -------------------------
    def apply_rule(self):
        # Get all rules for the current symbol
        rules = GRAMMAR.get(self.symbol, [])
        print(f"Applying rule for symbol: {self.symbol}, available rules: {rules}")
        if not rules:
            return  # terminal with no rules

        # Pick one rule **explicitly**
        rule = random.choice(rules)
        print("Rule0:" + rule[0])
        if rule[0] == "split":
            # Split into exactly the symbols in the rule
            self.split(rule[1], rule[2])
        elif rule[0] == "become":
            # Convert to the new symbol
            self.symbol = rule[1]
            print("Become:" + self.symbol + " " + str(len(self.children)))
            self.apply_rule()
        elif rule[0] == "type":
            # Assign type to the building
            self.type = random.choices(
                population=rule[1],
                weights=[0.5, 0.2, 0.3],  # e.g., res 40%, com 20%, park 40%
                k=1
            )[0]
           
    # -------------------------
    # Geometry split
    # -------------------------

    def split(self, left_symbol, right_symbol):
        print(f"Split: Splitting {self.symbol} into {left_symbol} and {right_symbol}")
        horizontal = random.random() < 0.5
        if horizontal:
            if self.rect.h < 80:
                return
            split = random.randint(40, self.rect.h - 40)
            r1 = pygame.Rect(self.rect.x, self.rect.y,
                             self.rect.w, split)
            r2 = pygame.Rect(self.rect.x,
                             self.rect.y + split,
                             self.rect.w,
                             self.rect.h - split)
        else:
            if self.rect.w < 80:
                return
            split = random.randint(40, self.rect.w - 40)
            r1 = pygame.Rect(self.rect.x, self.rect.y,
                             split, self.rect.h)

            r2 = pygame.Rect(self.rect.x + split,
                             self.rect.y,
                             self.rect.w - split,
                             self.rect.h)
        self.children = [
            Node(r1, left_symbol),
            Node(r2, right_symbol)
        ]

    # -------------------------
    # Grammar derivation
    # -------------------------
    def generate(self, depth):
        print(f"Generate: Generating node with symbol: {self.symbol} at depth {depth}")
        if depth <= 0:
            return
        #determines how to split the current node 
        # based on its level in the grammar.
        self.apply_rule()
        # recursively generate children
        # if there are no children, this is a terminal node and we stop
        for c in self.children:
            c.generate(depth-1)

    # -------------------------
    # Drawing
    # -------------------------

    def draw(self, surf):
        if not self.children:
            
            if self.symbol == "building":
                r = self.rect.inflate(-18,-18)
                if self.type == "park":
                    color = PARK
                elif self.type == "com":
                    color = COMMERCIAL
                else:
                    color = BUILDING
                pygame.draw.rect(surf, color, r)
        else:
            for c in self.children:
                c.draw(surf)
            pygame.draw.rect(surf, STREET, self.rect, 2)

root = Node(pygame.Rect(0,0,WIDTH,HEIGHT),"city")
print("Generating city..." )
root.generate(depth=1)
print("City generation complete.")
clock = pygame.time.Clock()
running = True
while running:

    clock.tick(60)

    for e in pygame.event.get():

        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                root = Node(pygame.Rect(0,0,WIDTH,HEIGHT),"city")
                root.generate(10)

    screen.fill(BG)

    root.draw(screen)

    pygame.display.flip()

pygame.quit()