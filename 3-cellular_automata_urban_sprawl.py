import pygame
import random

WIDTH, HEIGHT = 600, 600
CELL_SIZE = 8
COLS = WIDTH // CELL_SIZE
ROWS = HEIGHT // CELL_SIZE

EMPTY = 0
BUILDING = 1
ROAD = 2

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

def initialize():
    grid = [[EMPTY for _ in range(ROWS)] for _ in range(COLS)]

    # Road cross
    for x in range(COLS):
        grid[x][ROWS // 2] = ROAD
    for y in range(ROWS):
        grid[COLS // 2][y] = ROAD

    return grid

def count_neighbors(grid, x, y, state):
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                if grid[nx][ny] == state:
                    count += 1
    return count

def step(grid):
    new_grid = [row[:] for row in grid]

    for x in range(COLS):
        for y in range(ROWS):

            if grid[x][y] == ROAD:
                continue

            building_neighbors = count_neighbors(grid, x, y, BUILDING)
            road_neighbors = count_neighbors(grid, x, y, ROAD)

            if grid[x][y] == EMPTY:
                if building_neighbors >= 3 or road_neighbors > 0:
                    if random.random() < 0.3:
                        new_grid[x][y] = BUILDING

            elif grid[x][y] == BUILDING:
                if building_neighbors <= 1:
                    new_grid[x][y] = EMPTY

    return new_grid

def draw(grid):
    for x in range(COLS):
        for y in range(ROWS):
            rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)

            if grid[x][y] == EMPTY:
                color = (25, 25, 30)
            elif grid[x][y] == BUILDING:
                color = (220, 220, 230)
            elif grid[x][y] == ROAD:
                color = (90, 90, 90)

            pygame.draw.rect(screen, color, rect)

grid = initialize()
running = True

while running:
    clock.tick(5)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    grid = step(grid)

    screen.fill((0,0,0))
    draw(grid)
    pygame.display.flip()

pygame.quit()