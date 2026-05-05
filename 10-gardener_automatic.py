import pygame
import random
import math

# ------------------ CONFIG ------------------
WIDTH, HEIGHT = 800, 600
FLOWER_COUNT = 10
FLOWER_RADIUS = 60
MUTATION_RATE = 0.2

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Genetic Flowers (Auto Fitness)")
font = pygame.font.SysFont(None, 24)

# ------------------ FITNESS WEIGHTS ------------------
W_SYMMETRY = 0.5
W_COLOR = 1.0
W_BALANCE = 0.5
W_NOVELTY = 10.5
W_TARGET = 0.5

# Optional target (can tweak or disable)
TARGET = {
    "petals": 8,
    "radius": 40,
    "petal_length": 1.0
}

# ------------------ FLOWER CLASS ------------------
class Flower:
    def __init__(self, genome=None):
        if genome:
            self.genome = genome
        else:
            self.genome = {
                "petals": random.randint(3, 20),
                "radius": random.randint(20, 50),
                "color": [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)],
                "petal_length": random.uniform(0.5, 1.5),
                "rotation": random.uniform(0, math.pi)
            }

    def draw(self, surface, x, y):
        g = self.genome

        for i in range(g["petals"]):
            angle = (2 * math.pi / g["petals"]) * i + g["rotation"]

            px = x + math.cos(angle) * g["radius"]
            py = y + math.sin(angle) * g["radius"]

            petal_len = g["radius"] * g["petal_length"]
            tip_x = x + math.cos(angle) * petal_len
            tip_y = y + math.sin(angle) * petal_len

            pygame.draw.line(surface, g["color"], (px, py), (tip_x, tip_y), 3)

        pygame.draw.circle(surface, (255, 255, 255), (x, y), 5)

# ------------------ GENETIC OPERATORS ------------------
def crossover(g1, g2):
    return {k: random.choice([g1[k], g2[k]]) for k in g1}

def mutate(genome):
    for key in genome:
        if random.random() < MUTATION_RATE:
            if key == "petals":
                genome[key] = max(3, min(12, genome[key] + random.choice([-1, 1])))
            elif key == "radius":
                genome[key] = max(10, min(60, genome[key] + random.randint(-5, 5)))
            elif key == "color":
                genome[key] = [max(0, min(255, c + random.randint(-40, 40))) for c in genome[key]]
            elif key == "petal_length":
                genome[key] += random.uniform(-0.2, 0.2)
            elif key == "rotation":
                genome[key] += random.uniform(-0.3, 0.3)
    return genome

# ------------------ FITNESS FUNCTION ------------------
def fitness(flower, population):
    gen = flower.genome

    # --- 1. Symmetry / structure ---
    symmetry = 1 - abs(gen["petals"] - 10) / 10  # Rewards 10 petals, penalizes too few or too many
    symmetry += 1 - abs(gen["petal_length"] - 1.0)

    # --- 2. Color harmony ---
    r, g, b = gen["color"]
    contrast = abs(r - g) + abs(g - b) + abs(b - r)
    brightness = (r + g + b) / 3
    color_score = (contrast / 765) * 0.7 + (brightness / 255) * 0.3

    # --- 3. Balance (avoid extremes) ---
    balance = 1 - abs(gen["radius"] - 35) / 35
    balance += 1 - abs(gen["petals"] - 20) / 20 # Rewards more petals up to 20, penalizes too few or too many

    # --- 4. Novelty (difference from others) ---
    def dist(g1, g2):
        return (
            abs(g1["petals"] - g2["petals"]) +
            abs(g1["radius"] - g2["radius"]) +
            sum(abs(a - b) for a, b in zip(g1["color"], g2["color"]))
        )

    novelty = 0

    for other in population:
        if other != flower:
            d = dist(gen, other.genome)
            novelty += d
        novelty /= (len(population) * 500)  # normalize

    # --- 5. Target style ---
    target_score = (
        #“closeness score”—it turns how far you are from the target into a number where 1 = perfect match and smaller values mean worse matches.
        #score = 1 - (distance / max_possible_distance)
        1 - abs(gen["petals"] - TARGET["petals"]) / 12 + # Rewards flowers close to 8 petals / Penalizes too many or too few
        1 - abs(gen["radius"] - TARGET["radius"]) / 60 + # Prefers medium-sized flowers / Avoids tiny or oversized ones
        1 - abs(gen ["petal_length"] - TARGET["petal_length"]) #Prefers proportional petals / Not too short (stubby) /Not too long (spiky/explosive)
    )

    # --- FINAL WEIGHTED SUM ---
    return (
        W_SYMMETRY * symmetry +
        W_COLOR * color_score +
        W_BALANCE * balance +
        W_NOVELTY * novelty +
        W_TARGET * target_score
    )

# ------------------ INITIAL POPULATION ------------------
population = [Flower() for _ in range(FLOWER_COUNT)]

positions = []
cols = 5
for i in range(FLOWER_COUNT):
    row = i // cols
    col = i % cols
    x = 100 + col * 140
    y = 150 + row * 200
    positions.append((x, y))

# ------------------ MAIN LOOP ------------------
running = True
clock = pygame.time.Clock()

while running:
    screen.fill((30, 30, 30))

    # Evaluate fitness
    scored = [(flower, fitness(flower, population)) for flower in population]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Draw flowers
    for i, (flower, score) in enumerate(scored):
        flower.draw(screen, *positions[i])

        label = font.render(f"{score:.2f}", True, (255, 255, 255))
        screen.blit(label, (positions[i][0] - 20, positions[i][1] + 70))

    pygame.display.flip()

    # Create next generation every frame (or slow it down if needed)
    parents = [scored[0][0], scored[1][0]]

    new_population = []
    for _ in range(FLOWER_COUNT):
        child = crossover(parents[0].genome, parents[1].genome)
        child = mutate(child)
        new_population.append(Flower(child))

    population = new_population

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    clock.tick(2)  # slow evolution so you can see it

pygame.quit()