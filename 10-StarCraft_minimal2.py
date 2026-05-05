import pygame
import random
import math
from collections import deque

#This program makes 4 maps at once, and only generates offspring for the non-selected maps, 
# so the parents remain unchanged.
#  This allows you to keep selecting the same parents across multiple generations if you want.
#  It also adds a visual divider between the maps and highlights selected maps with a red border.

GRID_SIZE = 64
CELL_SIZE = 6   # smaller so 4 maps fit
MAP_PIXEL_SIZE = GRID_SIZE * CELL_SIZE

N_MAPS = 4

SCREEN_WIDTH = MAP_PIXEL_SIZE * N_MAPS + (N_MAPS - 1) * 4
SCREEN_HEIGHT = MAP_PIXEL_SIZE

N_BASES = 3
N_MINERALS = 8
N_GAS = 4
N_WALLS = 6
WALL_MAX_STEPS = 400

# Colors
COLOR_BG = (10, 10, 20) # dark background 
COLOR_PASSABLE = (30, 30, 40) # slightly lighter for passable terrain
COLOR_WALL = (40, 40, 120) # dark blue for walls 
COLOR_BASE = (0, 200, 0) # bright green for bases 
COLOR_MINERAL = (0, 180, 255) # bright blue for minerals
COLOR_GAS = (255, 200, 0) # bright yellow for gas
COLOR_GRID = (50, 50, 70)# subtle grid lines 
COLOR_SELECTED = (255, 50, 50)# bright red for selected maps to clearly indicate selection
COLOR_DIVIDER = (255, 255, 255)# white divider between maps for better separation


# --- GENOME ---
# The random_genotype function creates a random genome of the appropriate length, which can then be decoded into a map.
# The genome is a flat list of floats in [0,1] that encodes the positions of bases, minerals, gas, and walls.
# e.g for 1 base, we have 2 floats (x,y), the first float determines the x-coordinate of the base (scaled to GRID_SIZE), and the second float determines the y-coordinate.
# for 1 mineral we have 2 floats, etc.
# Walls are encoded with 5 floats each: (x, y, p_left, p_right, p_gap) which determine the starting point and the random walk parameters for the wall.

#example of genome: [0.5, 0.5, 0.2, 0.8, 0.9, 0.1, 0.3, 0.7, 0.4, 0.6, 0.8, 0.2, 0.9, 0.1, 0.6, 0.4, 0.3, 0.7, 0.5, 0.8] which stands for 
# 1 base at (32, 32), 1 mineral at (12, 51), 1 gas at (25, 45), and 1 wall starting at (38, 38) with p_left=0.6, p_right=0.4, p_gap=0.3
# 0.5 stands for 32 because int(0.5 * GRID_SIZE) = int(0.5 * 64) = 32

def random_genotype():
    length = (N_BASES * 2) + (N_MINERALS * 2) + (N_GAS * 2) + (N_WALLS * 5) # 2 floats per base, mineral, gas + 5 floats per wall, total length of the genome is determined by the number of elements we want in the map
    result = []
    for i in range(length):
        result.append(random.random())
    return result

# --- GENETIC OPERATORS ---
# Mutation randomly tweaks some genes, while crossover averages two parents to create a child.
# Mutation and crossover only affect the non-selected maps, so parents remain unchanged.
# This allows you to keep selecting the same parents across multiple generations 
def mutate(gen, rate=0.1, strength=0.02):
    new = gen[:]
    for i in range(len(new)):
        if random.random() < rate:
            new[i] += random.uniform(-strength, strength)
            if new[i] < 0.0:
                new[i] = 0.0
            elif new[i] > 1.0:
                new[i] = 1.0
    return new
# Crossover simply averages the genes of two parents to create a child.
# Since parents are not modified, we can safely reuse them across generations if desired.

def crossover(g1, g2):
    result = []
    for a, b in zip(g1, g2): #zip(g1, g2) pairs elements from the two sequences. E.g g1 = [0.2, 0.8, 0.5] g2 = [0.6, 0.4, 0.9]  → [0.4, 0.6, 0.7]
        average = (a + b) / 2.0
        result.append(average)
    return result
"""
def crossover(g1, g2):
    if len(g1) != len(g2):
        raise ValueError("Genomes must have the same length")
    point = 1#random.randint(1, len(g1) - 1)
    child1 = []
    child2 = []
    # Before crossover point
    for i in range(point):
        child1.append(g1[i])
        child2.append(g2[i])
    # After crossover point
    for i in range(point, len(g1)):
        child1.append(g2[i])
        child2.append(g1[i])
    return child1, child2
"""
# --- DECODE ---
# The decode function converts the flat genome into structured data for bases, minerals, gas, and walls.
# To avoid repetition, we use a helper function to read points from the genome.
# Walls are more complex, so we read their parameters separately.
# The resulting grid is a 2D list where 0 = passable and 1 = wall, and we also return the lists of bases, minerals, and gas.
# The seed for wall generation is derived from the genome to ensure that the same genome always produces the same map.
# This is important for consistency when evaluating fitness in a genetic algorithm.
# The in_bounds function checks if a coordinate is within the grid, which is used when drawing walls.
# The draw_wall function uses a random walk to create a wall based on the parameters in the genome, and it modifies the grid accordingly.
# The generate_map function combines all of this to produce a complete map from a genome, including the grid and the locations of bases, minerals, and gas.
# The is_playable function checks if all important points (bases, minerals, gas) are reachable from each other using a flood fill algorithm.
# The generate_valid function keeps generating maps from the genome until it finds one that is playable, ensuring that all maps in the population are valid for gameplay.
def decode_genotype(gen):
    idx = 0

    def get_points(n):
        nonlocal idx
        pts = []
        for _ in range(n):
            x = int(gen[idx] * GRID_SIZE); idx += 1
            y = int(gen[idx] * GRID_SIZE); idx += 1
            pts.append((x, y))
        return pts

    bases = get_points(N_BASES)
    minerals = get_points(N_MINERALS)
    gas = get_points(N_GAS)

    walls = []
    for _ in range(N_WALLS):
        x = int(gen[idx] * GRID_SIZE); idx += 1
        y = int(gen[idx] * GRID_SIZE); idx += 1
        p_left = gen[idx]; idx += 1
        p_right = gen[idx]; idx += 1
        p_gap = gen[idx]; idx += 1
        walls.append((x, y, p_left, p_right, p_gap))

    return bases, minerals, gas, walls
# The in_bounds function checks if a coordinate is within the grid, which is used when drawing walls.
def in_bounds(x, y):
    return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

# --- WALLS ---
#  The draw_wall function uses a random walk to create a wall based on the parameters in the genome, and it modifies the grid accordingly.
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

        if r >= p_left + p_right and r < p_left + p_right + p_gap:
            continue

        grid[y][x] = 1
# The generate_map function combines all of this to produce a complete map from a genome, including the grid and the locations of bases, minerals, and gas.
def generate_map(gen):
    bases, minerals, gas, walls = decode_genotype(gen)
    grid = []
    # Initialize the grid with 0s (passable terrain)
    for y in range(GRID_SIZE):
        row = []
        for x in range(GRID_SIZE):
            row.append(0)
        grid.append(row)
    # The seed for wall generation is derived from the genome to ensure that the same genome always produces the same map.
    # This is important for consistency when evaluating fitness in a genetic algorithm.
    seed = int(sum(gen) * 1e6) % (2**32)
    rng = random.Random(seed)

    for w in walls:
        draw_wall(grid, *w, rng)

    return grid, bases, minerals, gas

# --- PATH CHECK ---
# The is_playable function checks if all important points (bases, minerals, gas) are reachable from each other using a flood fill algorithm.
# The generate_valid function keeps generating maps from the genome until it finds one that is playable,
#the search algorithm used is a breadth-first search (BFS) implemented in the flood_fill function, 
# which explores the grid starting from one point and marks all reachable points.
def flood_fill(grid, start):
    q = deque([start])
    visited = {start}

    while q:
        x, y = q.popleft()
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x+dx, y+dy
            if in_bounds(nx, ny) and grid[ny][nx] == 0:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny))
    return visited

# The is_playable function checks if all important points (bases, minerals, gas) are reachable from each other using a flood fill algorithm.
def is_playable(grid, bases, minerals, gas):
    points = bases + minerals + gas
    # If there are no points, the map is not playable
    if len(points) == 0:
        return False

    # Start flood fill from the first point
    start_point = points[0]
    reachable_points = flood_fill(grid, start_point)

    # Check each point one by one
    for point in points:
        if point not in reachable_points:
            return False

    return True

# The generate_valid function keeps generating maps from the genome until it finds one that is playable, 
# ensuring that all maps in the population are valid for gameplay.
def generate_valid(gen):
# Generate the map from the genotype
    grid, bases, minerals, gas = generate_map(gen)

    # Check if the map is playable
    if is_playable(grid, bases, minerals, gas):
        return grid, bases, minerals, gas
    else:
        return None

# --- DRAW ---
# The draw_map function renders the grid and the points (bases, minerals, gas) onto the Pygame surface. 
# It also highlights selected maps with a red border.
# The main loop handles user input for selecting maps and generating offspring through crossover and mutation, 
# while ensuring that parents remain unchanged.
# The visual divider between maps helps distinguish them, and the selected maps are highlighted with a red border for clarity.
def draw_map(surface, offset_x, grid, bases, minerals, gas, selected):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            color = COLOR_WALL if grid[y][x] else COLOR_PASSABLE
            rect = pygame.Rect(offset_x + x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, color, rect)

    for (x, y) in bases:
        pygame.draw.circle(surface, COLOR_BASE,
            (offset_x + x*CELL_SIZE + CELL_SIZE//2, y*CELL_SIZE + CELL_SIZE//2),
            CELL_SIZE//2)

    for (x, y) in minerals:
        pygame.draw.circle(surface, COLOR_MINERAL,
            (offset_x + x*CELL_SIZE + CELL_SIZE//2, y*CELL_SIZE + CELL_SIZE//2),
            CELL_SIZE//3)

    for (x, y) in gas:
        pygame.draw.circle(surface, COLOR_GAS,
            (offset_x + x*CELL_SIZE + CELL_SIZE//2, y*CELL_SIZE + CELL_SIZE//2),
            CELL_SIZE//3)

    if selected:
        pygame.draw.rect(surface, COLOR_SELECTED,
            (offset_x, 0, MAP_PIXEL_SIZE, MAP_PIXEL_SIZE), 3)

# --- MAIN ---
# The main loop initializes Pygame, generates an initial population of maps, and handles user input for selecting maps and generating offspring through crossover and mutation. It ensures that parents remain unchanged while generating new maps for the non-selected slots. The visual divider between maps helps distinguish them, and the selected maps are highlighted with a red border for clarity.
# The program continues running until the user closes the window, at which point Pygame is properly quit.
# The main function serves as the entry point for the program, orchestrating the generation and visualization of maps, as well as handling user interactions for selection and reproduction.
# By keeping the parents unchanged during reproduction, users can experiment with different combinations of maps across multiple generations without losing their original selections. This allows for a more flexible and interactive exploration of the map design space
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # initial population
    # We generate a list of N_MAPS random genotypes, and then we will convert them to maps.
    genotypes = []
    for i in range(N_MAPS):
        genotype = random_genotype()
        genotypes.append(genotype)
    # This will store the valid generated maps
    maps = []
    # We convert each genotype to a map, ensuring that it is valid (playable). 
    # If a generated map is not valid, we keep generating until we get a valid one. 
    # This ensures that all maps in our initial population are playable.
    for g in genotypes:
        m = None
        while m is None:
            g = random_genotype()
            m = generate_valid(g)
        maps.append(m)

    selected = []

    running = True
    while running:
        screen.fill(COLOR_BG)
        # We draw each map in the population side by side, with a divider between them.
        for i in range(N_MAPS):
            offset = i * (MAP_PIXEL_SIZE + 4)
            draw_map(screen, offset, *maps[i], i in selected)

            if i < N_MAPS - 1:
                pygame.draw.line(screen, COLOR_DIVIDER,
                                 (offset + MAP_PIXEL_SIZE + 2, 0),
                                 (offset + MAP_PIXEL_SIZE + 2, SCREEN_HEIGHT), 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, _ = pygame.mouse.get_pos()
                # Determine which map was clicked based on the x-coordinate of the mouse click, accounting for the width of the maps and the dividers between them.
                idx = mx // (MAP_PIXEL_SIZE + 4)
                if idx < N_MAPS:
                    if idx in selected:
                        selected.remove(idx)
                    elif len(selected) < 2:
                        selected.append(idx)
            # When the user presses the Enter key, 
            # if exactly 2 maps are selected, we perform crossover and mutation to generate new maps for the non-selected slots, 
            # while keeping the selected parents unchanged.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if len(selected) == 2:
                    p1, p2 = selected
                    # We create new lists for genotypes and maps to hold the offspring, 
                    # starting with copies of the current population.
                    new_genotypes = genotypes[:]
                    new_maps = maps[:]

                    # Generate offspring ONLY for non-selected slots
                    for i in range(N_MAPS):
                        if i not in selected:
                            # We perform crossover between the two selected parents to create a child genotype.
                            child = crossover(genotypes[p1], genotypes[p2])
                            # We then mutate the child genotype to introduce variation.
                            m = None
                            while m is None:
                                mutated = mutate(child)
                                m = generate_valid(mutated)
                            # Finally, we store the new genotype and its corresponding map in the new lists.
                            new_genotypes[i] = mutated
                            #  We generate a valid map from the mutated child genotype, ensuring that it is playable, and store it in the new maps list.
                            new_maps[i] = m

                    # parents remain untouched
                    genotypes = new_genotypes
                    maps = new_maps
                    selected = []
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()