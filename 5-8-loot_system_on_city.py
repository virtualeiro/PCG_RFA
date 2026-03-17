import pygame
import random

pygame.init()

WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shape Grammar City")

AVENUE_WIDTH = 16
STREET_WIDTH = 6
MIN_BLOCK = 140
MIN_PARCEL = 40

BG = (20,20,20)
BUILDING = (140,170,210)
AVENUE = (220,220,220)
STREET = (150,150,150)
PARK = (80,250,80)
COMMERCIAL = (250,250,80)


# -------------------------------
# RFA-Loot generation
# -------------------------------
LOOT_COLORS = {
    "Gold": (255,215,0),      # gold
    "Potion": (255,0,255),    # purple
    "Sword": (255,80,80)      # red
}

def generate_sword():
    damage = random.randint(15,25)
    sword = {
        "name":"Sword",
        "damage":damage,
        "crit": False,
        "fire": False
    }
    if random.random() < 0.4:
        sword["crit"] = True
    if random.random() < 0.3:
        sword["fire"] = True
    return sword


def generate_loot():
    r = random.random()
    if r < 0.4:
        return {"name":"Gold", "amount":random.randint(10,100)}
    elif r < 0.7:
        return {"name":"Potion"}
    else:
        return generate_sword()

class Node:

    def __init__(self, rect, level):
        self.rect = rect
        self.level = level
        self.children = []
        self.type = None
        self.loot = None #RFA Loot
    #City → Block
    #Block → Block Block
    #Block → StreetBlock
    #StreetBlock → Parcel
    #Parcel → Building
    #Building → res | com | park

    # Applies the appropriate rule to split the current node into child nodes,
    #  which represent smaller parts of the city 
    # (e.g., blocks, street blocks, parcels, buildings).
    def apply_rule(self):
        print(self.level)
        if self.level == "city":
            self.split("avenue")

        elif self.level == "block":
        #Block(size > threshold) → Block Block
        #Block(size ≤ threshold) → StreetBlock
            #if min(self.rect.w, self.rect.h) < MIN_BLOCK:
            #    self.level = "streetblock"
            #    return

            if random.random() < 0.9:
                self.split("street")
            else:
                self.level = "streetblock"

        elif self.level == "streetblock":
            if min(self.rect.w, self.rect.h) > MIN_PARCEL*2:
                self.split("parcel")
            else:
                self.level = "building"

        elif self.level == "building":
            self.type = random.choice(["res","com","park"]) #REsidential or park  
        #RFA Loot generation
        if self.type != "park" and random.random() < 0.3:
                self.loot = generate_loot()
    # Determines how to split the current node 
    # based on its level in the grammar.
    def split(self, road_type):

        horizontal = random.random() < 0.5

        min_size = 80

        if horizontal:

            if self.rect.h < min_size:
                return

            split = random.randint(40, self.rect.h - 40)

            r1 = pygame.Rect(self.rect.x, self.rect.y,
                            self.rect.w, split)

            r2 = pygame.Rect(self.rect.x,
                            self.rect.y + split,
                            self.rect.w,
                            self.rect.h - split)

        else:

            if self.rect.w < min_size:
                return

            split = random.randint(40, self.rect.w - 40)

            r1 = pygame.Rect(self.rect.x, self.rect.y,
                            split, self.rect.h)

            r2 = pygame.Rect(self.rect.x + split,
                            self.rect.y,
                            self.rect.w - split,
                            self.rect.h)

        self.children = [
            Node(r1, "block"),
            Node(r2, "block")
        ]

    #Generates the geometry of the city by applying the shape grammar rules recursively until a certain depth is reached.
    #At each level of the grammar, it applies the appropriate rule 
    # to split the current node into child nodes, 
    # which represent smaller parts of the city 
    # (e.g., blocks, street blocks, parcels, buildings).
    def generate(self, depth):

        if depth <= 0:
            self.level = "building"
            self.apply_rule()    
            #RFA - print loot info
            if self.level == "building" and self.loot:
                print("Loot in building:", self.loot) 
            return
        #determines how to split the current node 
        # based on its level in the grammar.
        self.apply_rule()
        #If the node has children (i.e., it was split), 
        # it recursively calls generate on each child node,
        for c in self.children:
            c.generate(depth-1)


    def draw(self, surf):

        if not self.children:
            width = AVENUE_WIDTH if self.level == "city" else STREET_WIDTH
            pygame.draw.rect(surf, STREET, self.rect, width)
            if self.level == "building":

                r = self.rect.inflate(-18,-18)

                if self.type == "park":
                    color = PARK
                elif self.type == "com":
                    color = COMMERCIAL
                else:
                    color = BUILDING

                pygame.draw.rect(surf, color, r)
                #RFA - draw loot marker
                if self.loot:
                    cx = r.centerx
                    cy = r.centery

                    color = LOOT_COLORS.get(self.loot["name"], (255,255,255))

                    pygame.draw.circle(surf, color, (cx,cy), 10)

        else:

            for c in self.children:
                c.draw(surf)

            pygame.draw.rect(surf, STREET, self.rect, 2)

# -------------------------------------------------
# Shape grammar for building geometry
# -------------------------------------------------
root = Node(pygame.Rect(0,0,WIDTH,HEIGHT),"city")
root.generate(5)

clock = pygame.time.Clock()

running = True
while running:

    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running=False

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                root = Node(pygame.Rect(0,0,WIDTH,HEIGHT),"city")
                root.generate(5)

    screen.fill(BG)
    root.draw(screen)

    pygame.display.flip()

pygame.quit()
