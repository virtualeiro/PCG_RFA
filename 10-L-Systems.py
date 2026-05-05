import pygame
import random
import math
#This program implements a simple interactive L-System plant generator using Pygame.
# The user can click on two plants to select them, 
# and then a new generation of plants will be created by crossing over their genomes and applying random mutations. 
# Each plant's genome consists of an axiom, a set of production rules, an angle, a step size, a number of iterations, and a color. 
# E.g. the axiom is typically "F", and the rules define how "F" is replaced in each iteration to create a more complex string that represents the plant's structure.
# The angle determines how much the plant branches, the step size controls the length of each segment, and the iterations determine how many times the rules are applied to generate the final string.
# The color is randomly assigned to give each plant a unique appearance.

# The L-System string is generated based on the axiom and rules, and then drawn on the screen using turtle graphics principles. 
# The user can evolve the plants by selecting different pairs and observing the resulting variations in their structure and appearance.
#Example of a genome:
# {     "axiom": "F",
#       "rules": {"F": "F[+F]F[-F]F"},
#       "angle": 0.5,       
#       "step": 5,
#       "iterations": 4,
#       "color": (r,g,b)
# }
# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1000, 700
POP_SIZE = 10
MUTATION_RATE = 0.15

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Biomorphic L-System Gardener")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 22)

# ---------------- L-SYSTEM ----------------
def generate_string(axiom, rules, iterations):
    s = axiom
    for _ in range(iterations):
        new_s = ""
        for c in s:
            new_s += rules.get(c, c)
        s = new_s
    return s

def draw_lsystem(surface, string, x, y, angle, step, color):
    stack = []
    heading = -math.pi / 2
    pos = (x, y)

    for c in string:
        if c == "F":
            new_x = pos[0] + math.cos(heading) * step
            new_y = pos[1] + math.sin(heading) * step
            pygame.draw.line(surface, color, pos, (new_x, new_y), 1)
            pos = (new_x, new_y)

        elif c == "+":
            heading += angle
        elif c == "-":
            heading -= angle
        elif c == "[":
            stack.append((pos, heading))
        elif c == "]":
            pos, heading = stack.pop()

# ---------------- INDIVIDUAL ----------------
#genome will be a dict with:
# - axiom: "F"  
# - rules: {"F": "F[+F]F[-F]F"}
# - angle: 0.5
# - step: 5
# - iterations: 4
# - color: (r,g,b)
#   the draw function will generate the string and draw it on the surface 
class Plant:
    def __init__(self, genome=None):
        if genome:
            self.genome = genome
        else:
            self.genome = {
                "axiom": "F",
                "rules": {
                    "F": random.choice([
                        "F[+F]F[-F]F",
                        "FF",
                        "F[+F]F",
                        "F[-F]F",
                        "F[+F][-F]"
                    ])
                },
                "angle": random.uniform(0.2, 0.8),
                "step": random.randint(4, 8),
                "iterations": random.randint(3, 5),
                "color": (
                    random.randint(100,255),
                    random.randint(100,255),
                    random.randint(100,255)
                )
            }

    def draw(self, surface, x, y, selected=False):
        g = self.genome
        s = generate_string(g["axiom"], g["rules"], g["iterations"])
        draw_lsystem(surface, s, x, y, g["angle"], g["step"], g["color"])

        if selected:
            pygame.draw.circle(surface, (255,255,0), (x,y), 40, 2)

# ---------------- GENETICS ----------------
# Crossover will create a new genome by randomly picking parameters from two parents
def crossover(g1, g2):
    return {
        "axiom": "F",
        "rules": {
            "F": random.choice([g1["rules"]["F"], g2["rules"]["F"]])
        },
        "angle": random.choice([g1["angle"], g2["angle"]]),
        "step": random.choice([g1["step"], g2["step"]]),
        "iterations": random.choice([g1["iterations"], g2["iterations"]]),
        "color": tuple(
            random.choice([g1["color"][i], g2["color"][i]]) for i in range(3)
        )
    }
# Mutation will randomly change one of the parameters with a certain probability
def mutate(g):
    if random.random() < MUTATION_RATE:
        g["rules"]["F"] = random.choice([
            "F[+F]F[-F]F",
            "FF",
            "F[+F][-F]",
            "F[+F]F",
            "F[-F]F",
            "F[+F]F[-F]"
        ])

    if random.random() < MUTATION_RATE:
        g["angle"] += random.uniform(-0.2, 0.2)

    if random.random() < MUTATION_RATE:
        g["step"] = max(2, min(10, g["step"] + random.randint(-2,2)))

    if random.random() < MUTATION_RATE:
        g["iterations"] = max(2, min(6, g["iterations"] + random.choice([-1,1])))

    if random.random() < MUTATION_RATE:
        g["color"] = tuple(
            max(0,min(255,c+random.randint(-30,30))) for c in g["color"]
        )

    return g

# ---------------- SETUP ----------------
population = []
for _ in range(POP_SIZE):
    new_plant = Plant()
    population.append(new_plant)
selected = []

positions = []
cols = 5
for i in range(POP_SIZE):
    row = i // cols
    col = i % cols
    x = 100 + col * 180
    y = 250 + row * 250
    positions.append((x, y))

# ---------------- LOOP ----------------
running = True
while running:
    screen.fill((20, 20, 30))

    for i, plant in enumerate(population):
        plant.draw(screen, *positions[i], selected=(i in selected))

    txt = font.render("Click 2 plants to evolve", True, (255,255,255))
    screen.blit(txt, (20,20))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            for i, (x,y) in enumerate(positions):
                if math.hypot(mx-x, my-y) < 60:
                    if i not in selected:
                        selected.append(i)

            if len(selected) == 2:
                p1 = population[selected[0]]
                p2 = population[selected[1]]

                new_pop = []
                for _ in range(POP_SIZE):
                    child = crossover(p1.genome, p2.genome)
                    child = mutate(child)
                    new_pop.append(Plant(child))

                population = new_pop
                selected = []
                print("Genome of selected individuals:")
                print(p1.genome)
                print(p2.genome)    

    clock.tick(30)

pygame.quit()