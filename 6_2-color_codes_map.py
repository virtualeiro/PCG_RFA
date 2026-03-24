import random
import pygame

"""
ISLAND GENERATOR - COLOR VISUALIZER (NO SPRITES)

- Cellular Automata generates land/water
- 2x2 cells → 4-bit mask (0–15)
- Each mask is visualized with a color instead of a sprite
"""

# ----------------------------
# CONFIGURATION
# ----------------------------
WIDTH, HEIGHT = 800, 800
CELL_SIZE = 16

COLS = WIDTH // CELL_SIZE
ROWS = HEIGHT // CELL_SIZE

WALL_PROBABILITY = 0.60
ITERATIONS = 5

# TILE CONFIG (2x2 cells = 1 tile)
CELLS_PER_TILE = 2
TILE_SIZE = CELL_SIZE * CELLS_PER_TILE

TILE_COLS = COLS // CELLS_PER_TILE
TILE_ROWS = ROWS // CELLS_PER_TILE

# Toggle debug view (shows 2x2 structure)
DEBUG_BITMASK = False

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Island Generator (Color Mode) - SPACE to regenerate")
clock = pygame.time.Clock()

# ----------------------------
# COLOR MAPPING
# ----------------------------
def get_tile_color(index):
    # Water
    if index == 0:
        return (30, 60, 150)

    # Full land
    if index == 15:
        return (20, 120, 40)

    # Straight coastlines
    if index in [3, 5, 10, 12]:
        return (240, 230, 140)  # sand

    # Outer corners
    if index in [1, 2, 4, 8]:
        return (100, 200, 100)

    # Inner corners (bays)
    if index in [7, 11, 13, 14]:
        return (50, 160, 80)

    # Diagonals / rare
    return (180, 100, 180)

# ----------------------------
# LOGIC FUNCTIONS
# ----------------------------
def initialize_map_grid():
    return [[1 if random.random() < WALL_PROBABILITY else 0
             for _ in range(ROWS)] for _ in range(COLS)]

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

def simulation_step(map_grid):
    new_map_grid = [[0 for _ in range(ROWS)] for _ in range(COLS)]

    for x in range(COLS):
        for y in range(ROWS):
            n = count_wall_neighbors(map_grid, x, y)
            new_map_grid[x][y] = 1 if n > 4 else 0

    return new_map_grid

def generate_tiles(map_grid):
    tiles = []

    for tx in range(TILE_COLS):
        column = []
        for ty in range(TILE_ROWS):
            gx, gy = tx * 2, ty * 2

            tl = map_grid[gx][gy]
            tr = map_grid[gx + 1][gy]
            bl = map_grid[gx][gy + 1]
            br = map_grid[gx + 1][gy + 1]

            tile_index = (tl * 1) + (tr * 2) + (bl * 4) + (br * 8)
            column.append(tile_index)

        tiles.append(column)

    return tiles

def generate_all():
    grid = initialize_map_grid()

    for _ in range(ITERATIONS):
        grid = simulation_step(grid)

    return grid, generate_tiles(grid)

# ----------------------------
# DEBUG DRAW (2x2 CELLS)
# ----------------------------
def draw_bitmask_debug(x, y, tile_index):
    gx = x * TILE_SIZE
    gy = y * TILE_SIZE
    half = TILE_SIZE // 2

    bits = [
        (tile_index & 1),
        (tile_index & 2) >> 1,
        (tile_index & 4) >> 2,
        (tile_index & 8) >> 3
    ]

    colors = [
        (30, 60, 150),   # water
        (20, 120, 40)    # land
    ]

    pygame.draw.rect(screen, colors[bits[0]], (gx, gy, half, half))
    pygame.draw.rect(screen, colors[bits[1]], (gx + half, gy, half, half))
    pygame.draw.rect(screen, colors[bits[2]], (gx, gy + half, half, half))
    pygame.draw.rect(screen, colors[bits[3]], (gx + half, gy + half, half, half))

# ----------------------------
# MAIN LOOP
# ----------------------------
map_grid, tiles = generate_all()

running = True
while running:
    clock.tick(60)

    screen.fill((40, 80, 160))  # ocean background

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                map_grid, tiles = generate_all()

            if event.key == pygame.K_d:
                DEBUG_BITMASK = not DEBUG_BITMASK

    for x in range(TILE_COLS):
        for y in range(TILE_ROWS):
            tile_index = tiles[x][y]

            if DEBUG_BITMASK:
                draw_bitmask_debug(x, y, tile_index)
            else:
                color = get_tile_color(tile_index)

                pygame.draw.rect(
                    screen,
                    color,
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )

    pygame.display.flip()

pygame.quit()