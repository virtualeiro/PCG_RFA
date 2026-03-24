from importlib.resources import path

import pygame
import random
from collections import deque
"""
Mission placement using BFS distances → creates a progression curve
The “progress graph” is essentially:
-A graph of walkable tiles
-With distance-from-start = progression over time


Missão ao longo do caminho principal 
- O caminho principal é o mais longo possível (encontrado por BFS)
- Os elementos da missão são colocados ao longo do caminho principal, usando a distância do início
- O caminho é bloqueado por portas trancadas, que exigem chaves colocadas antes delas
- Ramo opcional: conteúdo extra (tesouro, inimigos)
 pode ser colocado em caminhos secundários conectados 
 ao caminho principal    
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
        ["KEY", "DOOR", "TREASURE"],
        ["TREASURE", "KEY"]
        ],

    "ENCOUNTER": [
        ["ENEMY"],
        ["ENEMY", "ENEMY"],
        ["ENEMY", "ENEMY", "ENEMY"],
        ["ENEMY", "ENEMY", "ENEMY", "ENEMY"] 
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

def expand(symbol):
    if symbol not in GRAMMAR:
        return [symbol]

    production = random.choice(GRAMMAR[symbol])
    result = []

    for sym in production:
        result.extend(expand(sym))
    return result

#STEP6: ENSURE MISSION REQUIREMENTS
def ensure_mission_requirements(mission):

    present = set(mission)

    # Always ensure START is first
    if "START" not in present:
        mission.insert(0, "START")

    # Always ensure EXIT is last
    if "EXIT" not in present:
        mission.append("EXIT")

    # Add missing elements in logical positions
    if "KEY" not in present:
        mission.insert(len(mission)//2, "KEY")

    if "DOOR" not in present:
        mission.insert(len(mission)//2 + 1, "DOOR")

    if "BOSS" not in present:
        # boss near the end (before exit)
        if "EXIT" in mission:
            idx = mission.index("EXIT")
            mission.insert(idx, "BOSS")
        else:
            mission.append("BOSS")

    return mission

def generate_mission():
    mission = expand("MISSION")
    #STEP 6
    mission = ensure_mission_requirements(mission)
    return mission
#------------------------------
def bfs_with_parents(start_node):
    visited = {start_node: 0}
    parent = {start_node: None}
    queue = deque([start_node])

    while queue:
        current = queue.popleft()

        for n in current.neighbors:
            if n.walkable and n not in visited:
                visited[n] = visited[current] + 1
                parent[n] = current
                queue.append(n)

    return visited, parent


def get_farthest_node(distances):
    return max(distances.items(), key=lambda x: x[1])[0]


def reconstruct_path(parent_map, end_node):
    path = []
    current = end_node

    while current is not None:
        path.append(current)
        current = parent_map[current]

    path.reverse()
    return path


def find_longest_path(graph):
    walkable_nodes = get_walkable_nodes(graph)

    # Step 1: random start
    start = random.choice(walkable_nodes)

    # Step 2: farthest from start → A
    dist1, _ = bfs_distances(start), None
    A = get_farthest_node(dist1)

    # Step 3: farthest from A → B
    dist2, parent = bfs_with_parents(A)
    B = get_farthest_node(dist2)

    # Step 4: path A → B
    path = reconstruct_path(parent, B)

    return path
#----------------------------------------------------------
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
class Node:
    def __init__(self, x, y, walkable):
        self.x = x
        self.y = y
        self.walkable = walkable
        self.neighbors = []
        #Step 5
        self.content = None  # what is placed here
        self.locked = False

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


#STEP5: PLACE MISSION CONTENT
def get_walkable_nodes(graph):
    return [n for n in graph.values() if n.walkable]


def bfs_distances(start_node, has_key=False):
    visited = {start_node: 0}
    queue = deque([start_node])

    while queue:
        current = queue.popleft()

        for n in current.neighbors:

            #  Block locked door if no key
            if n.locked and not has_key:
                continue

            if n.walkable and n not in visited:
                visited[n] = visited[current] + 1
                queue.append(n)

    return visited


def assign_mission_to_graph(graph, mission):

    path = find_longest_path(graph)

    if len(path) == 0:
        return None

    main_path_set = set(path)

    step = max(1, len(path) // len(mission))

    key_node = None
    door_node = None

    for i, element in enumerate(mission):
        idx = min(i * step, len(path) - 1)
        node = path[idx]
        node.content = element

        if element == "KEY":
            key_node = node
        elif element == "DOOR":
            door_node = node

    if door_node:
        door_node.locked = True

    # 🌿 Add branches
    place_optional_content(graph, main_path_set)

    return path[0]

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

def get_branch_nodes(graph, main_path_set):
    branches = []

    for node in graph.values():
        if not node.walkable:
            continue

        if node in main_path_set:
            continue

        # If connected to main path → candidate branch
        for n in node.neighbors:
            if n in main_path_set:
                branches.append(node)
                break

    return branches

def place_optional_content(graph, main_path_set):

    branches = get_branch_nodes(graph, main_path_set)

    for node in branches:

        r = random.random()

        if r < 0.1:
            node.content = "TREASURE"
        elif r < 0.25:
            node.content = "ENEMY"      
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