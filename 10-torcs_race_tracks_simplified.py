import pygame
import random
import math
import sys
# -----------------------------
# The program uses a genetic algorithm approach to  
# generate and  evolve race tracks, allowing the user to interactively select and evolve tracks over multiple generations.  
# The Track class represents a race track defined by a set of control points, 
# and includes methods for generating random tracks, computing tangents, and drawing the track on the screen.
#
# The crossover function creates a child track by combining control points from two parent tracks, 
# while the mutate function introduces random variations to a track's control points.  
#
# The evolve function manages the selection and reproduction process, creating a new population of tracks based on selected parents. 
#
# The main loop handles user input for selecting tracks and evolving the population, and renders the tracks in a grid layout on the screen.  
#  
# The draw_track function renders a track within a specified rectangular area on the screen, 
# scaling and translating the track's points to fit within the rectangle.
# -----------------------------
# CONFIG
# -----------------------------
WIDTH, HEIGHT = 800, 600
POP_SIZE = 6
NUM_POINTS = 8
MUTATION_RATE = 0.2
TENSION = 0.3  # controls curve smoothness

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# -----------------------------
# BEZIER UTIL
# -----------------------------
def cubic_bezier(p0, p1, p2, p3, steps=20):
    points = []
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
        points.append((x, y))
    return points

# -----------------------------
# TRACK CLASS
# -----------------------------
TRACK_WIDTH = 40

class Track:
    def __init__(self, points=None):
        if points:
            self.points = points
        else:
            self.points = self.random_points()
        self.fitness = 0
    #This function builds a random closed track shape, 
    #but in a controlled circular structure rather than fully chaotic randomness.
    #2π = full circle (360°)
    #dividing by NUM_POINTS spreads points evenly
    #multiplying by i places each point at a different angle
    def random_points(self):
        pts = []
        for i in range(NUM_POINTS):
            angle = (2 * math.pi / NUM_POINTS) * i
            radius = random.randint(120, 250) #Random radius per point to create variation in track shape
            #Convert polar to Cartesian coordinates, centering around the middle of the screen
            x = WIDTH//2 + radius * math.cos(angle)
            y = HEIGHT//2 + radius * math.sin(angle)
            pts.append((x, y))
        return pts
    #computes smoothed direction vectors at each track point by averaging the previous and next points, 
    #then scales them by TENSION to control curve smoothness.
    #This is done by computing tangents for each control point, which are used to create smooth curves between points when drawing the track.
    #The tangents are calculated based on the positions of the previous and next control points, and then scaled by a tension factor to control the curvature of the track.
    #REturns [(tx1, ty1), (tx2, ty2), ..., (txn, tyn)]
    def compute_tangents(self):
        tangents = []
        n = len(self.points)
        for i in range(n):
            p_prev = self.points[i-1]
            p_next = self.points[(i+1) % n]

            dx = (p_next[0] - p_prev[0]) * TENSION
            dy = (p_next[1] - p_prev[1]) * TENSION
            tangents.append((dx, dy))
        return tangents

    def get_smooth_path(self):
        tangents = self.compute_tangents()
        path = []

        n = len(self.points)
        for i in range(n):
            p0 = self.points[i]
            p1 = (p0[0] + tangents[i][0], p0[1] + tangents[i][1])

            j = (i + 1) % n
            p3 = self.points[j]
            p2 = (p3[0] - tangents[j][0], p3[1] - tangents[j][1])

            curve = cubic_bezier(p0, p1, p2, p3)
            path.extend(curve)

        return path

    def compute_road_edges(self, path):
        left_edge = []
        right_edge = []

        for i in range(len(path)):
            p = path[i]
            p_next = path[(i + 1) % len(path)]

            # tangent
            dx = p_next[0] - p[0]
            dy = p_next[1] - p[1]

            length = math.hypot(dx, dy)
            if length == 0:
                continue

            # normalize tangent
            dx /= length
            dy /= length

            # normal (perpendicular)
            nx = -dy
            ny = dx

            offset = TRACK_WIDTH / 2

            left = (p[0] + nx * offset, p[1] + ny * offset)
            right = (p[0] - nx * offset, p[1] - ny * offset)

            left_edge.append(left)
            right_edge.append(right)

        return left_edge, right_edge

    def draw(self, surface):
        path = self.get_smooth_path()
        left, right = self.compute_road_edges(path)

        if len(left) < 2:
            return

        # build polygon (left side forward, right side reversed)
        road_polygon = left + right[::-1]

        # draw road
        pygame.draw.polygon(surface, (80, 80, 80), road_polygon)

        # draw borders
        pygame.draw.lines(surface, (255,255,255), True, left, 2)
        pygame.draw.lines(surface, (255,255,255), True, right, 2)

# -----------------------------
# GENETIC OPERATORS
# -----------------------------
def crossover(parent1, parent2):
    cut = random.randint(1, NUM_POINTS-1)
    child_points = parent1.points[:cut] + parent2.points[cut:]
    return Track(child_points)

def mutate(track):
    new_points = []
    for (x, y) in track.points:
        if random.random() < MUTATION_RATE:
            x += random.randint(-40, 40)
            y += random.randint(-40, 40)
        new_points.append((x, y))
    return Track(new_points)

def evolve(population):
    population.sort(key=lambda t: t.fitness, reverse=True)

    survivors = population[:POP_SIZE//2]
    new_pop = survivors.copy()

    while len(new_pop) < POP_SIZE:
        p1, p2 = random.sample(survivors, 2)
        child = crossover(p1, p2)
        child = mutate(child)
        new_pop.append(child)

    return new_pop

# -----------------------------
# INITIALIZE
# -----------------------------
population = [Track() for _ in range(POP_SIZE)]
current_index = 0
generation = 1

GRID_COLS = 3
GRID_ROWS = 2
MARGIN = 20

def draw_population(surface, population, selected):
    cell_w = (WIDTH - (GRID_COLS + 1)*MARGIN) // GRID_COLS
    cell_h = (HEIGHT - (GRID_ROWS + 1)*MARGIN) // GRID_ROWS

    rects = []

    for i, track in enumerate(population):
        row = i // GRID_COLS
        col = i % GRID_COLS

        x = MARGIN + col * (cell_w + MARGIN)
        y = MARGIN + row * (cell_h + MARGIN)

        rect = pygame.Rect(x, y, cell_w, cell_h)
        rects.append(rect)

        # draw background
        pygame.draw.rect(surface, (50,50,50), rect)

        # highlight if selected
        if i in selected:
            pygame.draw.rect(surface, (0,200,0), rect, 4)
        else:
            pygame.draw.rect(surface, (100,100,100), rect, 2)

        # draw track inside cell (scaled)
        draw_track_in_rect(surface, track, rect)

    return rects


def draw_track_in_rect(surface, track, rect):
    path = track.get_smooth_path()
    left, right = track.compute_road_edges(path)

    if len(left) < 2:
        return

    # scale + translate into rect
    all_pts = left + right
    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)

    scale_x = (rect.width - 20) / (max_x - min_x + 1e-5)
    scale_y = (rect.height - 20) / (max_y - min_y + 1e-5)
    scale = min(scale_x, scale_y)

    def transform(p):
        x = (p[0] - min_x) * scale + rect.x + 10
        y = (p[1] - min_y) * scale + rect.y + 10
        return (x, y)

    left_t = [transform(p) for p in left]
    right_t = [transform(p) for p in right]

    polygon = left_t + right_t[::-1]

    pygame.draw.polygon(surface, (180,180,80), polygon)
    pygame.draw.lines(surface, (155,255,255), True, left_t, 2)
    pygame.draw.lines(surface, (155,255,155), True, right_t, 2)


def evolve_from_selection(population, selected_indices):
    if len(selected_indices) < 2:
        return population  # not enough parents

    parents = [population[i] for i in selected_indices]

    new_pop = []

    # keep parents
    for p in parents:
        new_pop.append(p)

    # generate rest
    while len(new_pop) < POP_SIZE:
        p1, p2 = random.sample(parents, 2)
        child = crossover(p1, p2)
        child = mutate(child)
        new_pop.append(child)

    return new_pop


# -----------------------------
# MAIN LOOP (REPLACE OLD ONE)
# -----------------------------
population = [Track() for _ in range(POP_SIZE)]
selected = set()
generation = 1

running = True
while running:
    screen.fill((30,30,30))

    rects = draw_population(screen, population, selected)

    text = font.render(f"Gen: {generation} | Click tracks to select | ENTER = evolve", True, (255,255,255))
    screen.blit(text, (10, HEIGHT - 30))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for i, rect in enumerate(rects):
                if rect.collidepoint(mx, my):
                    if i in selected:
                        selected.remove(i)
                    else:
                        selected.add(i)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                population = evolve_from_selection(population, selected)
                selected.clear()
                generation += 1

    clock.tick(60)

pygame.quit()
sys.exit()