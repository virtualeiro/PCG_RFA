import pygame
import random
import heapq

# =========================
# CONFIG
# =========================
GRID_SIZE = 20
CELL_SIZE = 25
WINDOW_SIZE = GRID_SIZE * CELL_SIZE

GRAPH_HEIGHT = 140
TOTAL_HEIGHT = WINDOW_SIZE + GRAPH_HEIGHT

LEVEL_FITNESS_THRESHOLD = 0.70

WHITE = (255,255,255)
BLACK = (30,30,30)
GRAY = (100,100,100)

RED = (200,50,50)
GREEN = (50,200,100)
BLUE = (50,100,255)
YELLOW = (255,230,100)

CYAN = (50,220,220)

# =========================
# DATA
# =========================
class GeneratedLevel:

    def __init__(self,
                 grid,
                 start,
                 end,
                 enemies,
                 obstacles):

        self.grid = grid
        self.start = start
        self.end = end
        self.enemies = enemies
        self.obstacles = obstacles

        self.fitness_score = 0.0
        self.path = []


# =========================
# A*
# =========================
def astar_path(grid, start, end):

    rows = len(grid)
    cols = len(grid[0])

    open_set = [(0, start)]

    came_from = {}

    g_score = {
        start: 0
    }

    while open_set:

        _, current = heapq.heappop(open_set)

        if current == end:

            path = []

            while current in came_from:

                path.append(current)
                current = came_from[current]

            path.append(start)
            path.reverse()

            return path

        x, y = current

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:

            nx = x + dx
            ny = y + dy

            if 0 <= nx < rows and 0 <= ny < cols:

                if grid[nx][ny] == 1:
                    continue

                neighbor = (nx, ny)

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:

                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g

                    f_score = (
                        tentative_g +
                        abs(nx - end[0]) +
                        abs(ny - end[1])
                    )

                    heapq.heappush(
                        open_set,
                        (f_score, neighbor)
                    )

    return None


# =========================
# OBSTACLE DENSITY
# =========================
#[180,120,60,0,0,0,0] clear
#[5,20,40,80,120,90] DENSE 
"""
| Bin Range | Spatial Interpretation     | Possible Player Experience |
| --------- | -------------------------- | -------------------------- |
| 0.0-0.1   | Very open                  | Calm, readable, exposed    |
| 0.1-0.2   | Mostly open                | Easy navigation            |
| 0.2-0.3   | Mild clutter               | Some tactical structure    |
| 0.3-0.4   | Moderate clutter           | Increased attention demand |
| 0.4-0.5   | Dense local geometry       | Maze-like movement         |
| 0.5-0.6   | Highly constrained         | Claustrophobic             |
| 0.6-0.7   | Near-blocked regions       | Stressful navigation       |
| 0.7-0.8   | Extremely dense            | Chokepoint-heavy           |
| 0.8-0.9   | Almost enclosed            | Severe restriction         |
| 0.9-1.0   | Fully blocked environments | Often unplayable           |
"""

def local_obstacle_density(grid, radius=2):

    rows = len(grid)
    cols = len(grid[0])

    densities = []

    for x in range(rows):
        for y in range(cols):

            obstacle_count = 0
            total = 0

            for dx in range(-radius, radius+1):
                for dy in range(-radius, radius+1):

                    nx = x + dx
                    ny = y + dy

                    if 0 <= nx < rows and 0 <= ny < cols:

                        total += 1

                        if grid[nx][ny] == 1:
                            obstacle_count += 1

            density = obstacle_count / total
            densities.append(density)

    return densities


def density_histogram(values, bins=10):

    hist = [0] * bins

    for v in values:

        index = min(int(v * bins), bins-1)

        hist[index] += 1

    return hist


# =========================
# CONNECTIVITY
# =========================
#Finds every connected region of walkable tiles (0)
#Uses flood fill (stack) to measure the size of each region
#we get values like [400] for a fully connected map, or [50, 30, 20] for a fragmented map with 3 separate open areas of those sizes.

#[180] highly connected one single region
#[5,20,40,80,120] fragmented map with multiple disconnected regions

"""
| Region Size | Spatial Interpretation    | Possible Experience         |
| ----------- | ------------------------- | --------------------------- |
| 1-5         | Tiny isolated pockets     | Dead zones, inaccessible    |
| 5-20        | Small disconnected areas  | Secrets, isolated rooms     |
| 20-50       | Moderate regions          | Partial exploration islands |
| 50-100      | Large connected subspaces | Distinct gameplay zones     |
| 100-200     | Major traversable sectors | Strong exploration          |
| 200+        | Giant connected world     | Openness, freedom           |
"""
def connectivity_histogram(grid):

    rows = len(grid)
    cols = len(grid[0])

    visited = set()

    region_sizes = []

    def flood_fill(start):

        stack = [start]
        size = 0

        while stack:

            x, y = stack.pop()

            if (x, y) in visited:
                continue

            visited.add((x,y))

            size += 1

            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:

                nx = x + dx
                ny = y + dy

                if 0 <= nx < rows and 0 <= ny < cols:

                    if grid[nx][ny] == 0:
                        stack.append((nx, ny))

        return size

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 0 and (x,y) not in visited:

                region_sizes.append(
                    flood_fill((x,y))
                )

    return region_sizes


# =========================
# CORRIDOR WIDTH
# =========================
#how much free space exists around a cell before hitting an obstacle
#If a wall is right next to you → low value
#If you are in an open room → high value
"""
Bin	Meaning
0	lowest clearance in THIS level
9	highest clearance in THIS level
"""
def corridor_width_histogram(grid, bins=10):

    rows = len(grid)
    cols = len(grid[0])

    widths = []

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            min_dist = 999

            for ox in range(rows):
                for oy in range(cols):

                    if grid[ox][oy] == 1:

                        d = abs(x - ox) + abs(y - oy)
                        min_dist = min(min_dist, d)

            widths.append(min_dist)

    # =========================
    # BIN INTO HISTOGRAM
    # =========================
    hist = [0] * bins

    if widths:
        max_w = max(widths)

        for w in widths:

            idx = int((w / max_w) * (bins - 1))
            hist[idx] += 1

    return hist
"""
per-cell measurements
good for heatmaps
def corridor_space_field(grid):

    rows = len(grid)
    cols = len(grid[0])

    widths = []

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            min_dist = 999

            for ox in range(rows):
                for oy in range(cols):

                    if grid[ox][oy] == 1:

                        d = abs(x - ox) + abs(y - oy)

                        min_dist = min(min_dist, d)

            widths.append(min_dist)

    return widths

"""
# =========================
# VISIBILITY
# =========================
#[0, 10, 50, 120, 80, 30, 5, 0, 0, 0]
#most of the map has medium visibility, few extreme open zones
def visibility_histogram(grid, bins=10):

    rows = len(grid)
    cols = len(grid[0])

    visibilities = []

    directions = [(-1,0),(1,0),(0,-1),(0,1)]

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            visible = 0

            for dx, dy in directions:

                nx, ny = x, y

                while True:

                    nx += dx
                    ny += dy

                    if not (0 <= nx < rows and 0 <= ny < cols):
                        break

                    if grid[nx][ny] == 1:
                        break

                    visible += 1

            visibilities.append(visible)

    # =========================
    # BIN INTO HISTOGRAM
    # =========================
    hist = [0] * bins

    if visibilities:
        max_v = max(visibilities)

        for v in visibilities:

            idx = int((v / max_v) * (bins - 1))
            hist[idx] += 1

    return hist
"""
def visibility_hspace_field(grid):

    rows = len(grid)
    cols = len(grid[0])

    visibilities = []

    directions = [
        (-1,0),
        (1,0),
        (0,-1),
        (0,1)
    ]

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            visible = 0

            for dx, dy in directions:

                nx = x
                ny = y

                while True:

                    nx += dx
                    ny += dy

                    if not (0 <= nx < rows and 0 <= ny < cols):
                        break

                    if grid[nx][ny] == 1:
                        break

                    visible += 1

            visibilities.append(visible)

    return visibilities
"""

# =========================
# PATH CURVATURE
# =========================
#[0,0,0,0,1,0] mostly straight path
#[1,1,1,0,1,1] many turns
"""
| Curvature Value | Spatial Interpretation | Possible Experience          |
| ----------------- | ---------------------- | ---------------------------- |
| 0                 | Straight path          | Easy navigation              |
| 1                 | Slight turn            | Minor adjustment             |
| 2                 | Sharp turn             | Noticeable change            |
| 3                 | Severe turn            | Significant adjustment       |
"""
def path_curvature_histogram(path):

    turns = []

    for i in range(1, len(path)-1):

        x1, y1 = path[i-1]
        x2, y2 = path[i]
        x3, y3 = path[i+1]

        dx1 = x2 - x1
        dy1 = y2 - y1

        dx2 = x3 - x2
        dy2 = y3 - y2

        turn = (
            dx1 != dx2 or
            dy1 != dy2
        )

        turns.append(int(turn))

    return turns


# =========================
# ENEMY PRESSURE
# =========================
#[180,100,20] Safe low pressure
#[50,80,30] Moderate pressure
#[10,50,100] High pressure
"""
| Pressure Range | Spatial Interpretation   | Possible Experience    |
| -------------- | ------------------------ | ---------------------- |
| 0.0-0.2        | Very safe                | Relaxed exploration    |
| 0.2-0.4        | Mild threat presence     | Awareness required     |
| 0.4-0.6        | Moderate danger          | Tactical caution       |
| 0.6-0.8        | High threat density      | Sustained tension      |
| 0.8-1.0        | Severe pressure          | Stressful gameplay     |
| 1.0+           | Overlapping danger zones | Overwhelming intensity |

"""
def enemy_pressure_histogram(grid, enemies):

    rows = len(grid)
    cols = len(grid[0])

    pressures = []

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            total_pressure = 0

            for ex, ey in enemies:

                d = abs(x - ex) + abs(y - ey)

                if d == 0:
                    pressure = 1.0
                else:
                    pressure = 1 / d

                total_pressure += pressure

            pressures.append(total_pressure)

    return pressures


# =========================
# EVALUATORS
# =========================
class PlayabilityEvaluator:

    def evaluate(self, level):

        path = astar_path(
            level.grid,
            level.start,
            level.end
        )

        if path:

            level.path = path
            return 1.0

        return 0.0


class HeuristicEvaluator:

    def evaluate(self, level):

        enemy_ratio = min(
            len(level.enemies) / 10,
            1.0
        )

        obstacle_ratio = min(
            len(level.obstacles) / 15,
            1.0
        )

        return 1.0 - abs(
            enemy_ratio - obstacle_ratio
        )


class DifficultyEvaluator:

    def evaluate(self, level):

        grid_size = (
            len(level.grid) *
            len(level.grid[0])
        )

        enemy_density = (
            len(level.enemies) / grid_size
        )

        path_length = (
            len(level.path)
            if level.path else 0
        )

        difficulty = (
            0.6 * enemy_density +
            0.4 * (path_length / 100)
        )

        return min(difficulty, 1.0)


# =========================
# PIPELINE
# =========================
class PCGPipeline:

    def __init__(self,
                 evaluators,
                 threshold=LEVEL_FITNESS_THRESHOLD):

        self.evaluators = evaluators
        self.threshold = threshold

    def evaluate(self, level):

        total = 0.0

        for e in self.evaluators:

            score = e.evaluate(level)

            if score == 0.0:
                return False

            total += score

        level.fitness_score = (
            total / len(self.evaluators)
        )

        return (
            level.fitness_score >=
            self.threshold
        )


# =========================
# GENERATOR
# =========================
def generate_level(size=GRID_SIZE):

    grid = [
        [0 for _ in range(size)]
        for _ in range(size)
    ]

    obstacles = []

    for _ in range(random.randint(20,60)):

        x = random.randint(0,size-1)
        y = random.randint(0,size-1)

        grid[x][y] = 1

        obstacles.append((x,y))

    enemies = []

    for _ in range(random.randint(5,20)):

        enemies.append((
            random.randint(0,size-1),
            random.randint(0,size-1)
        ))

    start = (0,0)
    end = (size-1,size-1)

    return GeneratedLevel(
        grid,
        start,
        end,
        enemies,
        obstacles
    )


# =========================
# DRAW LEVEL
# =========================
def draw_level(screen, level, font):

    screen.fill(BLACK)

    # obstacles
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            if level.grid[x][y] == 1:

                pygame.draw.rect(
                    screen,
                    GRAY,
                    (
                        y * CELL_SIZE,
                        x * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE
                    )
                )

    # path
    for (x,y) in level.path:

        pygame.draw.rect(
            screen,
            YELLOW,
            (
                y * CELL_SIZE,
                x * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
        )

    # enemies
    for (x,y) in level.enemies:

        pygame.draw.rect(
            screen,
            RED,
            (
                y * CELL_SIZE,
                x * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
        )

    # start/end
    sx, sy = level.start
    ex, ey = level.end

    pygame.draw.rect(
        screen,
        GREEN,
        (
            sy * CELL_SIZE,
            sx * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
    )

    pygame.draw.rect(
        screen,
        BLUE,
        (
            ey * CELL_SIZE,
            ex * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
    )

    # grid lines
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            pygame.draw.rect(
                screen,
                BLACK,
                (
                    y * CELL_SIZE,
                    x * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                ),
                1
            )

    text = font.render(
        f"Fitness: {level.fitness_score:.2f}",
        True,
        WHITE
    )

    screen.blit(text, (10,10))


# =========================
# DRAW HISTOGRAM
# =========================
def draw_histogram(screen,
                   values,
                   title,
                   font):

    graph_y = WINDOW_SIZE + 10

    bins = len(values)

    if bins == 0:
        return

    max_value = max(values)

    if max_value == 0:
        max_value = 1

    bar_width = WINDOW_SIZE / bins

    for i, value in enumerate(values):

        normalized = value / max_value

        bar_height = normalized * (
            GRAPH_HEIGHT - 40
        )

        x = i * bar_width

        y = graph_y + (
            GRAPH_HEIGHT - bar_height
        )

        pygame.draw.rect(
            screen,
            CYAN,
            (
                x,
                y,
                bar_width - 2,
                bar_height
            )
        )

    label = font.render(
        title,
        True,
        WHITE
    )

    screen.blit(label, (10, WINDOW_SIZE + 5))


# =========================
# MAIN
# =========================

def main():

    pygame.init()

    screen = pygame.display.set_mode(
        (WINDOW_SIZE, TOTAL_HEIGHT)
    )

    pygame.display.set_caption(
        "PCG Histograms"
    )

    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)

    pipeline = PCGPipeline([
        PlayabilityEvaluator(),
        HeuristicEvaluator(),
        DifficultyEvaluator()
    ])

    current_level = None
    generating = True
    attempts = 0

    current_graph = 0
    last_printed_graph = -1
    while True:

        clock.tick(30)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:

                    generating = True
                    current_level = None
                    attempts = 0
                    last_printed_graph = -1
                if event.key == pygame.K_1:
                    current_graph = 0

                if event.key == pygame.K_2:
                    current_graph = 1

                if event.key == pygame.K_3:
                    current_graph = 2

                if event.key == pygame.K_4:
                    current_graph = 3

                if event.key == pygame.K_5:
                    current_graph = 4

                if event.key == pygame.K_6:
                    current_graph = 5

        if generating:

            attempts += 1

            lvl = generate_level()

            if pipeline.evaluate(lvl):

                current_level = lvl
                generating = False

                print(
                    f"Found level "
                    f"{lvl.fitness_score:.2f} "
                    f"in {attempts} attempts"
                )

        if current_level:

            draw_level(
                screen,
                current_level,
                font
            )

            # =========================
            # BUILD HISTOGRAMS
            # =========================

            density_hist = density_histogram(
                local_obstacle_density(
                    current_level.grid
                )
            )

            connectivity_hist = (
                connectivity_histogram(
                    current_level.grid
                )
            )

            corridor_hist = (
                corridor_width_histogram(
                    current_level.grid
                )
            )

            visibility_hist = (
                visibility_histogram(
                    current_level.grid
                )
            )

            curvature_hist = (
                path_curvature_histogram(
                    current_level.path
                )
            )

            pressure_hist = density_histogram(
                enemy_pressure_histogram(
                    current_level.grid,
                    current_level.enemies
                )
            )

            graphs = [
                density_hist,
                connectivity_hist,
                corridor_hist,
                visibility_hist,
                curvature_hist,
                pressure_hist
            ]

            graph_names = [
                "1 Obstacle Density - nearby obstacle concentration",
                "2 Connectivity - How fragmented is the map?",
                "3 Corridor Width - How narrow are movement spaces?",
                "4 Visibility - How far can you see in each direction?",
                "5 Path Curvature - How often does the optimal path turn?",
                "6 Enemy Pressure - How much of the map lies near enemies?"
            ]

            draw_histogram(
                screen,
                graphs[current_graph],
                graph_names[current_graph],
                font
            )
            # =========================
            # PRINT HISTOGRAMS
            # =========================
            if current_graph != last_printed_graph:

                name = graph_names[current_graph]
                hist = graphs[current_graph]

                print(f"\n[{name}]")
                print(hist)

                last_printed_graph = current_graph


            pygame.display.flip()


if __name__ == "__main__":
    main()