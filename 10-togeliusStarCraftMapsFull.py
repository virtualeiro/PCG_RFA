import pygame
import random
import math
import heapq
import sys
#-------------------------------------------------------
#SMS-EMOA-style evolutionary loop on top of the map representation, with:
#Genotype to map decoding (bases, resources, walls via turtle walk)
#Playability check via A* reachability
#Key fitnesses close to the paper:
#fb0 - base space
#fb1 - base distance
#fr4 - resource fairness
#Constraints on fb0 and fb1
#SMS-EMO-like selection with 2D hypervolume contribution
#Pygame viewer to watch the current best map evolve
#-------------------------------------------------------
# =========================
# CONFIG
# =========================

GRID_SIZE = 64
CELL_SIZE = 10
SCREEN_SIZE = GRID_SIZE * CELL_SIZE

N_BASES = 3
N_MINERALS = 8
N_GAS = 4
N_WALLS = 6
WALL_MAX_STEPS = 400

POP_SIZE = 20
MAX_EVALS = 5000  # reduce if too slow
CROSSOVER_PROB = 0.9
MUTATION_PROB = 0.2
ETA_C = 15.0  # SBX
ETA_M = 20.0  # polynomial mutation

# We will optimize 2 objectives: fb1 (base distance) and fr4 (resource fairness)
N_OBJECTIVES = 2

# Colors
COLOR_BG = (10, 10, 20)
COLOR_PASSABLE = (30, 30, 40)
COLOR_WALL = (40, 40, 120)
COLOR_BASE = (0, 200, 0)
COLOR_MINERAL = (0, 180, 255)
COLOR_GAS = (255, 200, 0)
COLOR_GRID = (50, 50, 70)

# =========================
# GENOTYPE
# =========================

def genotype_length():
    # bases: 2 floats each (r, theta)
    # minerals: 2 floats each (x, y)
    # gas: 2 floats each (x, y)
    # walls: 5 floats each (x, y, p_left, p_right, p_gap)
    return (N_BASES * 2) + (N_MINERALS * 2) + (N_GAS * 2) + (N_WALLS * 5)

def random_genotype():
    return [random.random() for _ in range(genotype_length())]

def decode_genotype(gen):
    idx = 0

    # Bases: polar coords (r, theta) around center
    bases = []
    for _ in range(N_BASES):
        r = 0.25 + 0.25 * gen[idx]; idx += 1   # radius fraction
        theta = 2 * math.pi * gen[idx]; idx += 1
        cx = GRID_SIZE / 2
        cy = GRID_SIZE / 2
        x = int(cx + r * GRID_SIZE * math.cos(theta))
        y = int(cy + r * GRID_SIZE * math.sin(theta))
        x = max(0, min(GRID_SIZE - 1, x))
        y = max(0, min(GRID_SIZE - 1, y))
        bases.append((x, y))

    # Minerals
    minerals = []
    for _ in range(N_MINERALS):
        x = int(gen[idx] * GRID_SIZE); idx += 1
        y = int(gen[idx] * GRID_SIZE); idx += 1
        x = max(0, min(GRID_SIZE - 1, x))
        y = max(0, min(GRID_SIZE - 1, y))
        minerals.append((x, y))

    # Gas
    gas = []
    for _ in range(N_GAS):
        x = int(gen[idx] * GRID_SIZE); idx += 1
        y = int(gen[idx] * GRID_SIZE); idx += 1
        x = max(0, min(GRID_SIZE - 1, x))
        y = max(0, min(GRID_SIZE - 1, y))
        gas.append((x, y))

    # Walls: start x,y + probs (left, right, gap)
    walls = []
    for _ in range(N_WALLS):
        x = int(gen[idx] * GRID_SIZE); idx += 1
        y = int(gen[idx] * GRID_SIZE); idx += 1
        p_left = gen[idx]; idx += 1
        p_right = gen[idx]; idx += 1
        p_gap = gen[idx]; idx += 1
        walls.append((x, y, p_left, p_right, p_gap))

    return bases, minerals, gas, walls

# =========================
# MAP GENERATION
# =========================

def in_bounds(x, y):
    return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

def draw_wall(grid, start_x, start_y, p_left, p_right, p_gap):
    x, y = start_x, start_y
    if not in_bounds(x, y):
        return
    grid[y][x] = 1  # wall
    angle = 0.0  # pointing right

    for _ in range(WALL_MAX_STEPS):
        r = random.random()
        branch = None
        if r < p_left:
            angle -= math.pi / 4
            branch = "left"
        elif r < p_left + p_right:
            angle += math.pi / 4
            branch = "right"
        elif r < p_left + p_right + p_gap:
            branch = "gap"
        else:
            branch = "paint"

        dx = int(round(math.cos(angle)))
        dy = int(round(math.sin(angle)))
        nx, ny = x + dx, y + dy
        if not in_bounds(nx, ny):
            break
        x, y = nx, ny

        if branch == "gap":
            continue
        if grid[y][x] == 1:
            break
        grid[y][x] = 1

def generate_map_from_genotype(gen):
    bases, minerals, gas, walls = decode_genotype(gen)
    grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for (x, y, p_left, p_right, p_gap) in walls:
        draw_wall(grid, x, y, p_left, p_right, p_gap)
    return grid, bases, minerals, gas

# =========================
# PATHFINDING (A*)
# =========================
def neighbors(x, y):
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            yield nx, ny

def astar(grid, start, goal):
    (sx, sy) = start
    (gx, gy) = goal
    if grid[sy][sx] == 1 or grid[gy][gx] == 1:
        return None

    open_set = []
    heapq.heappush(open_set, (0, (sx, sy)))
    came_from = {}
    g_score = { (sx, sy): 0 }

    def h(x, y):
        return abs(x - gx) + abs(y - gy)

    while open_set:
        _, (x, y) = heapq.heappop(open_set)
        if (x, y) == (gx, gy):
            return g_score[(x, y)]
        for nx, ny in neighbors(x, y):
            if grid[ny][nx] == 1:
                continue
            tentative = g_score[(x, y)] + 1
            if (nx, ny) not in g_score or tentative < g_score[(nx, ny)]:
                g_score[(nx, ny)] = tentative
                f = tentative + h(nx, ny)
                heapq.heappush(open_set, (f, (nx, ny)))
                came_from[(nx, ny)] = (x, y)
    return None

# =========================
# FITNESS FUNCTIONS
# =========================
# For each wall, we do a random walk starting from (x,y) with the given probabilities.
#   At each step, we pick a random number r in [0,1):
#     If r < p_left: turn left
#     Else if r < p_left + p_right: turn right
#     Else: continue straight
#   Then we step forward. If we are in bounds and not already a wall, we set that cell to be a wall.
#   We repeat for a fixed number of steps or until we hit an existing wall or go out of bounds.
#   This creates a "turtle graphics"-style wall that can be more organic than just rectangles.
# The probabilities allow for different styles of walls: more straight, more zig-zag, more gaps, etc.
#   This is a simple way to create interesting wall patterns from a compact genotype.
# The walls are drawn on an initially empty grid, and then we evaluate the map based on reachability and the fitness functions.
#   
# The fitness functions are:
#   fb0: base space - fraction of passable cells in a 5x5 neighborhood around each base that are reachable within 5 steps
#   fb1: base distance - minimum distance between any two bases, normalized by max possible
#  fr4: resource fairness - for each base, compute distance to nearest mineral and nearest gas; then compute fairness = 1 - (max - min)/max_possible
# Constraints:
#   fb0 >= 0.5, fb1 >= 0.5
# Objectives: maximize fb1 and fr4
#   The evaluation function returns a dictionary with all this information, which is used for selection in the evolutionary loop.
#   The reachability check ensures that all bases, minerals, and gas are mutually reachable, which is a basic playability requirement for the map.
#------------------------------------------------------------------------------------------------------------               
def reachable_all(grid, bases, minerals, gas):
    points = bases + minerals + gas
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            d = astar(grid, points[i], points[j])
            if d is None:
                return False
    return True

def base_space(grid, bases):
    # fb0: fraction of passable cells in 5x5 neighborhood reachable within 5 steps
    total = 0
    count = 0
    for (bx, by) in bases:
        local_passable = 0
        local_total = 0
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x, y = bx + dx, by + dy
                if not in_bounds(x, y):
                    continue
                local_total += 1
                if grid[y][x] == 1:
                    continue
                d = astar(grid, (bx, by), (x, y))
                if d is not None and d <= 5:
                    local_passable += 1
        if local_total > 0:
            total += local_passable / local_total
            count += 1
    return total / count if count > 0 else 0.0

def base_distance(grid, bases):
    # fb1: min base-to-base distance normalized
    dists = []
    for i in range(len(bases)):
        for j in range(i+1, len(bases)):
            d = astar(grid, bases[i], bases[j])
            if d is None:
                return 0.0
            dists.append(d)
    if not dists:
        return 0.0
    min_d = min(dists)
    max_possible = GRID_SIZE * 2
    return min_d / max_possible

def resource_fairness(grid, bases, minerals, gas):
    # fr4: fairness of distance to nearest resource of each type
    # For each base, compute distance to nearest mineral and nearest gas
    # Then fairness = 1 - (max - min)/max_possible
    def nearest_dist(base, resources):
        bx, by = base
        best = None
        for (rx, ry) in resources:
            d = astar(grid, (bx, by), (rx, ry))
            if d is None:
                continue
            if best is None or d < best:
                best = d
        return best

    all_dists = []
    for b in bases:
        dm = nearest_dist(b, minerals)
        dg = nearest_dist(b, gas)
        if dm is not None:
            all_dists.append(dm)
        if dg is not None:
            all_dists.append(dg)

    if not all_dists:
        return 0.0

    d_min = min(all_dists)
    d_max = max(all_dists)
    max_possible = GRID_SIZE * 2
    return 1.0 - (d_max - d_min) / max_possible
#--------------------------------
# The evaluation function combines all the above: it generates the map from the genotype, checks reachability, computes fitnesses, applies constraints, and returns a dictionary with all this information for use in selection.
# The genotype is a list of random floats that encode the positions of bases, minerals, gas, and walls. The map is generated by decoding this genotype
#   
# The evaluation function returns a dictionary with keys:
#   "feasible": whether the map meets the constraints
#   "penalty": how much it violates the constraints (0 if feasible)
#   "fb0": base space fitness
#   "fb1": base distance fitness
#   "fr4": resource fairness fitness
#   "objectives": list of objective values (fb1, fr4)
#   "grid": the generated grid
#   "bases": list of base positions
#   "minerals": list of mineral positions
#   "gas": list of gas positions
# This information is used in the evolutionary loop to select and evolve the population of maps.
# The reachability check ensures that the map is playable, while the fitness functions guide the evolution towards maps with good base placement and resource distribution.
# The constraints ensure that we only consider maps that have a reasonable amount of space around bases and sufficient distance between bases, which are important for gameplay.
# The objectives allow us to optimize for both base distance and resource fairness, which can lead to interesting trade-offs in the evolved maps.
# The evolutionary operators (crossover and mutation) modify the genotype, which in turn modifies the generated map. The selection process uses non-dominated sorting and hypervolume contribution to maintain a diverse set of high-quality maps in the population.
# The Pygame visualization allows us to see the best map evolve over time, which can
# be very insightful for understanding how the evolutionary process is shaping the maps and what kinds of features are being favored by the fitness functions and constraints.
#------------------------------------------------------------------------------------------------------------
def evaluate_individual(gen):
    grid, bases, minerals, gas = generate_map_from_genotype(gen)

    # Sanity: reachability
    if not reachable_all(grid, bases, minerals, gas):
        return {
            "feasible": False,
            "penalty": 9999.0,
            "fb0": 0.0,
            "fb1": 0.0,
            "fr4": 0.0,
            "objectives": [0.0, 0.0],
            "grid": grid,
            "bases": bases,
            "minerals": minerals,
            "gas": gas
        }

    fb0 = base_space(grid, bases)
    fb1 = base_distance(grid, bases)
    fr4 = resource_fairness(grid, bases, minerals, gas)

    # Constraints:
    # fb0 >= 0.5, fb1 >= 0.5
    feasible = True
    penalty = 0.0
    if fb0 < 0.5:
        feasible = False
        penalty += (0.5 - fb0)
    if fb1 < 0.5:
        feasible = False
        penalty += (0.5 - fb1)

    # Objectives: maximize fb1 and fr4
    obj1 = fb1
    obj2 = fr4

    return {
        "feasible": feasible,
        "penalty": penalty,
        "fb0": fb0,
        "fb1": fb1,
        "fr4": fr4,
        "objectives": [obj1, obj2],
        "grid": grid,
        "bases": bases,
        "minerals": minerals,
        "gas": gas
    }

# =========================
# EVOLUTIONARY OPERATORS
# =========================
# We use Simulated Binary Crossover (SBX) and Polynomial Mutation, 
# which are common in real-valued evolutionary algorithms. 
# The crossover takes two parent genotypes and produces two offspring genotypes 
# by combining the values with a certain distribution. 
# The mutation randomly perturbs some values in the genotype with a certain probability.
# The selection process is based on non-dominated sorting and hypervolume contribution, 
# which are standard techniques in multi-objective evolutionary algorithms like SMS-EMOA. 
# We generate one offspring per iteration, evaluate it, and then combine it with the current population.
#  We then remove one individual from the combined population based on feasibility and hypervolume contribution 
# to maintain a constant population size.
# The evolutionary loop continues until we reach the maximum number of evaluations, 
# and we keep track of the best feasible solution found during the process. 
# The Pygame visualization allows us to see the best map evolve in real-time, 
# which can be very informative for understanding the dynamics of the evolution 
# and the kinds of maps that are being favored by the fitness functions and constraints.
#------------------------------------------------------------------------------------------------------------
def sbx_crossover(p1, p2, eta_c=ETA_C):
    if random.random() > CROSSOVER_PROB:
        return p1[:], p2[:]
    c1 = p1[:]
    c2 = p2[:]
    for i in range(len(p1)):
        u = random.random()
        if u <= 0.5:
            beta = (2*u)**(1.0/(eta_c+1))
        else:
            beta = (1/(2*(1-u)))**(1.0/(eta_c+1))
        x1 = p1[i]
        x2 = p2[i]
        c1[i] = 0.5*((1+beta)*x1 + (1-beta)*x2)
        c2[i] = 0.5*((1-beta)*x1 + (1+beta)*x2)
        c1[i] = min(1.0, max(0.0, c1[i]))
        c2[i] = min(1.0, max(0.0, c2[i]))
    return c1, c2

def polynomial_mutation(ind, eta_m=ETA_M):
    for i in range(len(ind)):
        if random.random() < MUTATION_PROB:
            x = ind[i]
            u = random.random()
            if u < 0.5:
                delta = (2*u)**(1.0/(eta_m+1)) - 1
            else:
                delta = 1 - (2*(1-u))**(1.0/(eta_m+1))
            x = x + delta
            x = min(1.0, max(0.0, x))
            ind[i] = x

def dominates(a, b):
    # a dominates b if a is at least as good in all objectives and better in at least one
    better_or_equal = True
    strictly_better = False
    for i in range(N_OBJECTIVES):
        if a["objectives"][i] < b["objectives"][i]:
            better_or_equal = False
            break
        if a["objectives"][i] > b["objectives"][i]:
            strictly_better = True
    return better_or_equal and strictly_better

def non_dominated_sort(pop):
    fronts = []
    S = {}
    n = {}
    rank = {}

    for p in range(len(pop)):
        S[p] = []
        n[p] = 0
        for q in range(len(pop)):
            if dominates(pop[p], pop[q]):
                S[p].append(q)
            elif dominates(pop[q], pop[p]):
                n[p] += 1
        if n[p] == 0:
            rank[p] = 0
    front = [p for p in range(len(pop)) if n[p] == 0]
    fronts.append(front)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    rank[q] = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    return fronts[:-1], rank
# The non-dominated sorting function organizes the population into different fronts based on dominance.
# The first front contains all non-dominated individuals, the second front contains individuals dominated only by those in the first front, and so on. This is used in the selection process to maintain a diverse set of high-quality solutions across the Pareto front.
# The hypervolume contribution function calculates how much each individual contributes to the overall hypervolume of the population, which is a measure of the quality of the solutions in multi-objective optimization. In SMS-EMOA, we use this to decide which individual to remove when we add a new offspring to the population.
#  The evolutionary loop (sms_emoa_step) generates one offspring, evaluates it, and then combines it with the current population. It then removes one individual based on feasibility and hypervolume contribution to maintain a constant population size. This process continues until we reach the maximum number of evaluations.
def hypervolume_2d(points, ref=(0.0, 0.0)):
    # points: list of (f1, f2), maximization
    # simple 2D hypervolume assuming ref is dominated by all points
    # sort by f1 ascending
    pts = sorted(points, key=lambda x: x[0])
    hv = 0.0
    prev_f1 = ref[0]
    prev_f2 = ref[1]
    for f1, f2 in pts:
        width = f1 - prev_f1
        height = max(0.0, f2 - ref[1])
        hv += width * height
        prev_f1 = f1
    return hv

def hypervolume_contributions(pop):
    # compute HV contribution for each individual in pop (2D)
    # reference point slightly below 0
    ref = (0.0, 0.0)
    points = [tuple(ind["objectives"]) for ind in pop]
    total_hv = hypervolume_2d(points, ref)
    contribs = []
    for i in range(len(pop)):
        others = [points[j] for j in range(len(pop)) if j != i]
        hv_others = hypervolume_2d(others, ref)
        contribs.append(total_hv - hv_others)
    return contribs

def sms_emoa_step(pop, evals_done):
    # 1 offspring per iteration
    # Tournament selection
    def tournament():
        i = random.randrange(len(pop))
        j = random.randrange(len(pop))
        a = pop[i]
        b = pop[j]
        # prefer feasible
        if a["feasible"] and not b["feasible"]:
            return i
        if b["feasible"] and not a["feasible"]:
            return j
        # if both infeasible, lower penalty is better
        if not a["feasible"] and not b["feasible"]:
            return i if a["penalty"] < b["penalty"] else j
        # both feasible: higher sum of objectives
        sa = sum(a["objectives"])
        sb = sum(b["objectives"])
        return i if sa > sb else j

    p1 = pop[tournament()]["gen"]
    p2 = pop[tournament()]["gen"]
    c1, c2 = sbx_crossover(p1, p2)
    polynomial_mutation(c1)
    polynomial_mutation(c2)

    # evaluate one offspring (SMS-EMOA uses one offspring per iteration; we can pick c1)
    child_gen = c1
    child_eval = evaluate_individual(child_gen)
    child_eval["gen"] = child_gen
    evals_done += 1

    # combine
    new_pop = pop + [child_eval]

    # separate feasible and infeasible
    feas = [ind for ind in new_pop if ind["feasible"]]
    infeas = [ind for ind in new_pop if not ind["feasible"]]

    if len(feas) > 0:
        # remove one individual based on HV contribution among feasible
        contribs = hypervolume_contributions(feas)
        # find index of smallest contribution
        min_idx = min(range(len(feas)), key=lambda i: contribs[i])
        to_remove = feas[min_idx]
    else:
        # all infeasible: remove one with largest penalty
        to_remove = max(infeas, key=lambda ind: ind["penalty"])

    # build final pop
    final_pop = []
    removed = False
    for ind in new_pop:
        if not removed and ind is to_remove:
            removed = True
            continue
        final_pop.append(ind)

    return final_pop, evals_done

# =========================
# PYGAME VISUALIZATION
# =========================

def draw_grid(surface, grid, bases, minerals, gas):
    surface.fill(COLOR_BG)

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if grid[y][x] == 1:
                color = COLOR_WALL
            else:
                color = COLOR_PASSABLE
            pygame.draw.rect(surface, color, rect)

    for x in range(GRID_SIZE):
        pygame.draw.line(surface, COLOR_GRID, (x * CELL_SIZE, 0), (x * CELL_SIZE, SCREEN_SIZE))
    for y in range(GRID_SIZE):
        pygame.draw.line(surface, COLOR_GRID, (0, y * CELL_SIZE), (SCREEN_SIZE, y * CELL_SIZE))

    for (x, y) in bases:
        cx = x * CELL_SIZE + CELL_SIZE // 2
        cy = y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, COLOR_BASE, (cx, cy), CELL_SIZE // 2)

    for (x, y) in minerals:
        cx = x * CELL_SIZE + CELL_SIZE // 2
        cy = y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, COLOR_MINERAL, (cx, cy), CELL_SIZE // 3)

    for (x, y) in gas:
        cx = x * CELL_SIZE + CELL_SIZE // 2
        cy = y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, COLOR_GAS, (cx, cy), CELL_SIZE // 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("SMS-EMOA StarCraft-like Map Evolution")

    clock = pygame.time.Clock()

    # init population
    pop = []
    evals_done = 0
    for _ in range(POP_SIZE):
        g = random_genotype()
        ev = evaluate_individual(g)
        ev["gen"] = g
        pop.append(ev)
        evals_done += 1

    best = max(pop, key=lambda ind: sum(ind["objectives"]) if ind["feasible"] else -1e9)

    running = True
    paused = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

        if not paused and evals_done < MAX_EVALS:
            pop, evals_done = sms_emoa_step(pop, evals_done)
            current_best = max(pop, key=lambda ind: sum(ind["objectives"]) if ind["feasible"] else -1e9)
            if current_best["feasible"] and sum(current_best["objectives"]) > sum(best["objectives"]):
                best = current_best

        draw_grid(screen, best["grid"], best["bases"], best["minerals"], best["gas"])
        pygame.display.set_caption(
            f"SMS-EMOA | Evals: {evals_done} | fb0={best['fb0']:.2f} fb1={best['fb1']:.2f} fr4={best['fr4']:.2f}"
        )
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
