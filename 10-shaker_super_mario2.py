# FULL 1:1 STYLE IMPLEMENTATION (Closer to Paper)
# Includes: grammar expansion, priorities, structured generation, GE loop

import pygame
import random
# ==============================
#The Evolving levels for Super Mario Bros using grammatical evolution 
# in proceedings of the IEEE E conference on computational intelligence and games 
# pages 300 and four 311 IEEE 2012
#Inspired by the paper "Procedural Content Generation of Super Mario Bros. 
# using a Simple Evolutionary Algorithm" (https://arxiv.org/abs/1705.10869).
# ==============================
# This code implements a simplified version of the procedural content generation approach described in the paper.
# It defines a genetic algorithm that evolves levels for a Mario-like game using a grammar-based representation.
# The code includes functions for creating individuals, mutating them, performing crossover, and selecting parents
# using tournament selection. 
# The main loop evolves the population for a number of generations and then
# displays the best level using Pygame.
# ==============================
# the chromosome is a list of integers,
#  and each integer is expanded into a chunk with specific parameters based on the grammar rules. 
# e.g a gene value might correspond to a "platform" chunk with certain x, y, and width parameters,
# while another gene might correspond to a "hill" chunk with its own parameters.
# example of a chromosome: [23, 45, 67, 89, 12, 34, 56, 78]
# The expand_gene function takes a gene value and maps it to a chunk type and its parameters
# based on the grammar rules defined in the paper.
# For instance, a gene value of 23 might be expanded to a "platform" chunk with specific x, y, and width parameters, 
# while a gene value of 45 might be expanded to a "hill" chunk with its own parameters.  
# The build_level function then takes a chromosome (list of genes), expands them into chunks, and constructs the level grid based on the grammar rules and priorities.

#For instance the gene value of 23 might be expanded to a "platform" chunk with specific x, y, and width parameters,
#This mapping is determined by the expand_gene function, which uses the gene value to determine the type of chunk (e.g., gap, platform, hill, coin, enemy) and its parameters (e.g., x, y, width, height).
#this is performed by taking the gene value and applying modulo operations to determine the chunk type and randomly generating parameters based on the type.
# ==============================
# CONFIG
WIDTH, HEIGHT = 1000, 400
TILE = 20
COLS = WIDTH // TILE
ROWS = HEIGHT // TILE

POP_SIZE = 50
GENERATIONS = 10
CHROM_LEN = 40

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

SKY = (135,206,235)
GROUND = (139,69,19)
HILL = (34,139,34)
ENEMY = (200,50,50)
COIN = (255,215,0)

# ==============================
# PRIORITY MAP (for placement conflicts)
# ==============================
PRIORITY = {
    "gap": 5,
    "platform": 4,
    "hill": 3,
    "enemy": 2,
    "coin": 1
}

# ==============================
# GRAMMAR RULES (Fig.4 inspired)
# ==============================
# Each gene encodes a chunk type and its parameters.
# Types: gap, platform, hill, coin, enemy
# Parameters are randomly generated based on the type, but could be evolved as well.
# For example, a "platform" chunk might have parameters for x, y, and width,
#  while a "hill" might have x, y, width, and height.
# The expand_gene function takes a gene value and maps it to a chunk type and its parameters.
#The gene has a form of an integer, and we use modulo to determine the type of chunk it represents.
# ==============================
def expand_gene(gene):
    # Each gene is a number between 0 and 255. 
    # gene%5  forces to 5 chunk types: 0, 1, 2, 3, 4
    # e.g 23 % 5 = 3 → coin; 45 % 5 = 0 → gap...
    t = gene % 5

    x = 5 + (gene % (COLS-10))
    y = (gene // 7) % (ROWS//2) + ROWS//2

    if t == 0:  # gap
        w = (gene // 11) % 4 + 2 # width between 2 and 5
        return ("gap", x, y, w)

    if t == 1:  # platform 
        w = (gene // 13) % 12 + 3 # width between 3 and 14
        return ("platform", x, y, w)

    if t == 2:  # hill
        w = (gene // 17) % 8 + 3 # width between 3 and 10
        h = (gene // 19) % 3 + 1 # height between 1 and 3
        return ("hill", x, y, w, h)

    if t == 3:  # coin
        n = (gene // 23) % 5 + 2 # number of coins between 2 and 6
        return ("coin", x, y-2, n)

    if t == 4:  # enemy
        return ("enemy", x)

# ==============================
# BUILD LEVEL (3-step like paper)
# ==============================
# The build_level function then takes a chromosome (list of genes), 
# expands them into chunks, and constructs the level grid based on the grammar rules and priorities.
# It first creates a base platform, 
# then adds structure (platforms, hills, gaps), 
# and finally places enemies and coins in valid positions.
def build_level(chromosome):
    grid = []
    #initializes the grid with "empty" tiles
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            row.append(("empty", -1))
        grid.append(row)

    # base platform
    #It then creates a base platform at the bottom row by filling it with "ground" tiles.
    for x in range(COLS):
        grid[ROWS-1][x] = ("ground", 10)
    # Next, it iterates through the chromosome, expands each gene into a chunk using the expand_gene function, and stores these chunks in a list.
    chunks = []
    for g in chromosome:
        chunk = expand_gene(g) # expands the gene into a chunk (type and parameters)
        chunks.append(chunk)

    #The list of chucks should have now the expanded chunks with their parameters, which will be used to build the level in the next steps.
    #For instance: [("platform", 23, 18, 5), ("hill", 45, 20, 8, 2), ("coin", 67, 16, 4), ("enemy", 89, 30), ("gap", 12, 22, 3), ...]
    # 1. STRUCTURE 
    # (platforms, hills, gaps)
    for c in chunks:
        t = c[0]

        if t == "platform":
            x = c[1] # x position of the platform
            y = c[2] #  y position of the platform 
            w = c[3] # width of the platform
            for i in range(w):
                place(grid, x+i, y, "ground")

        elif t == "hill":
            x = c[1]
            y = c[2]
            w = c[3]
            h = c[4]
            for i in range(w):
                for j in range(h):
                    place(grid, x+i, y-j, "hill")

        elif t == "gap":
            x = c[1]
            w = c[3]
            for i in range(w):
                place(grid, x+i, ROWS-1, "empty", force=True)

    # 2. VALID POSITIONS
    # Before placing enemies and coins, we need to determine valid positions where they can be placed.
    #This is done by checking the grid for "empty" tiles that are above "ground" or "hill" tiles, 
    # ensuring that enemies and coins are placed in locations where they can be supported and are reachable by the player.
    valid_positions = []
    for y in range(ROWS-1):
        for x in range(COLS):
            # Check the type of the tile below
            tile_below_type = grid[y + 1][x][0]
            # Check the type of the current tile
            current_tile_type = grid[y][x][0]
            # Define which types are considered walkable/supporting
            valid_ground_types = ["ground", "hill"]
            # Final condition
            if tile_below_type in valid_ground_types and current_tile_type == "empty":
                valid_positions.append((x,y))
    #valid_positions should now contain all the coordinates where we can place enemies and coins, for example: [(23, 18), (45, 20), (67, 16), (89, 30), ...]
    
    # 3. ENEMIES + COINS
    for c in chunks:
        if c[0] == "enemy" and valid_positions:
            x,y = random.choice(valid_positions)
            place(grid, x, y, "enemy")

        if c[0] == "coin":            
            x = c[1]
            y = c[2]
            n = c[3]
            for i in range(n):
                place(grid, x+i, y, "coin")

    return [[grid[y][x][0] for x in range(COLS)] for y in range(ROWS)]

# ==============================
# PRIORITY PLACEMENT
# ==============================
# When placing elements on the grid, we check the current element and its priority.
# If the new element has a higher priority, it replaces the existing one.
# This allows us to resolve conflicts when multiple chunks try to place something in the same location,
# ensuring that more important elements (like gaps) can override less important ones (like coins).
# The place function handles this logic, taking into account the type of element being placed and its priority.
def place(grid, x, y, t, force=False):
    if not (0 <= x < COLS and 0 <= y < ROWS): return

    current, pr = grid[y][x]

    if force or PRIORITY.get(t,0) >= pr:
        grid[y][x] = (t, PRIORITY.get(t,0))

# ==============================
# FITNESS (paper)
# ==============================
# The fitness function evaluates the generated level based on two criteria:
# 1. fp: how close the chromosome length is to the desired length (CHROM_LEN).
# 2. fc: how many holes (empty spaces on the ground) are present, 
# which serves as a proxy for playability (too many holes would make the level unplayable).
# The fitness is calculated as a weighted combination of these two factors, 
# with fp contributing 70% and fc contributing 30% to the final fitness score.    

def fitness(chrom):
    grid = build_level(chrom)

    # fp
    fp = abs(len(chrom)-CHROM_LEN)/CHROM_LEN

    # fc (overlaps approximated via empty holes + unreachable)
    holes = 0

    for x in range(COLS):
        if grid[ROWS - 1][x] == "empty":
            holes += 1
    fc = holes / COLS

    return 1 - (0.7*fp + 0.3*fc)

# ==============================
# EVOLUTION
# ==============================
#  The evolution process follows a standard genetic algorithm approach:
# 1. Create an initial population of random chromosomes.
# 2. For a number of generations, perform selection, crossover, and mutation to create a new population.
# 3. After the evolution loop, select the best chromosome and build the corresponding level to display.
# The create, mutate, crossover, and select functions implement the genetic operators,
# while the evolve function orchestrates the overall evolutionary process.
# The tournament selection method is used to select parents based on their fitness,
# ensuring that better-performing chromosomes have a higher chance of being selected for reproduction.  
def create():
    chromosome = []
    for i in range(CHROM_LEN):
        gene = random.randint(0, 255)
        chromosome.append(gene)
    return chromosome

def mutate(c):
    for i in range(len(c)):
        if random.random()<0.1:
            c[i]=random.randint(0,255)


def crossover(a,b):
    p=random.randint(1,len(a)-1)
    return a[:p]+b[p:]


def select(pop):
    a,b=random.sample(pop,2)
    return a if fitness(a)>fitness(b) else b

# The evolve function orchestrates the overall evolutionary process, creating an initial population,
# performing selection, crossover, and mutation for a specified number of generations,
# and finally selecting the best chromosome to build and return the corresponding level grid.
def evolve():
    pop = []
    for i in range(POP_SIZE):
        individual = create()
        pop.append(individual)

    for _ in range(GENERATIONS):
        new=[]
        for _ in range(POP_SIZE):
            p1=select(pop)
            p2=select(pop)
            c=crossover(p1,p2)
            mutate(c)
            new.append(c)
        pop=new

    best = None
    best_score = None

    for individual in pop:
        score = fitness(individual)

        if best is None or score > best_score:
            best = individual
            best_score = score
    return build_level(best)

# ==============================
# DRAW
# ==============================
# The draw function uses Pygame to visualize the generated level on the screen.
# It iterates through the grid and draws different colored rectangles or circles 
# based on the type of element present (ground, hill, enemy, coin).
# The main function runs the evolution process and displays the best level using Pygame, 
# allowing the user to generate new levels by pressing the spacebar.
def draw(grid):
    screen.fill(SKY)
    for y in range(ROWS):
        for x in range(COLS):
            t=grid[y][x]
            r=pygame.Rect(x*TILE,y*TILE,TILE,TILE)
            if t=="ground": pygame.draw.rect(screen,GROUND,r)
            elif t=="hill": pygame.draw.rect(screen,HILL,r)
            elif t=="enemy": pygame.draw.rect(screen,ENEMY,r)
            elif t=="coin": pygame.draw.circle(screen,COIN,r.center,TILE//3)

# ==============================
# MAIN
# ==============================
# The main function runs the evolution process and displays the best level using Pygame, 
# allowing the user to generate new levels by pressing the spacebar.
# The game loop handles events and updates the display at a fixed frame rate, 
# ensuring smooth visualization of the generated levels.
# The user can quit the program by closing the window, and new levels can be generated on demand,
#  providing an interactive way to explore the evolved content.
#
def main():
    grid=evolve()
    run=True
    while run:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: run=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_SPACE:
                grid=evolve()

        draw(grid)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__=="__main__": main()
