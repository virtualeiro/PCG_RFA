import pygame
import random
import math

# ------------------ CONFIG ------------------
WIDTH, HEIGHT = 800, 600
FLOWER_COUNT = 10
FLOWER_RADIUS = 60
MUTATION_RATE = 0.9

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Virtual Gardener (Genetic Flowers)")
font = pygame.font.SysFont(None, 24)

# ------------------ FLOWER CLASS ------------------
class Flower:
    def __init__(self, genome=None):
        if genome:
            self.genome = genome
        else:
            self.genome = {
                "petals": random.randint(3, 12),
                "radius": random.randint(20, 50),             
                "color" : [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)],
                "petal_length": random.uniform(0.5, 1.5),
                "rotation": random.uniform(0, math.pi)
            }

    def draw(self, surface, x, y, selected=False):
        g = self.genome

        # Draw petals
        for i in range(g["petals"]):
            angle = (2 * math.pi / g["petals"]) * i + g["rotation"] #+ rotation for variation
            px = x + math.cos(angle) * g["radius"]
            py = y + math.sin(angle) * g["radius"]

            petal_len = g["radius"] * g["petal_length"]
            tip_x = x + math.cos(angle) * petal_len
            tip_y = y + math.sin(angle) * petal_len

            pygame.draw.line(surface, g["color"], (px, py), (tip_x, tip_y), 3)

        # Center
        pygame.draw.circle(surface, (255,255,255), (x,y), 5)

        # Selection highlight
        if selected:
            pygame.draw.circle(surface, (255,255,0), (x,y), g["radius"]+10, 2)

# ------------------ GENETIC OPERATORS ------------------
def crossover(g1, g2):
    new_genome = {}
    for key in g1:
        new_genome[key] = random.choice([g1[key], g2[key]])
    return new_genome

def mutate(genome):
    for key in genome:
        if random.random() < MUTATION_RATE:
            if key == "petals":
                genome[key] = max(3, min(12, genome[key] + random.choice([-1,1]))) # Ensure petals stay between 3 and 12
            elif key == "radius":
                genome[key] = max(10, min(60, genome[key] + random.randint(-5,5))) # Ensure radius stays between 10 and 60
            elif key == "color":
                genome[key] = [max(0,min(255,c+random.randint(-40,40))) for c in genome[key]] # Ensure color stays between 0 and 255
            elif key == "petal_length":
                genome[key] += random.uniform(-0.2, 0.2) # Petal length can vary more freely
            elif key == "rotation":
                genome[key] += random.uniform(-0.3, 0.3) # Rotation can vary more freely
    return genome

# ------------------ INITIAL POPULATION ------------------
population = []
for _ in range(FLOWER_COUNT):
    population.append(Flower())
selected = []

# Layout positions
positions = []
cols = 5
for i in range(FLOWER_COUNT):
    # Calculate grid position, with some spacing, and a bit of margin from the edges
    #by using the index and the number of columns, we can determine the row and column for each flower. 
    # The x and y coordinates are then calculated based on these row and column values, 
    # with added spacing and margins to ensure the flowers are displayed neatly on the screen.
    row = i // cols
    col = i % cols
    x = 100 + col * 140
    y = 150 + row * 200
    positions.append((x, y))

# ------------------ MAIN LOOP ------------------
running = True
while running:
    screen.fill((30,30,30))

    # Draw flowers
    for i, flower in enumerate(population):
        flower.draw(screen, *positions[i], selected=(i in selected))

    # Instructions
    text = font.render("Click 2 flowers to breed next generation", True, (255,255,255))
    screen.blit(text, (20, 20))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            for i, (x,y) in enumerate(positions):
                dist = math.hypot(mx-x, my-y) # Calculate distance from click to flower center 
                if dist < FLOWER_RADIUS: 
                    if i not in selected:
                        selected.append(i)

            # When 2 selected it then breeds the next generation by performing crossover and mutation on the selected flowers' genomes.
            if len(selected) == 2:
                p1 = population[selected[0]]
                p2 = population[selected[1]]

                new_population = []
                for _ in range(FLOWER_COUNT):
                    child_genome = crossover(p1.genome, p2.genome)
                    child_genome = mutate(child_genome)
                    new_population.append(Flower(child_genome))

                population = new_population
                selected = []

pygame.quit()