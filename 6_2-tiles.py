import pygame
"""
Cave systems <- cellular automata
Converts them into a tile-based graph structure (for pathfinding or tile drawing).
Step-by-step process:
1. INITIALIZATION:
    - Creates a random grid of cells where each cell is either a wall (1) or floor (0)
    - Wall probability is set to 60% initially
2. CELLULAR AUTOMATA SIMULATION:
    - Iterates 5 times through the grid
    - Each iteration applies Conway's Game of Life-style rules:
      - Counts neighboring walls (8 neighbors, treating out-of-bounds as walls)
      - If more than 4 neighbors are walls, the cell becomes a wall
      - Otherwise, the cell becomes a floor
    - This smooths out the random pattern into cave-like structures
3. TILE GENERATION:
    - Groups cells into 2x2 tile blocks
    - Counts walls in each tile
    - If >90% of cells in a tile are walls, marks the tile as solid (1)
    - Otherwise marks it as walkable (0)
    - Reduces complexity from 800x800 cells to 200x200 tiles

5. VISUALIZATION & INTERACTION:
    - Renders the detailed cell grid in grayscale (gray=wall, white=floor)
    - Renders the tile grid as outlined squares (black=wall, green=walkable)
    - Press SPACE to generate a new island system
    - Runs at 60 FPS using Pygame
"""
import random

# ----------------------------
# CONFIGURATION
# ----------------------------
WIDTH, HEIGHT = 800, 800
CELL_SIZE = 16

COLS = WIDTH // CELL_SIZE
ROWS = HEIGHT // CELL_SIZE

WALL_PROBABILITY = 0.60
ITERATIONS = 5

# ----------------------------
# TILE CONFIG 
# ----------------------------
CELLS_PER_TILE_X = 2
CELLS_PER_TILE_Y = 2

TILE_COLS = COLS // CELLS_PER_TILE_X
TILE_ROWS = ROWS // CELLS_PER_TILE_Y

TILE_SIZE_X = CELLS_PER_TILE_X * CELL_SIZE
TILE_SIZE_Y = CELLS_PER_TILE_Y * CELL_SIZE

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# ----------------------------
# map_grid INITIALIZATION
# ----------------------------
def initialize_map_grid():
     grid = []
     for r in range(ROWS):
        row = []
        for c in range(COLS):
            if random.random() < WALL_PROBABILITY:
                row.append(1)
            else:
                row.append(0)
        grid.append(row)
     return grid

# ----------------------------
# COUNT NEIGHBORS
# ----------------------------
def count_wall_neighbors(map_grid, x, y):
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy

            if nx < 0 or ny < 0 or nx >= COLS or ny >= ROWS:
                count += 1
            elif map_grid[nx][ny] == 1:
                count += 1

    return count

# ----------------------------
# SIMULATION
# ----------------------------
def simulation_step(map_grid):
    new_map_grid = []

    for x in range(COLS):
        column = []
        for y in range(ROWS):
            n = count_wall_neighbors(map_grid, x, y)
            column.append(1 if n > 4 else 0)
        new_map_grid.append(column)

    return new_map_grid

# ----------------------------
# DRAW map_grid
# ----------------------------
def draw_map_grid(map_grid):
    for x in range(COLS):
        for y in range(ROWS):
            rect = pygame.Rect(
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            color = (40, 40, 40) if map_grid[x][y] else (200, 200, 200)
            pygame.draw.rect(screen, color, rect)

# ----------------------------
# STEP 2: GENERATE TILES
# ----------------------------
def generate_tiles(map_grid):
    tiles = []

    for tx in range(TILE_COLS):
        column = []
        for ty in range(TILE_ROWS):

            wall_count = 0
            total = 0

            for cx in range(CELLS_PER_TILE_X):
                for cy in range(CELLS_PER_TILE_Y):

                    gx = tx * CELLS_PER_TILE_X + cx
                    gy = ty * CELLS_PER_TILE_Y + cy

                    total += 1
                    if map_grid[gx][gy] == 1:
                        wall_count += 1
                        
            if wall_count / total > 0.9:
                column.append(1)
            else:
                column.append(0)

        tiles.append(column)

    return tiles
 


# ----------------------------
# DRAW TILES
# ----------------------------
def draw_tiles(tiles):
    for x in range(TILE_COLS):
        for y in range(TILE_ROWS):

            rect = pygame.Rect(
                x * TILE_SIZE_X,
                y * TILE_SIZE_Y,
                TILE_SIZE_X,
                TILE_SIZE_Y
            )

            color = (0, 255, 0) if tiles[x][y] == 0 else (0, 0, 0)
            pygame.draw.rect(screen, color, rect)

# ----------------------------
# GENERATE ALL
# ----------------------------
def generate_all():
    map_grid = initialize_map_grid()
    for _ in range(ITERATIONS):
        map_grid = simulation_step(map_grid)

    tiles = generate_tiles(map_grid)


    return map_grid, tiles

# ----------------------------
# MAIN
# ----------------------------
map_grid, tiles = generate_all()

running = True
while running:
    clock.tick(60)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                map_grid, tiles = generate_all()

    draw_tiles(tiles)

    pygame.display.flip()

pygame.quit()