import pygame
import random

# ----------------------------
# CONFIGURATION
# ----------------------------
WIDTH, HEIGHT = 1000, 800
CELL_SIZE = 6

COLS = WIDTH // CELL_SIZE
ROWS = HEIGHT // CELL_SIZE

INITIAL_TREE_DENSITY = 0.55
GROW_PROBABILITY = 0.02
REGROW_PROBABILITY = 0.01

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cellular Automata - Forest Fire Simulation")
clock = pygame.time.Clock()

# ----------------------------
# STATES
# ----------------------------
EMPTY = 0
TREE = 1
FIRE = 2
BURNED = 3

# ----------------------------
# INITIALIZE GRID
# ----------------------------
def initialize_grid():
    grid = []
    for x in range(COLS):
        column = []
        for y in range(ROWS):
            if random.random() < INITIAL_TREE_DENSITY:
                column.append(TREE)
            else:
                column.append(EMPTY)
        grid.append(column)
    return grid

# ----------------------------
# COUNT NEIGHBORS
# ----------------------------
def count_neighbors(grid, x, y, state):
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue

            nx = x + dx
            ny = y + dy

            if 0 <= nx < COLS and 0 <= ny < ROWS:
                if grid[nx][ny] == state:
                    count += 1
    return count

# ----------------------------
# SIMULATION STEP
# ----------------------------
def simulation_step(grid):
    new_grid = []
    for x in range(COLS):
        column = []
        for y in range(ROWS):
            current = grid[x][y]

            # EMPTY → TREE (growth near trees)
            if current == EMPTY:
                tree_neighbors = count_neighbors(grid, x, y, TREE)
                if tree_neighbors >= 3:
                    column.append(TREE)
                else:
                    column.append(EMPTY)

            # TREE → FIRE (if adjacent to fire)
            elif current == TREE:
                fire_neighbors = count_neighbors(grid, x, y, FIRE)
                if fire_neighbors > 0:
                    column.append(FIRE)
                else:
                    column.append(TREE)

            # FIRE → BURNED
            elif current == FIRE:
                column.append(BURNED)

            # BURNED → TREE probabilistically
            elif current == BURNED:
                if random.random() < REGROW_PROBABILITY:
                    column.append(TREE)
                else:
                    column.append(BURNED)

        new_grid.append(column)

    return new_grid

# ----------------------------
# DRAW FUNCTION
# ----------------------------
def draw_grid(grid):
    for x in range(COLS):
        for y in range(ROWS):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE,
                               CELL_SIZE, CELL_SIZE)

            state = grid[x][y]

            if state == EMPTY:
                pygame.draw.rect(screen, (30, 30, 30), rect)
            elif state == TREE:
                pygame.draw.rect(screen, (0, 150, 0), rect)
            elif state == FIRE:
                pygame.draw.rect(screen, (255, 0, 0), rect)
            elif state == BURNED:
                pygame.draw.rect(screen, (60, 60, 60), rect)

# ----------------------------
# MAIN
# ----------------------------
grid = initialize_grid()

running = True
while running:
    clock.tick(20)  # slower for visibility

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Press SPACE to ignite random fire
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                x = random.randint(0, COLS - 1)
                y = random.randint(0, ROWS - 1)
                grid[x][y] = FIRE

            if event.key == pygame.K_r:
                grid = initialize_grid()

    grid = simulation_step(grid)

    screen.fill((0, 0, 0))
    draw_grid(grid)
    pygame.display.flip()

pygame.quit()