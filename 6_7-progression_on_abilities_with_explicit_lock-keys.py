import pygame
import random
import sys

# ----------------------------
# CONFIGURAÇÃO GERAL
# ----------------------------
WIDTH, HEIGHT = 1100, 800
SIDEBAR_WIDTH = 380
CELL_SIZE = 16
COLS, ROWS = (WIDTH - SIDEBAR_WIDTH) // CELL_SIZE, HEIGHT // CELL_SIZE
TILE_SIZE = 2 * CELL_SIZE 

# ----------------------------
# 1. THE PROGRESSION GRAPH (The Rules)
# ----------------------------
PROGRESSION = {
    "GATE": "Combat_Mastery",      # To pass a Gate, you need Combat Mastery
    "BOSS_CAVE": "Elite_Combat"    # To enter Boss, you need Elite Combat
}

DEPENDENCIES = {
    "Combat_Mastery": "Basic_Weaponry",
    "Elite_Combat": "Combat_Mastery"
}

UNLOCK_LOCATIONS = {
    "Basic_Weaponry": "WRECKED_SHIP",
    "Combat_Mastery": "OLD_FORTRESS",
    "Elite_Combat": "HERMIT_HUT"
}

# ----------------------------
# 2. THE MISSION GRAMMAR (The Content)
# ----------------------------
GRAMMAR = {
    "MISSION": [
        ["START", "OBJECTIVE", "GOAL"],
        ["START", "ENCOUNTER", "OBJECTIVE", "GOAL"],
    ],
    "OBJECTIVE": [["GATE"]], # The Grammar chooses the obstacle
    "ENCOUNTER": [["ENEMY_CAMP"], ["AMBUSH"]],
    "GOAL": [["RUINS"], ["BOSS_CAVE"]]
}

# ----------------------------
# 3. MISSION DIRECTOR (The Logic Bridge)
# ----------------------------
class MissionDirector:
    def __init__(self):
        self.raw_sequence = []    # Result of Grammar
        self.final_sequence = []  # Result after Progression Repair
        self.main_path = []
        self.start_node = None
        self.end_node = None

    def expand(self, symbol):
        if symbol not in GRAMMAR: return [symbol]
        production = random.choice(GRAMMAR[symbol])
        res = []
        for s in production: res.extend(self.expand(s))
        return res

    def generate_and_repair(self):
        # Step 1: Grammar Expansion
        self.raw_sequence = self.expand("MISSION")
        
        # Step 2: Progression Repair (Recursive Skill Insertion)
        self.final_sequence = []
        for item in self.raw_sequence:
            if item in PROGRESSION:
                # Find what skills are missing for this specific obstacle
                required_skill = PROGRESSION[item]
                repair_path = self.get_skill_chain(required_skill)
                
                # Insert the unlock locations before the obstacle
                for skill in repair_path:
                    loc = UNLOCK_LOCATIONS[skill]
                    if loc not in self.final_sequence:
                        self.final_sequence.append(loc)
            
            self.final_sequence.append(item)

    def get_skill_chain(self, skill):
        """Recursively finds prerequisites."""
        chain = [skill]
        curr = skill
        while curr in DEPENDENCIES:
            pre = DEPENDENCIES[curr]
            chain.insert(0, pre)
            curr = pre
        return chain

# ----------------------------
# 4. SPATIAL & GENERATION
# ----------------------------
class Node:
    def __init__(self, x, y, walkable):
        self.x, self.y = x, y
        self.walkable = walkable
        self.neighbors = []
        self.tag = None 

def generate_cave():
    grid = [[1 if random.random() < 0.45 else 0 for _ in range(ROWS)] for _ in range(COLS)]
    for _ in range(4):
        new_grid = [[0 for _ in range(ROWS)] for _ in range(COLS)]
        for x in range(COLS):
            for y in range(ROWS):
                walls = sum(1 for dx in [-1,0,1] for dy in [-1,0,1] if 0<=x+dx<COLS and 0<=y+dy<ROWS and grid[x+dx][y+dy]==1)
                new_grid[x][y] = 1 if walls > 4 else 0
        grid = new_grid
    return grid

def find_path(start, end):
    queue = [(start, [start])]
    visited = {start}
    while queue:
        (curr, path) = queue.pop(0)
        if curr == end: return path
        for n in curr.neighbors:
            if n.walkable and n not in visited:
                visited.add(n); queue.append((n, path + [n]))
    return []

def run_simulation():
    grid = generate_cave()
    nodes = {}
    for tx in range(COLS // 2):
        for ty in range(ROWS // 2):
            walls = sum(grid[tx*2+cx][ty*2+cy] for cx in range(2) for cy in range(2))
            nodes[(tx, ty)] = Node(tx, ty, walls < 2)
    for (tx, ty), node in nodes.items():
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            if (tx+dx, ty+dy) in nodes: node.neighbors.append(nodes[(tx+dx, ty+dy)])

    director = MissionDirector()
    director.generate_and_repair()
    
    walkable = [n for n in nodes.values() if n.walkable]
    if len(walkable) < 100: return run_simulation()

    director.start_node = min(walkable, key=lambda n: n.x)
    director.end_node = max(walkable, key=lambda n: n.x)
    
    path = find_path(director.start_node, director.end_node)
    if not path or len(path) < 25: return run_simulation()
    director.main_path = path

    # Place entities along the path
    for i, symbol in enumerate(director.final_sequence):
        if symbol in ["START", "RUINS"]: continue
        pos_idx = int((len(path) / len(director.final_sequence)) * i)
        pivot = path[min(pos_idx, len(path)-1)]
        
        # Place off-road
        for n in pivot.neighbors:
            if n.walkable and n not in path:
                n.tag = symbol
                break
    return grid, nodes, director

# ----------------------------
# 5. VISUALIZATION
# ----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("Courier New", 12, bold=True)
header = pygame.font.SysFont("Courier New", 15, bold=True)

def draw_sidebar(director):
    ui_x = WIDTH - SIDEBAR_WIDTH + 20
    
    # Show Raw Grammar
    y = 30
    screen.blit(header.render("1. GRAMMAR (RAW)", True, (255, 255, 255)), (ui_x, y))
    y += 25
    for s in director.raw_sequence:
        screen.blit(font.render(f"- {s}", True, (150, 150, 150)), (ui_x + 10, y))
        y += 18

    # Show Final Mission (Repaired with Skills)
    y += 30
    screen.blit(header.render("2. FINAL MISSION (REPAIRED)", True, (255, 255, 255)), (ui_x, y))
    y += 25
    for i, s in enumerate(director.final_sequence):
        col = (200, 200, 200)
        if s in UNLOCK_LOCATIONS.values(): col = (0, 200, 255) # Skills
        if s in PROGRESSION: col = (255, 120, 0) # Gates/Obstacles
        
        pygame.draw.circle(screen, col, (ui_x + 5, y + 7), 4)
        screen.blit(font.render(f"{i+1}. {s}", True, col), (ui_x + 15, y))
        y += 22

def main():
    grid, nodes, director = run_simulation()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                grid, nodes, director = run_simulation()

        screen.fill((20, 20, 25))
        for x in range(COLS):
            for y in range(ROWS):
                col = (40, 40, 45) if grid[x][y] else (180, 180, 185)
                pygame.draw.rect(screen, col, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        if director.main_path:
            pts = [(n.x*TILE_SIZE + 16, n.y*TILE_SIZE + 16) for n in director.main_path]
            pygame.draw.lines(screen, (255, 215, 0), False, pts, 3)

        for node in nodes.values():
            pos = (node.x*TILE_SIZE + 16, node.y*TILE_SIZE + 16)
            if node == director.start_node: pygame.draw.circle(screen, (0, 255, 0), pos, 12)
            elif node == director.end_node: pygame.draw.circle(screen, (255, 0, 0), pos, 12)
            elif node.tag:
                col = (0, 150, 255) if node.tag in UNLOCK_LOCATIONS.values() else (255, 120, 0)
                if "ENEMY" in node.tag or "AMBUSH" in node.tag: col = (200, 50, 50)
                pygame.draw.rect(screen, col, (pos[0]-10, pos[1]-10, 20, 20))
                screen.blit(font.render(node.tag, True, (0,0,0)), (pos[0]+15, pos[1]-10))

        pygame.draw.rect(screen, (10, 10, 15), (WIDTH-SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))
        draw_sidebar(director)
        pygame.display.flip()

if __name__ == "__main__":
    main()