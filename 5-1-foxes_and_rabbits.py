import pygame
import random
import math
import sys

pygame.init()

WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ecosystem Simulation")

clock = pygame.time.Clock()

# ==============================
# CONFIGURATION
# ==============================

GRASS_GROW_RATE = 0.002
GRASS_MAX = 1200

RABBIT_START = 25
RABBIT_LIFESPAN = 500
RABBIT_SPEED = 3.2
RABBIT_REPRODUCE_CHANCE = 0.009
RABBIT_EAT_COOLDOWN = 40  # frames

FOX_START = 6
FOX_LIFESPAN = 900
FOX_SPEED = 2.4
FOX_REPRODUCE_CHANCE = 0.002
FOX_EAT_COOLDOWN = 400    # frames

GRASS_SIZE = 3


# ==============================
# ENTITIES
# ==============================

class Grass:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)

    def draw(self):
        pygame.draw.circle(screen, (0,180,0), (int(self.x), int(self.y)), GRASS_SIZE)


class Rabbit:
    def __init__(self,x=None,y=None):
        self.x = x if x else random.randint(0,WIDTH)
        self.y = y if y else random.randint(0,HEIGHT)
        self.energy = 50
        self.age = 0
        self.eat_cooldown = 0  # frames until can eat again

    def move(self):
        angle = random.random()*math.tau
        self.x += math.cos(angle)*RABBIT_SPEED
        self.y += math.sin(angle)*RABBIT_SPEED
        self.x = max(0,min(WIDTH,self.x))
        self.y = max(0,min(HEIGHT,self.y))

    def update(self,grass_list):

        self.move()

        if self.eat_cooldown <= 0:
            for g in grass_list[:]:
                if math.hypot(self.x-g.x,self.y-g.y) < 6:
                    grass_list.remove(g)
                    self.energy += 20
                    self.eat_cooldown = RABBIT_EAT_COOLDOWN
                    break
        else:
            self.eat_cooldown -= 1

        self.energy -= 0.1
        self.age += 1

    def draw(self):
        pygame.draw.circle(screen,(220,220,220),(int(self.x),int(self.y)),5)


class Fox:
    def __init__(self,x=None,y=None):
        self.x = x if x else random.randint(0,WIDTH)
        self.y = y if y else random.randint(0,HEIGHT)
        self.energy = 80
        self.age = 0
        self.eat_cooldown = 0  # frames until can eat again

    def move(self,rabbits):
        if self.eat_cooldown <= 0 and rabbits:
            target = min(rabbits, key=lambda r: math.hypot(self.x-r.x,self.y-r.y))
            dx = target.x-self.x
            dy = target.y-self.y
            dist = math.hypot(dx,dy)
            if dist > 0:
                self.x += (dx/dist)*FOX_SPEED
                self.y += (dy/dist)*FOX_SPEED
        else:
            angle=random.random()*math.tau
            self.x += math.cos(angle)*FOX_SPEED
            self.y += math.sin(angle)*FOX_SPEED

        self.x = max(0,min(WIDTH,self.x))
        self.y = max(0,min(HEIGHT,self.y))

    def update(self,rabbits):
        self.move(rabbits)

        if self.eat_cooldown <= 0:
            for r in rabbits[:]:
                if math.hypot(self.x-r.x,self.y-r.y) < 8:
                    rabbits.remove(r)
                    self.energy += 40
                    self.eat_cooldown = FOX_EAT_COOLDOWN
                    break
        else:
            self.eat_cooldown -= 1

        self.energy -= 0.15
        self.age += 1

    def draw(self):
        pygame.draw.circle(screen,(255,120,50),(int(self.x),int(self.y)),7)


# ==============================
# RESET FUNCTION
# ==============================

def reset_simulation():
    grass = [Grass() for _ in range(400)]
    rabbits = [Rabbit() for _ in range(RABBIT_START)]
    foxes = [Fox() for _ in range(FOX_START)]
    return grass, rabbits, foxes


grass, rabbits, foxes = reset_simulation()

font = pygame.font.SysFont(None,24)

# ==============================
# MAIN LOOP
# ==============================

running=True

while running:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type==pygame.QUIT:
            running=False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.key == pygame.K_SPACE:
                grass, rabbits, foxes = reset_simulation()


    # ==============================
    # GRASS GROWTH
    # ==============================

    if len(grass) < GRASS_MAX and random.random() < GRASS_GROW_RATE*WIDTH*HEIGHT:
        grass.append(Grass())

    # ==============================
    # RABBITS
    # ==============================

    for r in rabbits[:]:
        r.update(grass)

        if random.random() < RABBIT_REPRODUCE_CHANCE and r.energy > 40:
            rabbits.append(Rabbit(r.x,r.y))
            r.energy -= 20

        if r.energy <= 0 or r.age > RABBIT_LIFESPAN:
            rabbits.remove(r)

    # ==============================
    # FOXES
    # ==============================

    for f in foxes[:]:
        f.update(rabbits)

        if random.random() < FOX_REPRODUCE_CHANCE and f.energy > 60:
            foxes.append(Fox(f.x,f.y))
            f.energy -= 30

        if f.energy <= 0 or f.age > FOX_LIFESPAN:
            foxes.remove(f)

    # ==============================
    # DRAW
    # ==============================

    screen.fill((30,30,30))

    for g in grass:
        g.draw()

    for r in rabbits:
        r.draw()

    for f in foxes:
        f.draw()

    text = font.render(
        f"Grass:{len(grass)} Rabbits:{len(rabbits)} Foxes:{len(foxes)}   SPACE=Restart  ESC=Quit",
        True,(255,255,255)
    )
    screen.blit(text,(10,10))

    pygame.display.flip()

pygame.quit()