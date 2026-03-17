import pygame
import random

# ----------------------------
# CONFIGURATION
# ----------------------------
WIDTH, HEIGHT = 1000, 800
CELL_SIZE = 18 #8

COLS = WIDTH // CELL_SIZE
ROWS = HEIGHT // CELL_SIZE

WALL_PROBABILITY = 0.60 #0.45
ITERATIONS = 5

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cellular Automata Cave Generator")
clock = pygame.time.Clock()

# ----------------------------
# GRID INITIALIZATION
# ----------------------------
def initialize_grid():
    grid = []
    for x in range(COLS):
        column = []
        for y in range(ROWS):
            if random.random() < WALL_PROBABILITY:
                column.append(1)  # Wall
            else:
                column.append(0)  # Empty
        grid.append(column)
    return grid

# ----------------------------
# COUNT WALL NEIGHBORS
# ----------------------------
def count_wall_neighbors(grid, x, y):
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            nx = x + dx
            ny = y + dy

            if dx == 0 and dy == 0:
                continue

            if nx < 0 or ny < 0 or nx >= COLS or ny >= ROWS:
                count += 1  # Treat out-of-bounds as walls
            elif grid[nx][ny] == 1:
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
            neighbors = count_wall_neighbors(grid, x, y)

            if neighbors > 4:
                column.append(1)  # Become wall
            else:
                column.append(0)  # Become empty
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
            if grid[x][y] == 1:
                pygame.draw.rect(screen, (40, 40, 40), rect)
            else:
                pygame.draw.rect(screen, (200, 200, 200), rect)

# ----------------------------
# MAIN
# ----------------------------
grid = initialize_grid()

for _ in range(ITERATIONS):
    grid = simulation_step(grid)

running = True
while running:
    clock.tick(60)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Regenerate new cave
                grid = initialize_grid()
                for _ in range(ITERATIONS):
                    grid = simulation_step(grid)

    draw_grid(grid)
    pygame.display.flip()

pygame.quit()