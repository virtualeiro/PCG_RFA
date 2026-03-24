import pygame
import random
"""
procedural cave system using Cellular Automata and then 
abstracts that map into a navigation graph. 

Step 1: Initialize the Map Grid
The world is treated as a high-resolution grid of "cells."
Random Seed: Every cell is randomly assigned to be a Wall (1) or Floor (0) 
based on the WALL_PROBABILITY (60%).
At this stage, the map looks like "static" on a TV screen—completely chaotic.

Step 2: Cellular Automata Simulation (Cave Smoothing)
To turn the "static" into organic caves, the code runs a simulation for 5 iterations:
Neighbor Counting: For every cell, it counts how many of its 8 neighbors are walls.
The Rule: If a cell has more than 4 wall neighbors, it becomes a wall. 
Otherwise, it becomes floor.
Result: Small gaps are filled, and lone blocks are deleted, resulting in smooth,
 connected cavern structures.

Step 3: Tile Generation (Downsampling)
The high-resolution map_grid is too detailed for complex pathfinding. 
The code "shrinks" the map into larger Tiles (2x2 cells):
Averaging: It looks at the group of cells inside a tile.
Threshold: If more than 90% of the cells in that area are walls, 
the entire Tile is marked as a Wall (1). 
Otherwise, it is a Walkable Floor (0).

Step 4: Building the Graph
The code converts the simplified Tile map into a mathematical Graph for navigation:
Nodes: Every tile becomes a Node object. 
It stores its position and whether it is "walkable."
Adjacency: Every node is automatically connected to its 4 immediate neighbors (Up, Down, Left, Right).

Step 5: Visualization (The Pygame Loop)
The final step renders three distinct layers on top of each other:
Background (draw_map_grid): Draws the raw cells 
(Dark Gray for walls, Light Gray for floors).
Overlays (draw_tiles): Draws green outlines over the larger "Walkable" areas.
Pathfinding Layer (draw_graph): * Nodes: Draws small Green circles for walkable areas 
and Red circles for walls.
Edges: Draws Blue lines showing valid paths between floor nodes and 
Gray lines for blocked paths.
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
    return [
        [1 if random.random() < WALL_PROBABILITY else 0 for y in range(ROWS)]
        for x in range(COLS)
    ]

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
# STEP 3: GRAPH TILES
# ----------------------------
#Each tile becomes a:
#        Node(x, y)
#Each node stores:
#        Position
#        Walkable or not
#        Neighbors (up, down, left, right) 
class Node:
    def __init__(self, x, y, walkable):
        self.x = x
        self.y = y
        self.walkable = walkable
        self.neighbors = []
#-------------------------
def build_graph(tiles):
   
    nodes = {}

    # Create nodes
    for x in range(TILE_COLS):
        for y in range(TILE_ROWS):
            nodes[(x, y)] = Node(x, y, tiles[x][y] == 0)

    # Connect neighbors
    for x in range(TILE_COLS):
        for y in range(TILE_ROWS):
            node = nodes[(x, y)]

            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in nodes:
                    node.neighbors.append(nodes[(nx, ny)])

    return nodes

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
            pygame.draw.rect(screen, color, rect, 2)

# ----------------------------
# GENERATE ALL
# ----------------------------
def generate_all():
    map_grid = initialize_map_grid()
    for _ in range(ITERATIONS):
        map_grid = simulation_step(map_grid)

    tiles = generate_tiles(map_grid)
    graph = build_graph(tiles)

    return map_grid, tiles, graph

#STEP4 
# Draw graph connections and nodes
def draw_graph(graph):
    for node in graph.values():

        # Convert tile position → pixel center
        px = node.x * TILE_SIZE_X + TILE_SIZE_X // 2
        py = node.y * TILE_SIZE_Y + TILE_SIZE_Y // 2

        # Draw edges first (so nodes appear on top)
        for neighbor in node.neighbors:
            npx = neighbor.x * TILE_SIZE_X + TILE_SIZE_X // 2
            npy = neighbor.y * TILE_SIZE_Y + TILE_SIZE_Y // 2

            # Edge color: depends on walkability
            if node.walkable and neighbor.walkable:
                color = (0, 150, 255)   # blue = walkable connection
            else:
                color = (100, 100, 100) # gray = blocked connection
            pygame.draw.line(screen, color, (px, py), (npx, npy), 1)

        # Draw node
        if node.walkable:
            color = (0, 255, 0)  # green
        else:
            color = (255, 0, 0)  # red
        pygame.draw.circle(screen, color, (px, py), 4)

# ----------------------------
# MAIN
# ----------------------------
map_grid, tiles, graph = generate_all()

running = True
while running:
    clock.tick(60)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                map_grid, tiles, graph = generate_all()

    draw_map_grid(map_grid)
    draw_tiles(tiles)
    draw_graph(graph)
    pygame.display.flip()

pygame.quit()