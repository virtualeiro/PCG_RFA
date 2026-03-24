from turtle import distance, right

import pygame
import random
from collections import deque
"""

1. Generate cave (cellular automata)
2. Aggregate into tiles
3. Build graph (nodes + neighbors)
    Each tile becomes a:
        Node(x, y)
    Each node stores:
        Position
        Walkable or not
        Neighbors (up, down, left, right)
4. Generate mission (grammar)
5. Map mission onto graph (using BFS distance)
    We stretch the map into a line from start to farthest point, 
    then drop mission events along that line.
6. Draw everything
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
#----------------------------------------------------------
#"START -> KEY -> DOOR -> GOAL"
#"START -> ENEMY -> KEY -> GOAL"
#"START -> TREASURE -> ENEMY -> EXIT"
# ----------------------------
# MISSION GRAMMAR
# ----------------------------
GRAMMAR = {
    "MISSION": [
        ["START", "OBJECTIVE", "GOAL"],
        ["START", "ENCOUNTER", "OBJECTIVE", "GOAL"],
    ],

    "OBJECTIVE": [
        ["KEY", "DOOR"],
        ["TREASURE"],
    ],

    "ENCOUNTER": [
        ["ENEMY"],
        ["ENEMY", "ENEMY"]
    ],

    "GOAL": [
        ["EXIT"],
        ["BOSS"]
    ]
}
# ----------------------------
# MISSION COLORS
# ----------------------------
MISSION_COLORS = {
    "START": (0, 255, 255),     # cyan
    "EXIT": (255, 255, 255),    # white
    "KEY": (255, 255, 0),       # yellow
    "DOOR": (255, 165, 0),      # orange
    "ENEMY": (255, 0, 0),       # red
    "BOSS": (0, 0, 0),      # black
    "TREASURE": (0, 255, 0),    # green
}
#----------------------------
#Recursive expansion:
#Result: An ordered list of gameplay events
#START → KEY → DOOR → EXIT
#START → ENEMY → TREASURE → BOSS
def expand(symbol):
    if symbol not in GRAMMAR:
        return [symbol]

    production = random.choice(GRAMMAR[symbol])
    result = []

    for sym in production:
        result.extend(expand(sym))
    print(f"Expanded {symbol} → {production} → {result}")
    return result

def generate_mission():
    return expand("MISSION")

#----------------------------------------------------------
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
# STEP 3: GRAPH TILES
# ----------------------------
class Node:
    def __init__(self, x, y, walkable):
        self.x = x
        self.y = y
        self.walkable = walkable
        self.neighbors = []
        #Step 5
        self.content = None  # what is placed here
#-------------------------
def build_graph(tiles):
#Each tile becomes a:
#        Node(x, y)
#Each node stores:
#        Position
#        Walkable or not
#        Neighbors (up, down, left, right)
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

    mission = generate_mission()
    start_node = assign_mission_to_graph(graph, mission)

    return map_grid, tiles, graph, mission

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

#-----------------------------
#STEP5: PLACE MISSION CONTENT
def get_walkable_nodes(graph):
    return [n for n in graph.values() if n.walkable]

#Compute BFS distances from start node to all others
#Start from a random walkable node
#Use BFS to compute distance to all others
def bfs_distances(start_node):
    visited = {start_node: 0}
    queue = deque([start_node])
    while queue:
        current = queue.popleft()
        for n in current.neighbors:
            if n.walkable and n not in visited:
                visited[n] = visited[current] + 1
                queue.append(n)
    return visited
#-------------------------------------------------
#Take all reachable nodes, sort them from near → far,
#  and place mission elements along that line.
def assign_mission_to_graph(graph, mission):
    walkable_nodes = get_walkable_nodes(graph)
    start_node = random.choice(walkable_nodes)
    #1-Compute BFS distances from start node to all others
    distances = bfs_distances(start_node)

    #2-Sort nodes by distance (farther = later mission elements)
    #creates a progression gradient:
    #Near = early
    #Far = late
    sorted_nodes = sorted(distances.items(), key=lambda x: x[1])
    #3-Distribute mission elements along this distance gradient
    #Nodes:    100
    #Mission:  5 elements
    #step = 100 // 5 = 20
    #Meaning:
    #Place one mission element every 20 nodes
    step = max(1, len(sorted_nodes) // len(mission))
    #4-Loop Through Mission
    #e.g ["START", "KEY", "DOOR", "BOSS", "EXIT"]
    #i = 0 → START  
    #i = 1 → KEY  
    #i = 2 → DOOR  
    #i = 3 → BOSS  
    #i = 4 → EXIT  
    for i, element in enumerate(mission):
        #Compute index along sorted nodes
        idx = min(i * step, len(sorted_nodes) - 1)
        #assign mission element to that node
        #e.g Node at distance 0   → START  
        #e.g Node at distance 20  → KEY  
        node = sorted_nodes[idx][0]
        node.content = element
    return start_node
#----------------------------
# VISUALIZE MISSION GRAPH GRAMMAR
#----------------------------
def draw_mission(graph):
    font = pygame.font.SysFont(None, 18)

    for node in graph.values():
        if node.content is None:
            continue

        px = node.x * TILE_SIZE_X + TILE_SIZE_X // 2
        py = node.y * TILE_SIZE_Y + TILE_SIZE_Y // 2
        
        # Draw filled circle (main visual)
        # Get color
        color = MISSION_COLORS.get(node.content, (200, 200, 200))
        pygame.draw.circle(screen, color, (px, py), 15)
         
        font = pygame.font.SysFont('Arial', 26, bold = True)
        text = font.render(node.content[0], True, (255, 0, 255))
        screen.blit(text, (px - 8, py - 15))

       
# ----------------------------
# MAIN
# ----------------------------
map_grid, tiles, graph, mission = generate_all()
print("Mission:", mission)

running = True
while running:
    clock.tick(60)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                map_grid, tiles, graph, mission = generate_all()
                print("Mission:", mission)

    draw_map_grid(map_grid)
    draw_tiles(tiles)
    draw_graph(graph)
    draw_mission(graph)
    pygame.display.flip()

pygame.quit()