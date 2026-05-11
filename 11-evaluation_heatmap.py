import pygame
import random
import heapq

# =========================
# CONFIG
# =========================
GRID_SIZE = 20
CELL_SIZE = 25

WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE

TOTAL_WIDTH = WIDTH * 2

BLACK = (20,20,20)
WHITE = (255,255,255)

GRAY = (120,120,120)

RED = (220,60,60)
GREEN = (60,220,120)
BLUE = (80,120,255)

YELLOW = (240,220,80)

# =========================
# LEVEL
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

        self.path = []

# =========================
# A*
# =========================
def astar(grid, start, end):

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

    return []

# =========================
# LEVEL GENERATION
# =========================
def generate_level():

    grid = [
        [0 for _ in range(GRID_SIZE)]
        for _ in range(GRID_SIZE)
    ]

    obstacles = []

    for _ in range(60):

        x = random.randint(0, GRID_SIZE-1)
        y = random.randint(0, GRID_SIZE-1)

        grid[x][y] = 1

        obstacles.append((x,y))

    enemies = []

    for _ in range(10):

        enemies.append((
            random.randint(0, GRID_SIZE-1),
            random.randint(0, GRID_SIZE-1)
        ))

    start = (0,0)
    end = (GRID_SIZE-1, GRID_SIZE-1)

    return GeneratedLevel(
        grid,
        start,
        end,
        enemies,
        obstacles
    )

# =========================================================
# HEATMAP FIELDS
# =========================================================

# =========================
# 1 DENSITY
# =========================
def field_density(grid):

    rows = len(grid)
    cols = len(grid[0])

    field = [
        [0 for _ in range(cols)]
        for _ in range(rows)
    ]

    for x in range(rows):
        for y in range(cols):

            obstacle_count = 0
            total = 0

            for dx in range(-2, 3):
                for dy in range(-2, 3):

                    nx = x + dx
                    ny = y + dy

                    if 0 <= nx < rows and 0 <= ny < cols:

                        total += 1

                        if grid[nx][ny] == 1:
                            obstacle_count += 1

            field[x][y] = obstacle_count / total

    return field

# =========================
# 2 CLEARANCE
# =========================
def field_clearance(grid):

    rows = len(grid)
    cols = len(grid[0])

    field = [
        [0 for _ in range(cols)]
        for _ in range(rows)
    ]

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            best = 999

            for ox in range(rows):
                for oy in range(cols):

                    if grid[ox][oy] == 1:

                        d = abs(x - ox) + abs(y - oy)

                        best = min(best, d)

            field[x][y] = best

    return field

# =========================
# 3 VISIBILITY
# =========================
def field_visibility(grid):

    rows = len(grid)
    cols = len(grid[0])

    field = [
        [0 for _ in range(cols)]
        for _ in range(rows)
    ]

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

            field[x][y] = visible

    return field

# =========================
# 4 ENEMY PRESSURE
# =========================
def field_pressure(grid, enemies):

    rows = len(grid)
    cols = len(grid[0])

    field = [
        [0 for _ in range(cols)]
        for _ in range(rows)
    ]

    for x in range(rows):
        for y in range(cols):

            if grid[x][y] == 1:
                continue

            pressure = 0

            for ex, ey in enemies:

                d = abs(x - ex) + abs(y - ey)

                if d == 0:
                    pressure += 1
                else:
                    pressure += 1 / d

            field[x][y] = pressure

    return field

# =========================================================
# HEATMAP COLOR
# =========================================================
def heat_color(v):

    v = max(0.0, min(1.0, v))

    # BLUE -> CYAN
    if v < 0.25:

        t = v / 0.25

        r = 0
        g = int(255 * t)
        b = 255

    # CYAN -> GREEN
    elif v < 0.5:

        t = (v - 0.25) / 0.25

        r = 0
        g = 255
        b = int(255 * (1 - t))

    # GREEN -> YELLOW
    elif v < 0.75:

        t = (v - 0.5) / 0.25

        r = int(255 * t)
        g = 255
        b = 0

    # YELLOW -> RED
    else:

        t = (v - 0.75) / 0.25

        r = 255
        g = int(255 * (1 - t))
        b = 0

    return (r,g,b)

# =========================================================
# DRAW MAP
# =========================================================
def draw_map(screen, level):

    offset_x = 0

    # background
    pygame.draw.rect(
        screen,
        BLACK,
        (0,0,WIDTH,HEIGHT)
    )

    # obstacles
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            if level.grid[x][y] == 1:

                pygame.draw.rect(
                    screen,
                    GRAY,
                    (
                        offset_x + y * CELL_SIZE,
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
                offset_x + y * CELL_SIZE,
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
                offset_x + y * CELL_SIZE,
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
            offset_x + sy * CELL_SIZE,
            sx * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
    )

    pygame.draw.rect(
        screen,
        BLUE,
        (
            offset_x + ey * CELL_SIZE,
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
                (40,40,40),
                (
                    offset_x + y * CELL_SIZE,
                    x * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                ),
                1
            )

# =========================================================
# DRAW HEATMAP
# =========================================================
def draw_heatmap(screen,
                 field,
                 title,
                 font):

    offset_x = WIDTH

    rows = len(field)
    cols = len(field[0])

    maxv = max(max(r) for r in field)
    minv = min(min(r) for r in field)

    if maxv == minv:
        maxv += 1

    # background
    pygame.draw.rect(
        screen,
        BLACK,
        (offset_x,0,WIDTH,HEIGHT)
    )

    # =========================
    # DRAW FIELD
    # =========================
    for x in range(rows):
        for y in range(cols):

            raw = field[x][y]

            v = (
                (raw - minv) /
                (maxv - minv)
            )

            color = heat_color(v)

            pygame.draw.rect(
                screen,
                color,
                (
                    offset_x + y * CELL_SIZE,
                    x * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
            )

    # =========================
    # GRID
    # =========================
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            pygame.draw.rect(
                screen,
                (40,40,40),
                (
                    offset_x + y * CELL_SIZE,
                    x * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                ),
                1
            )

    # =========================
    # TITLE
    # =========================
    text = font.render(
        title,
        True,
        WHITE
    )

    screen.blit(
        text,
        (offset_x + 10, 10)
    )

    # =========================
    # VALUE RANGE
    # =========================
    range_text = font.render(
        f"min={minv:.2f} max={maxv:.2f}",
        True,
        WHITE
    )

    screen.blit(
        range_text,
        (offset_x + 10, 35)
    )

    # =========================
    # SCALE BAR
    # =========================
    scale_x = offset_x + 10
    scale_y = HEIGHT - 40

    scale_w = 220
    scale_h = 20

    for i in range(scale_w):

        v = i / scale_w

        pygame.draw.rect(
            screen,
            heat_color(v),
            (
                scale_x + i,
                scale_y,
                1,
                scale_h
            )
        )

    pygame.draw.rect(
        screen,
        WHITE,
        (
            scale_x,
            scale_y,
            scale_w,
            scale_h
        ),
        1
    )

    low_text = font.render(
        "LOW",
        True,
        WHITE
    )

    high_text = font.render(
        "HIGH",
        True,
        WHITE
    )

    screen.blit(
        low_text,
        (scale_x, scale_y - 20)
    )

    screen.blit(
        high_text,
        (scale_x + scale_w - 45, scale_y - 20)
    )

# =========================================================
# MAIN
# =========================================================
def main():

    pygame.init()

    screen = pygame.display.set_mode(
        (TOTAL_WIDTH, HEIGHT)
    )

    pygame.display.set_caption(
        "PCG Spatial Heatmaps"
    )

    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)

    level = generate_level()

    level.path = astar(
        level.grid,
        level.start,
        level.end
    )

    current_view = 0

    metric_names = [
        "1 Density",
        "2 Clearance",
        "3 Visibility",
        "4 Enemy Pressure"
    ]

    running = True

    while running:

        clock.tick(30)

        # =========================
        # EVENTS
        # =========================
        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:

                    level = generate_level()

                    level.path = astar(
                        level.grid,
                        level.start,
                        level.end
                    )

                if event.key == pygame.K_1:
                    current_view = 0

                if event.key == pygame.K_2:
                    current_view = 1

                if event.key == pygame.K_3:
                    current_view = 2

                if event.key == pygame.K_4:
                    current_view = 3

        # =========================
        # BUILD HEATMAPS
        # =========================
        heatmaps = [

            field_density(level.grid),

            field_clearance(level.grid),

            field_visibility(level.grid),

            field_pressure(
                level.grid,
                level.enemies
            )
        ]

        # =========================
        # DRAW
        # =========================
        screen.fill(BLACK)

        draw_map(
            screen,
            level
        )

        draw_heatmap(
            screen,
            heatmaps[current_view],
            metric_names[current_view],
            font
        )

        # =========================
        # CONTROLS
        # =========================
        controls = font.render(
            "SPACE regenerate | 1 Density | 2 Clearance | 3 Visibility | 4 Pressure",
            True,
            WHITE
        )

        screen.blit(
            controls,
            (10, HEIGHT - 25)
        )

        pygame.display.flip()

    pygame.quit()

# =========================================================
# START
# =========================================================
if __name__ == "__main__":
    main()