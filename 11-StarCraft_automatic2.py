import pygame
import random
import math
import heapq
import statistics
from collections import deque
from copy import deepcopy

#------------------------------------------------
#This program generates StarCraft-like maps using a multi-objective evolutionary algorithm (MOEA). 
# It encodes map features (bases, resources, walls) in a genome, 
# evaluates playability and various fitness functions inspired by RTS map design principles, 
# and evolves maps using selection based on Pareto dominance and hypervolume contribution. 
# The program also includes an A* pathfinding implementation to evaluate map connectivity and resource accessibility. 
# The best evolved map is displayed using Pygame.
#
#The huyperparameters (e.g., population size, mutation rate, fitness function weights) can be adjusted to explore different map generation outcomes.
# The fitness functions evaluate aspects like base spacing, resource distribution, chokepoints,
#  and path overlap, which are crucial for creating engaging and balanced RTS maps.
"""
A* pathfinding
Multi-objective fitness evaluation
Playability constraints
Pareto dominance
Approximate SMS-EMOA selection
Recombination + mutation
Eight RTS-inspired entertainment/playability fitness functions:
base space
base distance
resource fairness
resource ownership
resource safety
path overlap
choke points
tactical geography
"""
# ==========================================================
# CONFIG
# ==========================================================

GRID_SIZE = 100
CELL_SIZE = 6
SCREEN_SIZE = GRID_SIZE * CELL_SIZE

POP_SIZE = 20
GENERATIONS_PER_SECOND = 5

N_BASES = 3 # Number of bases to place on the map
N_MINERALS = 8 # Number of mineral patches to place on the map
N_GAS = 4# Number of gas geysers to place on the map
N_WALLS = 6#
WALL_MAX_STEPS = 100

MUTATION_RATE = 0.08
MUTATION_STRENGTH = 0.08

# SMS-EMOA
MAX_EVALUATIONS = 50000

# ----------------------------------------------------------
# COLORS
# ----------------------------------------------------------

COLOR_BG = (10, 10, 20)
COLOR_PASSABLE = (30, 30, 40)
COLOR_WALL = (40, 40, 120)

COLOR_BASE = (0, 220, 0)
COLOR_MINERAL = (0, 180, 255)
COLOR_GAS = (255, 200, 0)

# ==========================================================
# GENOME
# ==========================================================
# The genome is a list of floats in [0,1] that encodes the positions of bases, minerals, gas, and walls.
#example: [0.1, 0.2, 0.3, 0.4, ...] where pairs of values represent x and y coordinates for bases and resources, 
# and additional values encode wall generation parameters.
def random_genotype():
    length = (
        (N_BASES * 2) +
        (N_MINERALS * 2) +
        (N_GAS * 2) +
        (N_WALLS * 5)
    )
    return [random.random() for _ in range(length)]

# ==========================================================
# MUTATION / RECOMBINATION
# ==========================================================

def mutate(gen, rate=MUTATION_RATE, strength=MUTATION_STRENGTH):
    #mutation iterates through each gene in the genome and randomly decides whether to mutate it based on the specified mutation rate.
    #If a gene is selected for mutation, it is modified by adding a random value within the range defined by the mutation strength. 
    # The resulting value is then clamped to ensure it remains within the valid range of [0, 1]. 
    # This process introduces variation into the population while maintaining valid gene values.
    #example: If a gene value is 0.5 and it is selected for mutation with a strength of 0.1, 
    # it might be modified to a new value between 0.4 and 0.6, ensuring that the gene remains valid for decoding into map features.
    g = gen[:]
    for i in range(len(g)):
        if random.random() < rate:
            g[i] += random.uniform(-strength, strength)
            #clamp to [0,1]
            g[i] = max(0.0, min(1.0, g[i]))
    #g formats the mutated genome as a new list of floats that can be decoded into map features for evaluation.
    return g


def crossover(a, b):
#crossover creates a child genome by taking a weighted average of two parent genomes.
#example: If parent A has a gene value of 0.2 and parent B has a gene value of 0.8,
# the child gene value might be a random weighted average, such as 0.5, which combines traits from both parents.
    child = []

    for x, y in zip(a, b):
        t = random.random()
        #t is a random value between 0 and 1 that determines the weighting of the two parent genes.
        #example: If t is 0.3, the child gene will be closer to parent A (0.2) than parent B (0.8), resulting in a child gene value of around 0.38.
        child.append((1 - t) * x + t * y) 
    #child format is a list of floats that represents the combined traits of the two parent genomes, 
    # which can then be decoded into map features for evaluation.
    return child

# ==========================================================
# DECODE
# ==========================================================
def decode_genotype(gen):
    #decode_genotype takes a genome (a list of floats) and translates it into map features such as base locations, mineral patches, gas geysers, and wall parameters.
    #example: If the genome starts with [0.1, 0.2, 0.3, 0.4, ...], the first two values (0.1, 0.2) might be decoded into a base location at (10, 20) on the grid,
    # the next two values (0.3, 0.4) might represent a mineral patch at (30, 40), and so on for gas geysers and wall parameters.
    idx = 0

    def get_points(n):
        nonlocal idx
        pts = []

        for _ in range(n):
            x = int(gen[idx] * GRID_SIZE)
            idx += 1

            y = int(gen[idx] * GRID_SIZE)
            idx += 1

            pts.append((x, y))

        return pts

    bases = get_points(N_BASES)
    minerals = get_points(N_MINERALS)
    gas = get_points(N_GAS)

    walls = []

    for _ in range(N_WALLS):

        x = int(gen[idx] * GRID_SIZE)
        idx += 1

        y = int(gen[idx] * GRID_SIZE)
        idx += 1

        p_left = gen[idx]
        idx += 1

        p_right = gen[idx]
        idx += 1

        p_gap = gen[idx]
        idx += 1

        walls.append((x, y, p_left, p_right, p_gap))

    return bases, minerals, gas, walls

# ==========================================================
# GRID HELPERS
# ==========================================================

def in_bounds(x, y):
    return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

# ==========================================================
# WALLS
# ==========================================================

def draw_wall(grid, x, y, p_left, p_right, p_gap, rng):

    total = p_left + p_right + p_gap

    if total == 0:
        return

    p_left /= total
    p_right /= total
    p_gap /= total

    angle = 0.0

    for _ in range(WALL_MAX_STEPS):

        r = rng.random()

        if r < p_left:
            angle -= math.pi / 4

        elif r < p_left + p_right:
            angle += math.pi / 4

        dx = int(round(math.cos(angle)))
        dy = int(round(math.sin(angle)))

        nx, ny = x + dx, y + dy

        if not in_bounds(nx, ny):
            break

        x, y = nx, ny

        if r >= p_left + p_right:
            continue

        grid[y][x] = 1

# ==========================================================
# MAP
# ==========================================================

def generate_map(gen):
#decode_genotype takes a genome (a list of floats) and translates it into map features such as base locations, mineral patches, gas geysers, and wall parameters.
    bases, minerals, gas, walls = decode_genotype(gen)
    #grid is initialized as a 2D list representing the map, where each cell is either passable (0) or a wall (1).   
    #example: A 100x100 grid is created, and initially all cells are set to 0 (passable). 
    grid = []
    for y in range(GRID_SIZE):
        row = []
        for x in range(GRID_SIZE):
            row.append(0) #
        grid.append(row)

    seed = int(sum(gen) * 1e6) % (2**32)

    rng = random.Random(seed)

    # The walls defined by the genome will modify the grid to create the map layout.
    for wall in walls:

        x = wall[0]
        y = wall[1]

        p_left  = wall[2]
        p_right = wall[3]
        p_gap   = wall[4]

        draw_wall(grid, x, y, p_left, p_right, p_gap, rng)
    return grid, bases, minerals, gas

# ==========================================================
# A*
# ==========================================================

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(grid, start, goal):

    if grid[start[1]][start[0]] == 1:
        return None

    if grid[goal[1]][goal[0]] == 1:
        return None

    frontier = []

    heapq.heappush(frontier, (0, start))

    came_from = {}
    cost_so_far = {}

    came_from[start] = None
    cost_so_far[start] = 0

    while frontier:

        _, current = heapq.heappop(frontier)

        if current == goal:

            path = []

            while current is not None:
                path.append(current)
                current = came_from[current]

            path.reverse()

            return path

        x, y = current

        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:

            nx, ny = x + dx, y + dy

            if not in_bounds(nx, ny):
                continue

            if grid[ny][nx] == 1:
                continue

            nxt = (nx, ny)

            new_cost = cost_so_far[current] + 1

            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:

                cost_so_far[nxt] = new_cost

                priority = new_cost + heuristic(goal, nxt)

                heapq.heappush(frontier, (priority, nxt))

                came_from[nxt] = current

    return None

def path_distance(grid, a, b):

    p = astar(grid, a, b)

    if p is None:
        return None

    return len(p)

# ==========================================================
# PLAYABILITY
# ==========================================================

def flood_fill(grid, start):
#flood_fill performs a breadth-first search (BFS) starting from a given point on the grid to determine which cells are reachable.
    q = deque([start])

    visited = {start}

    while q:

        x, y = q.popleft()

        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:

            nx, ny = x + dx, y + dy

            if in_bounds(nx, ny) and grid[ny][nx] == 0:

                if (nx, ny) not in visited:

                    visited.add((nx, ny))
                    q.append((nx, ny))

    return visited

def is_playable(grid, bases, minerals, gas):
#
    points = bases + minerals + gas

    if not points:
        return False

    reachable = flood_fill(grid, points[0])

    return all(p in reachable for p in points)

# ==========================================================
# FITNESS FUNCTIONS
# ==========================================================

def clamp01(v):
    return max(0.0, min(1.0, v))

# ----------------------------------------------------------
# fb0 BASE SPACE
# ----------------------------------------------------------

def fitness_base_space(grid, bases):
#fitness_base_space evaluates the spacing of bases on the map by checking the proportion of passable cells around each base within a certain radius.
#example: For each base, the function checks a 5x5 area around it and calculates the ratio of passable cells to total cells in that area.
# If a base is surrounded by many walls, it will have a low score, while a base with more open space around it will score higher.
# The final fitness score is the average of these ratios for all bases, providing an overall measure of how well-spaced the bases are on the map.
    vals = []

    for bx, by in bases:

        total = 0
        good = 0

        for dy in range(-2, 3):
            for dx in range(-2, 3):

                nx, ny = bx + dx, by + dy

                if not in_bounds(nx, ny):
                    continue

                total += 1

                if grid[ny][nx] == 0:

                    d = path_distance(grid, (bx, by), (nx, ny))

                    if d is not None and d <= 5:
                        good += 1

        vals.append(good / max(1, total))

    return sum(vals) / len(vals)

# ----------------------------------------------------------
# fb1 BASE DISTANCE
# ----------------------------------------------------------

def fitness_base_distance(grid, bases):
#fitness_base_distance evaluates the minimum path distance between all pairs of bases on the map.
#example: If there are three bases located at (10, 10), (50, 50), and (90, 90), 
# the function will calculate the path distance between each pair of bases using the A* algorithm.
# If the distance between any two bases is very short (e.g., 5 steps), it will contribute to a lower fitness score, 
# while longer distances (e.g., 30 steps) will contribute to a higher score.
    dists = []

    for i in range(len(bases)):
        for j in range(i+1, len(bases)):

            d = path_distance(grid, bases[i], bases[j])

            if d is None:
                return 0.0

            dists.append(d)

    if not dists:
        return 0.0

    return clamp01(min(dists) / (GRID_SIZE * 2))

# ----------------------------------------------------------
# fr1 RESOURCE DISTANCE FAIRNESS
# ----------------------------------------------------------

def closest_distance(grid, base, resources):
#closest_distance calculates the shortest path distance from a given base to the closest resource (either mineral or gas) using the A* pathfinding algorithm.
#example: If a base is located at (10, 10) and there are mineral patches at (20, 20) and (30, 30), 
# the function will compute the path distance from the base to each mineral patch and return the shortest distance.
# If the base cannot reach any of the resources due to walls blocking the path, the function will return None, 
# indicating that the resource is inaccessible from that base.
# This function is used in the fitness evaluation to assess how well resources are distributed in relation to the bases, 
# contributing to the overall resource distance fairness of the map.
    vals = []

    for r in resources:
        d = path_distance(grid, base, r)

        if d is not None:
            vals.append(d)

    if not vals:
        return None

    return min(vals)

def fitness_resource_distance(grid, bases, minerals, gas):
#fitness_resource_distance evaluates the fairness of resource distribution 
# by calculating the sum of the closest distances from each base to the nearest mineral patch and gas geyser.
#example: For each base, the function finds the closest mineral patch and gas geyser and sums their distances.
# If a base has a mineral patch 5 steps away and a gas geyser 10 steps away, its contribution to the fitness score would be 15.
# The function then compares the minimum and maximum of these sums across all bases to assess fairness.
    vals = []

    for b in bases:

        dm = closest_distance(grid, b, minerals)
        dg = closest_distance(grid, b, gas)

        if dm is None or dg is None:
            return 0.0

        vals.append(dm + dg)

    mn = min(vals)
    mx = max(vals)

    if mx == 0:
        return 1.0

    return mn / mx

# ----------------------------------------------------------
# fr2 RESOURCE OWNERSHIP
# ----------------------------------------------------------

def fitness_resource_ownership(grid, bases, minerals, gas):
#fitness_resource_ownership evaluates how well resources are "owned" by bases, meaning how many resources are closest to each base compared to others.
#example: If there are three bases and a total of 12 resources, the function will determine how many resources are closest to each base.
# If one base has 8 resources closest to it while the others have only 2 each, the fitness score will be lower due to poor ownership distribution.
# Conversely, if the resources are more evenly distributed (e.g., each base has 4 resources closest to it), the fitness score will be higher, 
# indicating better ownership fairness on the map.

    resources = minerals + gas

    ownership = []

    for r in resources:

        dists = []

        for b in bases:

            d = path_distance(grid, b, r)

            if d is not None:
                dists.append(d)

        if not dists:
            continue

        best = min(dists)

        owners = sum(1 for d in dists if d == best)

        ownership.append(1.0 / owners)

    if not ownership:
        return 0.0

    return sum(ownership) / len(ownership)

# ----------------------------------------------------------
# fr3 RESOURCE SAFETY
# ----------------------------------------------------------

def fitness_resource_safety(grid, bases, minerals, gas):
#fitness_resource_safety evaluates the safety of resources by measuring the variability in distances from bases to their closest resources.
#example: For each resource, the function calculates the distances from all bases to that resource and computes the standard deviation of these distances.
# If a resource is equally accessible from all bases (e.g., 10 steps from each base), 
# it will have a low standard deviation, contributing to a higher fitness score.
# Conversely, if a resource is much closer to one base (e.g., 5 steps from one base and 20 steps from another), 
# it will have a higher standard deviation, which may indicate that the resource is less safe and more likely to be contested, resulting in a lower fitness score.
    def score(resources):

        deviations = []

        for r in resources:

            dists = []

            for b in bases:

                d = path_distance(grid, b, r)

                if d is not None:
                    dists.append(d)

            if len(dists) >= 2:
                deviations.append(statistics.pstdev(dists))

        if not deviations:
            return 0.0

        return sum(deviations) / len(deviations)

    s1 = score(minerals)
    s2 = score(gas)

    val = min(s1, s2)

    return clamp01(val / GRID_SIZE)

# ----------------------------------------------------------
# fr4 RESOURCE FAIRNESS
# ----------------------------------------------------------

def fitness_resource_fairness(grid, bases, minerals, gas):
#fitness_resource_fairness evaluates the fairness of resource distribution 
# by comparing the sums of the closest distances from each base to its nearest mineral patch and gas geyser.
#example: For each base, the function calculates the sum of the distance to the closest mineral patch and the closest gas geyser.
# If one base has a total distance of 15 (e.g., 5 to minerals and 10 to gas) while another base has a total distance of 30 (e.g., 20 to minerals and 10 to gas),
# the fitness score will be lower due to the disparity in resource accessibility.
# Conversely, if all bases have similar total distances to their closest resources (e.g., each base has a total distance of around 20),
# the fitness score will be higher, indicating a more fair distribution of resources across the map.
# This function is similar to fitness_resource_distance but focuses on the fairness aspect by comparing the sums of distances rather than their ratio.
    vals = []

    for b in bases:

        dm = closest_distance(grid, b, minerals)
        dg = closest_distance(grid, b, gas)

        if dm is None or dg is None:
            return 0.0

        vals.append(dm + dg)

    mx = max(vals)
    mn = min(vals)

    return clamp01(1.0 - ((mx - mn) / GRID_SIZE))

# ----------------------------------------------------------
# fp1 CHOKE POINTS
# ----------------------------------------------------------

def local_width(grid, x, y):
#local_width calculates the width of a choke point at a given cell by checking how many passable cells are connected in the horizontal direction.
#example: If a cell at (50, 50) is part of a choke point, the function will check to the left and right of that cell to count how many consecutive passable cells there are before hitting a wall.
# If there are 2 passable cells to the left and 3 passable cells to the right before hitting walls, the local width would be 1 (the cell itself) + 2 (left) + 3 (right) = 6.    
# This function is used in the fitness evaluation to identify narrow passages on the map, which can be important for strategic gameplay.
# A lower local width indicates a tighter choke point, which can be advantageous for defensive strategies, while a higher local width indicates a more open area that may be less defensible.
# The fitness_chokepoints function uses local_width to evaluate the narrowest point along paths between bases, contributing to the overall assessment of map design in terms of strategic chokepoints.
# The local width is calculated by starting from the given cell and expanding left and right until a wall is encountered, counting the number of passable cells in each direction.
# The total width is the sum of the passable cells to the left and right plus one for the cell itself, providing a measure of how narrow or wide the passage is at that point.

    width = 1

    for dx in [-1, 1]:

        nx = x

        while True:

            nx += dx

            if not in_bounds(nx, y):
                break

            if grid[y][nx] == 1:
                break

            width += 1

    return width

def fitness_chokepoints(grid, bases):
#fitness_chokepoints evaluates the presence of chokepoints between bases by finding paths between them and measuring the narrowest point along those paths.
#example: If there are two bases located at (10, 10) and (90, 90), the function will find the path between them using A* and check the local width at each cell along that path.
# If the narrowest point along the path has a local width of 2, it indicates a tight chokepoint, contributing to a higher fitness score.
# Conversely, if the narrowest point has a local width of 5, it indicates a wider passage, which may contribute to a lower fitness score.
# The function calculates the fitness score by taking the inverse of the narrowest width (1 / (1 + narrowest)) 
# for each pair of bases and averaging these values across all pairs.
# This means that maps with tighter chokepoints between bases will score higher, 
# while maps with wider passages will score lower, reflecting the strategic importance of chokepoints in RTS map design.
    vals = []

    for i in range(len(bases)):
        for j in range(i+1, len(bases)):

            p = astar(grid, bases[i], bases[j])

            if not p:
                continue

            narrowest = min(local_width(grid, x, y) for x, y in p)

            vals.append(1.0 / (1 + narrowest))

    if not vals:
        return 0.0

    return sum(vals) / len(vals)

# ----------------------------------------------------------
# fp2 PATH OVERLAP
# ----------------------------------------------------------

def fitness_path_overlap(grid, bases, minerals, gas):
#fitness_path_overlap evaluates the overlap of paths from bases to resources by counting how many paths share the same cells on the grid.
#example: If there are three bases and a total of 12 resources, the function will find the paths from each base to its closest resources and count how many times each cell on the grid is used in these paths.
# If many paths overlap on the same cells (e.g., a narrow passage that all bases must use to reach a resource), it will contribute to a higher fitness score, indicating more strategic contention points.
# Conversely, if the paths are more spread out with less overlap, it will contribute to a
# lower fitness score, indicating that resources are more easily accessible without forcing players to compete for the same routes.
# The function calculates the average usage of cells across all paths and normalizes it to provide a fitness score that reflects the degree of path overlap on the map.
# This fitness function is important for assessing how much players will have to contend for the same routes to access resources, which can impact the strategic depth and balance of the map.
# The function works by first finding the paths from each base to each resource and then counting how many times each cell is used across all these paths.
# The average usage is then calculated and normalized to provide a score between 0 and 1, where higher scores indicate more path overlap and potential contention points on the map.
# The fitness score is calculated by taking the average usage of cells across all paths and dividing it by a normalization factor (in this case, 10.0) to ensure the score remains between 0 and 1.
# The clamp01 function is used to ensure that the final fitness score does not exceed 1.0, even if there is a high degree of path overlap.
    usage = {}

    total_paths = 0

    resources = minerals + gas

    for b in bases:
        for r in resources:

            p = astar(grid, b, r)

            if p is None:
                continue

            total_paths += 1

            for cell in p:
                usage[cell] = usage.get(cell, 0) + 1

    if not usage:
        return 0.0

    avg = sum(usage.values()) / len(usage)

    return clamp01(avg / 10.0)

# ==========================================================
# MULTI OBJECTIVE FITNESS
# ==========================================================

FITNESS_NAMES = [
    "fb0",
    "fb1",
    "fr1",
    "fr2",
    "fr3",
    "fr4",
    "fp1",
    "fp2"
]

def evaluate(genome):
# evaluate takes a genome, generates the corresponding map features, checks if the map is playable, and if so, 
# calculates various fitness scores based on the defined fitness functions.
#example: If a genome encodes a map with three bases, several mineral patches, and some walls, 
# the function will first generate the grid and place the features according to the genome.
# It will then check if all bases and resources are reachable (playable). If the map is not playable, it returns a fitness score of 0 for all objectives.
# If the map is playable, it calculates the fitness scores for
#  base spacing, base distance, resource distance fairness, resource ownership, resource safety, resource fairness, chokepoints, and path overlap.
# The function returns a dictionary containing the validity of the map, the list of fitness scores for each objective, 
# and the generated map features for potential visualization.
# The fitness scores are calculated using the previously defined fitness functions, 
# which assess different aspects of the map design to ensure it is engaging and balanced for RTS gameplay.
#
    grid, bases, minerals, gas = generate_map(genome)

    if not is_playable(grid, bases, minerals, gas):

        return {
            "valid": False,
            "fitness": [0.0] * 8,
            "map": (grid, bases, minerals, gas)
        }

    # If the map is playable, the function calculates the fitness scores for each of the defined objectives and returns them in a structured format.
    #format of the returned dictionary includes a "valid" key indicating whether the map is playable, 
    # a "fitness" key containing a list of fitness scores for each objective, 
    # and a "map" key that holds the generated grid and feature locations for potential visualization or further analysis.
    #fitness key contains a list of fitness scores corresponding to the defined objectives, which can be used for selection and evolution in the MOEA process.
    #e.g., fitness[0] corresponds to the base space fitness score, fitness[1] corresponds to the base distance fitness score, and so on for each of the eight defined fitness functions.    
    
    fitness = [
        #Base Space (fb0)
        #Measures how much navigable space surrounds each base.
        #RTS bases need:
        #room for building placement
        #unit movement
        #defensive maneuvering
        fitness_base_space(grid, bases),
        #Base Distance (fb1)
        #Measures strategic spacing between player starting locations.
        #If bases are too close:
        #rushes dominate
        #matches become too short
        #If too far:
        #interaction becomes rare
        fitness_base_distance(grid, bases),
        #Resource Distance Fairness (fr1)
        #Ensures all bases have similar access to resources.
        #This prevents:
        #one player spawning with major economic advantage
        fitness_resource_distance(
            grid, bases, minerals, gas
        ),
        #Resource Ownership (fr2)
        #Measures territorial control over resources.
        #Resources should naturally belong to particular bases.
        fitness_resource_ownership(
            grid, bases, minerals, gas
        ),
        #Resource Safety (fr3)
        #Measures how risky resource gathering is.
        #Resources equally reachable by all players are dangerous.
        #Resources protected by one base are safer.
        fitness_resource_safety(
            grid, bases, minerals, gas
        ),
        #Resource Fairness (fr4)
        #Measures whether all players receive equivalent total economic access.
        #Unlike fr1, this explicitly evaluates disparity.
        fitness_resource_fairness(
            grid, bases, minerals, gas
        ),
        #Chokepoints (fp1)
        #Evaluates narrow passages between bases.
        #Chokepoints are central to RTS gameplay because they:
        #enable defense
        #create ambushes
        #shape battles
        fitness_chokepoints(
            grid, bases
        ),
        #how frequently players are forced through shared routes.
        #Path Overlap (fp2)
        #Measures how frequently players are forced through shared routes.
        #Shared paths create:
        # conflict
        # pressure
        # territorial contest
        fitness_path_overlap(
            grid, bases, minerals, gas
        )
    ]

    return {
        "valid": True,
        "fitness": fitness,
        "map": (grid, bases, minerals, gas)
    }

# ==========================================================
# PARETO DOMINANCE
# ==========================================================

def dominates(a, b):
#dominates checks if one individual (a) dominates another individual (b) based on their fitness scores.
# The function checks if all fitness scores of A are greater than or equal to those of B (better_or_equal) 
# and if at least one fitness score of A is strictly greater than that of B (strictly_better).

#example: If individual A has fitness scores [0.8, 0.9, 0.7] and individual B has fitness scores [0.7, 0.9, 0.6],
# the function will compare each corresponding fitness score.
# In this case, A is better than B in the first and third objectives (0.8 > 0.7 and 0.7 > 0.6) and equal in the second objective (0.9 == 0.9).
# Since A is better in at least one objective and not worse in any objective, A dominates B, and the function will return True.
# Conversely, if A had a fitness score of [0.8, 0.8, 0.7], it would not dominate B because it is worse in the second objective (0.8 < 0.9), and the function would return False.

    better_or_equal = True
    strictly_better = False

    for x, y in zip(a["fitness"], b["fitness"]):

        if x < y:
            better_or_equal = False
            break

        if x > y:
            strictly_better = True

    return better_or_equal and strictly_better

# ==========================================================
# HYPERVOLUME CONTRIBUTION (APPROX)
# ==========================================================
#hypervolume_contribution calculates an approximate contribution of an individual to the hypervolume of the Pareto front 
# by summing its fitness scores and applying a penalty for any individuals in the population that dominate it.
#example: If an individual has fitness scores [0.8, 0.9, 0.7], the function will sum these scores to get a total fitness of 2.4.
# It will then check the population to see if any other individuals dominate this individual.
# If there are 3 individuals that dominate it, the domination penalty will be 3.
# The final hypervolume contribution will be the total fitness (2.4) minus the domination penalty (3), resulting in a contribution of -0.6.
# This approximation allows the algorithm to estimate the contribution of each individual to the overall Pareto front 
# without performing a full hypervolume calculation, which can be computationally expensive.

# The function returns a value that can be used to identify which individuals are contributing more to the diversity and quality of the Pareto front,
# with higher values indicating greater contribution and lower (or negative) values indicating less contribution due to being dominated by others in the population.
# The hypervolume contribution is used in the selection process of the MOEA to determine which individuals to remove from the population when it exceeds the specified size,
# ensuring that the population maintains a diverse and high-quality set of solutions across the multiple objectives.
def hypervolume_contribution(ind, pop):

    s = sum(ind["fitness"])

    domination_penalty = 0

    for other in pop:

        if other is ind:
            continue

        if dominates(other, ind):
            domination_penalty += 1

    return s - domination_penalty

# ==========================================================
# SMS-EMOA
# ==========================================================

def create_individual():
#create_individual generates a new random individual by creating a random genome, evaluating it to determine its fitness and validity, 
# and returning a structured dictionary containing the genome, its fitness scores, validity status, and the generated map features.
#example: The function will call random_genotype to create a new genome (e.g., [0.1, 0.2, 0.3, ...]), 
# then it will evaluate this genome to generate the corresponding map and calculate its fitness scores.
# If the generated map is playable, the fitness scores will reflect the various objectives; 
# if not, the fitness scores will be set to 0 and the valid flag will be False.
# The returned dictionary will have the format: {
#     "genome": [0.1, 0.2, 0.3, ...],
#     "valid": True or False,   
#     "fitness": [0.8, 0.9, 0.7, ...],
#     "map": (grid, bases, minerals, gas)   
# }

    genome = random_genotype()

    e = evaluate(genome)
    individual = {}
    individual["genome"] = genome
    # The individual's genome is stored in the "genome" key, 
    # while the evaluation results (validity, fitness scores, and map features) are unpacked and 
    # added to the individual's dictionary for easy access during selection and evolution processes.
    for key in e:
        individual[key] = e[key]
    
    # The function returns a complete individual that can be added to the population for the MOEA process. 
    # Format of the returned individual includes the genome, its validity, fitness scores for each objective, 
    # and the generated map features for potential visualization or further analysis.
    return individual 

def offspring(pop):
#offspring creates a new child individual by selecting two parent genomes from the population, performing crossover to combine their traits,
# applying mutation to introduce variation, and then evaluating the resulting child genome to determine its fitness and validity.
#example: The function randomly selects two parent individuals from the population (e.g., Parent A with genome [0.1, 0.2, 0.3, ...] and Parent B with genome [0.4, 0.5, 0.6, ...]),
# performs crossover to create a child genome that combines traits from both parents (e.g., [0.25, 0.35, 0.45, ...]), applies mutation to introduce random changes (e.g., [0.27, 0.33, 0.48, ...]),
# and then evaluates the child genome to generate its fitness scores and validity status.
    parent_a = random.choice(pop)["genome"]
    parent_b = random.choice(pop)["genome"]

    child_genome = crossover(parent_a, parent_b)
    child_genome = mutate(child_genome)

    e = evaluate(child_genome)

    individual = {}
    individual["genome"] = child_genome
    for key in e:
        individual[key] = e[key]
    return individual

def remove_worst(pop):
#remove_worst identifies and removes the worst individual from the population based on validity and hypervolume contribution.
#example: The function first checks for any invalid individuals in the population (e.g., those with "valid" set to False). 
# If it finds any, it removes the first invalid individual it encounters.
# If all individuals are valid, it calculates the hypervolume contribution for each individual and 
# identifies the one with the lowest contribution (e.g., the individual that is dominated by many others and has low fitness scores) and 
# removes it from the population.   

    invalid = [p for p in pop if not p["valid"]]

    if invalid:
        worst = invalid[0]
        pop.remove(worst)
        return

    contributions = [
        hypervolume_contribution(p, pop)
        for p in pop
    ]

    idx = contributions.index(min(contributions))

    pop.pop(idx)

# ==========================================================
# DRAW
# ==========================================================

def draw_map(screen, grid, bases, minerals, gas):

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):

            color = (
                COLOR_WALL
                if grid[y][x]
                else COLOR_PASSABLE
            )

            pygame.draw.rect(
                screen,
                color,
                (
                    x * CELL_SIZE,
                    y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
            )

    for (x, y) in bases:

        pygame.draw.circle(
            screen,
            COLOR_BASE,
            (
                x * CELL_SIZE + CELL_SIZE // 2,
                y * CELL_SIZE + CELL_SIZE // 2
            ),
            CELL_SIZE // 1
        )

    for (x, y) in minerals:

        pygame.draw.circle(
            screen,
            COLOR_MINERAL,
            (
                x * CELL_SIZE + CELL_SIZE // 2,
                y * CELL_SIZE + CELL_SIZE // 2
            ),
            CELL_SIZE // 3
        )

    for (x, y) in gas:

        pygame.draw.circle(
            screen,
            COLOR_GAS,
            (
                x * CELL_SIZE + CELL_SIZE // 2,
                y * CELL_SIZE + CELL_SIZE // 2
            ),
            CELL_SIZE // 3
        )

# ==========================================================
# BEST INDIVIDUAL
# ==========================================================

def best_individual(pop):
#best_individual identifies the best individual in the population based on the highest sum of fitness scores across all objectives.
#example: The function iterates through the population and calculates the sum of fitness scores for each individual 
# (e.g., Individual A with fitness [0.8, 0.9, 0.7] has a total fitness of 2.4).
# It compares these sums and returns the individual with the highest total fitness score, 
# which represents the best overall solution in the population considering all objectives.  
    #return max( pop, key=lambda p: sum(p["fitness"]) )
    best_score = -999999
    for individual in pop:
        score = sum(individual["fitness"])
        if score > best_score:
            best_score = score
            best = individual
    return best
# ==========================================================
# MAIN
# ==========================================================

def main():

    pygame.init()

    screen = pygame.display.set_mode(
        (SCREEN_SIZE, SCREEN_SIZE)
    )

    pygame.display.set_caption(
        "MOEA RTS Map Evolution"
    )

    clock = pygame.time.Clock()

    # ------------------------------------------------------
    # INITIAL POPULATION
    # ------------------------------------------------------

    population = [
        create_individual()
        for _ in range(POP_SIZE)
    ]

    evaluations = POP_SIZE

    running = True

    while running:

        # --------------------------------------------------
        # EVOLUTION
        # --------------------------------------------------

        for _ in range(GENERATIONS_PER_SECOND):

            if evaluations >= MAX_EVALUATIONS:
                break

            child = offspring(population)

            population.append(child)

            remove_worst(population)

            evaluations += 1

        # --------------------------------------------------
        # DISPLAY
        # --------------------------------------------------

        best = best_individual(population)

        grid, bases, minerals, gas = best["map"]

        draw_map(
            screen,
            grid,
            bases,
            minerals,
            gas
        )

        pygame.display.set_caption(
            f"Eval {evaluations} | "
            f"Fitness: "
            f"{[round(x,2) for x in best['fitness']]}"
        )

        pygame.display.flip()

        # --------------------------------------------------
        # EVENTS
        # --------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

        clock.tick(30)

    pygame.quit()

# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":
    main()