import pygame
import random

# =========================
# CONFIG
# =========================
WIDTH, HEIGHT = 800, 600
GENOME_LENGTH = 200
STEP_SIZE = 1
MAX_SPEED = 2

TARGET = pygame.Vector2(WIDTH // 2, 100)
START = pygame.Vector2(WIDTH // 2, HEIGHT - 50)

FPS = 60

# =========================
# AGENT
# =========================
class Agent:
    def __init__(self, genome):
        self.genome = genome
        self.reset()
    #   Generates a random genome of the specified length
    #   Each gene is a 2D vector with random values between -1 and 1, 
    # representing the movement direction and magnitude for that step.
  
    def random_genome(length):
        result = []
        for _ in range(length):
            gene = pygame.Vector2(
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            )
            result.append(gene)
        return result
    
    def reset(self):
        self.pos = START.copy()
        self.vel = pygame.Vector2(0, 0)
        self.step = 0
        self.finished = False
        self.path = []

    #   Updates the agent's position based on its genome and velocity.
    #   It applies the current gene to the velocity, limits the speed, and updates the position.
    #   If the agent reaches the target, it marks itself as finished.
    def update(self):
        if self.step >= len(self.genome):
            return
        move = self.genome[self.step]
        self.vel += move

        if self.vel.length() > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)
        self.pos += self.vel
        self.path.append(self.pos.copy())
        self.step += 1

        if self.pos.distance_to(TARGET) < 10:
            self.finished = True

    def fitness(self):
        dist = self.pos.distance_to(TARGET)
        score = 1 / (dist + 1)
        if self.finished:
            score *= 2
        return score


# =========================
# EVOLUTION STRATEGY
# =========================
class EvolutionStrategy:
    def __init__(self):
        self.generation = 1

        self.parent = Agent(Agent.random_genome(GENOME_LENGTH))
        self.child = Agent(self.mutate(self.parent.genome)) #versão do parent mutada

        self.mode = "parent"

    #   Mutates the given genome by adding a small random vector to each gene.
    #   The mutation is controlled by the STEP_SIZE constant, 
    #   which determines how much each gene can change.
    def mutate(self, genome):
        new_genome = []

        for gene in genome:
            dx = random.uniform(-STEP_SIZE, STEP_SIZE)
            dy = random.uniform(-STEP_SIZE, STEP_SIZE)
            new_genome.append(gene + pygame.Vector2(dx, dy))

        return new_genome
    
    #   The step function manages the different phases of the evolution process:3
    #   - In "parent" mode, it updates the parent agent until it has completed its genome.
    #   - In "child" mode, it updates the child agent until it has completed its genome.
    def step(self):
        if self.mode == "parent":
            self.parent.update()
            if self.parent.step >= GENOME_LENGTH:
                self.mode = "child"

        elif self.mode == "child":
            self.child.update()
            if self.child.step >= GENOME_LENGTH:
                self.mode = "selection"

        elif self.mode == "selection":
            self.select()
            self.mode = "parent"
    #  In "selection" mode, it compares the fitness of the parent and child agents, 
    # selects the better one as the new parent, and creates a new child by mutating the parent's genome.
    #  After selection, it resets both agents and increments the generation count.
    def select(self):
        #If parent is better, keep it. 
        # Otherwise, replace it with the child.
        if self.child.fitness() > self.parent.fitness():
            self.parent = self.child
        print(self.parent.genome)
        # Create a new child by mutating the parent's genome
        self.child = Agent(self.mutate(self.parent.genome))

        self.parent.reset()
        self.child.reset()

        self.generation += 1

        print(f"Gen {self.generation} | Fitness: {self.parent.fitness():.4f}")


# =========================
# DRAWING
# =========================
def draw(screen, es):
    screen.fill((30, 30, 30))

    # target
    pygame.draw.circle(screen, (0, 255, 0), TARGET, 10)

    # parent path
    for p in es.parent.path:
        pygame.draw.circle(screen, (100, 100, 255), p, 2)

    # child path
    for p in es.child.path:
        pygame.draw.circle(screen, (255, 100, 100), p, 2)

    # agents
    pygame.draw.circle(screen, (0, 0, 255), es.parent.pos, 5)
    pygame.draw.circle(screen, (255, 0, 0), es.child.pos, 5)

    # UI
    font = pygame.font.SysFont(None, 24)
    text = font.render(
        f"Gen: {es.generation} | Mode: {es.mode}",
        True,
        (255, 255, 255)
    )
    screen.blit(text, (10, 10))


# =========================
# MAIN
# =========================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    es = EvolutionStrategy()

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        es.step()
        draw(screen, es)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()