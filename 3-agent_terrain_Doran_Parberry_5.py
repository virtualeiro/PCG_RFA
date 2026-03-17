import pygame
import random
import math

# -------------------- CONFIGURATION --------------------
SCREEN_SIZE = 600
MAP_SIZE = 100  # grid size
CELL_SIZE = SCREEN_SIZE // MAP_SIZE
SEA_LEVEL = 0.5  # normalized height
AGENT_LIFETIME = 500  # number of steps an agent can take
NUM_COASTLINE_AGENTS = 5  # initial number of coastline agents
#--------------------- SMOOTHING AGENTS --------------------
NUM_SMOOTHING_AGENTS = 10  # number of smoothing agents
SMOOTHING_VISITS = 5  # number of times a smoothing agent revisits a point
# -------------------- BEACH AGENTS --------------------
NUM_BEACH_AGENTS = 8
BEACH_AGENT_STEPS = 400

BEACH_MAX_ALTITUDE = SEA_LEVEL + 0.15   # agent works only below this altitude
BEACH_DEPTH_LIMIT = 0.25                # how deep inland flattening allowed
BEACH_HEIGHT_RANGE = (SEA_LEVEL - 0.02, SEA_LEVEL + 0.04)
#Flat tropical beach 
#BEACH_HEIGHT_RANGE = (SEA_LEVEL - 0.01, SEA_LEVEL + 0.01)
#BEACH_DEPTH_LIMIT = 0.1
#Rocky bumpy beach
#BEACH_HEIGHT_RANGE = (SEA_LEVEL - 0.05, SEA_LEVEL + 0.08)
#BEACH_DEPTH_LIMIT = 0.3
#Wide Mediterranean beach
#NUM_BEACH_AGENTS = 15
#BEACH_AGENT_STEPS = 800

# -------------------- MOUNTAIN AGENTS --------------------
NUM_MOUNTAIN_AGENTS = 6
MOUNTAIN_AGENT_STEPS = 300

MOUNTAIN_MIN_ALTITUDE = SEA_LEVEL + 0.095   # mountains only above this
MOUNTAIN_MAX_HEIGHT = 1.0                 # absolute cap
MOUNTAIN_HEIGHT_INCREMENT = (0.2, 0.35)
MOUNTAIN_SLOPE_DROP = (0.01, 0.02)
MOUNTAIN_WIDTH = 10
MOUNTAIN_MAX_HEIGHT = 1.0
MOUNTAIN_WIDTH = 8                        # half-width of ridge
MOUNTAIN_SLOPE_DROP = (0.01, 0.06)        # how quickly slope falls
MOUNTAIN_HEIGHT_INCREMENT = (0.15, 0.25)  # ridge elevation amount
FOOTHILL_LENGTH = 5
FOOTHILL_FREQUENCY = 0.1                  # probability per step
#Alpine jagged peaks
#MOUNTAIN_SLOPE_DROP = (0.05, 0.1)
#MOUNTAIN_HEIGHT_INCREMENT = (0.1, 0.2)
#MOUNTAIN_WIDTH = 4
#Rolling hills
#MOUNTAIN_WIDTH = 10
#MOUNTAIN_SLOPE_DROP = (0.01, 0.03)
#MOUNTAIN_HEIGHT_INCREMENT = (0.03, 0.07)
#Rugged terrain with foothills
#FOOTHILL_FREQUENCY = 0.3
#FOOTHILL_LENGTH = 8
# -------------------- RIVER AGENTS --------------------
NUM_RIVER_AGENTS = 5
RIVER_MAX_ATTEMPTS = 5

RIVER_INITIAL_WIDTH = 1
RIVER_WIDEN_FREQUENCY = 0.01
RIVER_SLOPE = 0.015
RIVER_MIN_LENGTH = 20
RIVER_STEPS = 3
RIVER_MAX_WIDTH = 1


# -------------------- PEAK SETTINGS --------------------
HILL_LEVEL = SEA_LEVEL + 0.12
MOUNTAIN_LEVEL = SEA_LEVEL + 0.0
PEAK_LEVEL = SEA_LEVEL + 0.15
SNOW_LEVEL = SEA_LEVEL + 0.30



# Colors
WATER_COLOR = (0, 0, 128)
LAND_COLOR = (20, 139, 34)
COAST_COLOR = (210, 180, 140)
PEAK_COLOR = (0, 84, 8)   # light gray (rock)
SNOW_COLOR = (1, 61, 7)   # snow caps
RIVER_COLOR = (30, 144, 255)  # bright river blue

# -------------------- ENVIRONMENT --------------------
class Terrain:
    def __init__(self, size):
        self.size = size
        # initialize map under sea level
        level = SEA_LEVEL - 0.1
        self.height_map = []
        self.river_map = [[False for _ in range(size)] for _ in range(size)]
        for y in range(size):                            # rows
            row = []
            for x in range(size):                        # columns
                row.append(level)
            self.height_map.append(row)
            
    def elevate_point(self, x, y, amount=0.1):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.height_map[y][x] += amount
            if self.height_map[y][x] > 1.0:
                self.height_map[y][x] = 1.0

    def get_height(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.height_map[y][x]
        return SEA_LEVEL - 0.1

    def set_height(self, x, y, value):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.height_map[y][x] = max(0.0, min(1.0, value))

    def draw(self, screen):
        for y in range(self.size):
            for x in range(self.size):
                h = self.height_map[y][x]

                if self.river_map[y][x]:
                    color = RIVER_COLOR
                elif h < SEA_LEVEL:
                    color = WATER_COLOR
                elif h < SEA_LEVEL + 0.05:
                    color = COAST_COLOR
                elif h < PEAK_LEVEL:
                    color = LAND_COLOR
                elif h < SNOW_LEVEL:
                    color = PEAK_COLOR
                else:
                    color = SNOW_COLOR

                pygame.draw.rect(
                    screen,
                    color,
                    (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                )

# -------------------- AGENT --------------------
#sense a local 3×3 patch, 
# choose a valid exit cell based on a simple potential‐field heuristic,
# elevate it, move there, 
# and repeat until the agent runs out of life.
#------------------------------------------------
class CoastlineAgent:
    def __init__(self, terrain, x, y, direction=(1,0), lifespanTokens=AGENT_LIFETIME):
        self.terrain = terrain
        self.x = x #current grid x
        self.y = y #current grid y
        self.dir = direction # direction (dx, dy)
        self.lifespanTokens = lifespanTokens # number of steps agent can take before becoming inactive

    def step(self):# returns False if agent is inactive    
        if self.lifespanTokens <= 0:
            return False  # agent inactive

        # generate attractor and repulsor
        #two random points are generated by taking the agent’s current position
        #and adding a uniform offset in [-5,5] in both coordinates.
        #the idea is that the agent will try to move toward the attractor 
        # and away from the repulsor
        attractor = (self.x + random.randint(-5,5), self.y + random.randint(-5,5))
        repulsor = (self.x + random.randint(-5,5), self.y + random.randint(-5,5))

        #look around 
        # find candidate points in a 3x3 neighborhood      
        #examines the 3×3 neighborhood centred on its current location.
        #any neighbour whose height is still below SEA_LEVEL + 0.05 (i.e. water or very shallow coast)
        #is added to a candidates list.
        candidates = []
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < self.terrain.size and 0 <= ny < self.terrain.size:
                    if self.terrain.get_height(nx, ny) < SEA_LEVEL + 0.05:
                        candidates.append((nx, ny))
        #no candidates?
        #if the list is empty the agent simply walks one step in its current dir,
        # decrements lifespanTokens, and returns. 
        # it will keep going straight 
        # until it finds some low‑height cell, 
        # or until its tokens run out.
        if not candidates:
            # move in direction until suitable point found
            self.x += self.dir[0]
            self.y += self.dir[1]
            self.lifespanTokens -= 1
            return True

        # score candidates based on attractor/repulsor
        #a neighbour that is closer to the attractor 
        # and farther from the repulsor gets a higher score.
        def score(point):
            ax, ay = attractor
            rx, ry = repulsor
            px, py = point
            attract_dist = math.hypot(px - ax, py - ay)
            repulse_dist = math.hypot(px - rx, py - ry)
            return repulse_dist - attract_dist  # closer to attractor, higher score

        #move and raise terrain
        #the candidate with the maximum score is chosen, 
        # the agent’s x,y are updated to that cell
        #terrain.elevate_point() is called to bump the height there
        #finally the token count is decremented
        best_point = max(candidates, key=score)
        bx, by = best_point
        self.terrain.elevate_point(bx, by)
        self.x, self.y = bx, by
        self.lifespanTokens -= 1
        return True

#-------------------- SMOOTHING AGENT --------------------
# After the coastline agents have done their work,
# we can add some smoothing agents that 
# randomly walk around and average the heights of their neighbors 
# to create a more natural terrain.
#----
#meanders around the map and, 
# every time it lands on a cell, 
# replaces that cell’s height 
# with the average of the surrounding heights
#----

class SmoothingAgent:
    def __init__(self, terrain, x, y, visits=SMOOTHING_VISITS):
        self.terrain = terrain
        self.x = x
        self.y = y
        self.visits_remaining = visits

    def step(self):
        if self.visits_remaining <= 0:
            return False

        # move randomly
        self.x += random.choice([-1,0,1])
        self.y += random.choice([-1,0,1])
        self.x = max(0, min(self.terrain.size-1, self.x))
        self.y = max(0, min(self.terrain.size-1, self.y))

        # smooth current point
        neighbors = []

        # four orthogonal neighbors
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx = self.x + dx
            ny = self.y + dy
            neighbors.append(self.terrain.get_height(nx, ny))

        # four points behind those (2 steps away)
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            nx, ny = self.x + dx, self.y + dy
            neighbors.append(self.terrain.get_height(nx, ny))
        avg_height = (self.terrain.get_height(self.x, self.y)*2 + sum(neighbors)) / (len(neighbors)+2)
        #avg_height = sum(neighbors) / len(neighbors)
        self.terrain.set_height(self.x, self.y, avg_height)

        self.visits_remaining -= 1
        return True

# -------------------- BEACH AGENT --------------------
#When the coast/smoothing phase finishes the map consists of 
# water at ~0.5 and 
# a thin rim of coast at around SEA_LEVEL+0.05.
# the beach agents will only operate in this narrow band
class BeachAgent:
    def __init__(self, terrain, x, y,
                 steps=BEACH_AGENT_STEPS,
                 max_altitude=BEACH_MAX_ALTITUDE,
                 depth_limit=BEACH_DEPTH_LIMIT,
                 height_range=BEACH_HEIGHT_RANGE):

        self.terrain = terrain
        self.x = x
        self.y = y
        self.steps_remaining = steps
        self.max_altitude = max_altitude
        self.depth_limit = depth_limit
        self.height_range = height_range

    def is_coastline(self, x, y):
        """Check if cell is coastline (land next to water)."""
        h = self.terrain.get_height(x, y)
        if h < SEA_LEVEL:
            return False

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if self.terrain.get_height(nx, ny) < SEA_LEVEL:
                return True
        return False

    def step(self):
        if self.steps_remaining <= 0:
            return False

        # random shoreline movement
        self.x += random.choice([-1,0,1])
        self.y += random.choice([-1,0,1])
        self.x = max(0, min(self.terrain.size-1, self.x))
        self.y = max(0, min(self.terrain.size-1, self.y))

        current_height = self.terrain.get_height(self.x, self.y)

        # only work near sea level and below max altitude
        if SEA_LEVEL <= current_height <= self.max_altitude:
            
            # depth constraint
            if current_height - SEA_LEVEL <= self.depth_limit:

                # assign new height from designer-defined range
                new_height = random.uniform(*self.height_range)

                # only lower terrain (never raise mountains)
                if new_height < current_height:
                    self.terrain.set_height(self.x, self.y, new_height)

        self.steps_remaining -= 1
        return True
    
# -------------------- MOUNTAIN AGENT --------------------
class MountainAgent:
    def __init__(self, terrain, x, y,
                 steps=MOUNTAIN_AGENT_STEPS):

        self.terrain = terrain
        self.x = x
        self.y = y
        self.steps_remaining = steps

        # random direction vector
        angle = random.uniform(0, 2 * math.pi)
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)

    def turn(self):
        """Random zigzag turn within ±45°."""
        angle = math.atan2(self.dy, self.dx)
        angle += random.uniform(-math.pi/4, math.pi/4)
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)

    def elevate_wedge(self):
        """Create V-shaped ridge perpendicular to movement."""

        slope_drop = random.uniform(*MOUNTAIN_SLOPE_DROP)
        height_boost = random.uniform(*MOUNTAIN_HEIGHT_INCREMENT)

        # perpendicular direction
        perp_x = -self.dy
        perp_y = self.dx

        for i in range(-MOUNTAIN_WIDTH, MOUNTAIN_WIDTH + 1):
            nx = int(self.x + perp_x * i)
            ny = int(self.y + perp_y * i)

            if 0 <= nx < self.terrain.size and 0 <= ny < self.terrain.size:
                base_height = self.terrain.get_height(nx, ny)

                if base_height >= MOUNTAIN_MIN_ALTITUDE:
                    distance = abs(i)
                    drop = slope_drop * distance
                    new_height = base_height + height_boost - drop
                    new_height = min(new_height, MOUNTAIN_MAX_HEIGHT)
                    self.terrain.set_height(nx, ny, new_height)

    def create_foothill(self):
        """Generate perpendicular foothill ridge."""
        perp_x = -self.dy
        perp_y = self.dx

        for i in range(1, FOOTHILL_LENGTH):
            nx = int(self.x + perp_x * i)
            ny = int(self.y + perp_y * i)

            if 0 <= nx < self.terrain.size and 0 <= ny < self.terrain.size:
                h = self.terrain.get_height(nx, ny)
                if h > MOUNTAIN_MIN_ALTITUDE:
                    drop = 0.02 * i
                    self.terrain.set_height(
                        nx, ny,
                        min(h + 0.03 - drop, MOUNTAIN_MAX_HEIGHT)
                    )

    def step(self):
        if self.steps_remaining <= 0:
            return False

        # move
        self.x += int(round(self.dx))
        self.y += int(round(self.dy))

        # clamp inside map
        self.x = max(0, min(self.terrain.size-1, self.x))
        self.y = max(0, min(self.terrain.size-1, self.y))

        current_height = self.terrain.get_height(self.x, self.y)

        # only operate above threshold
        if current_height > MOUNTAIN_MIN_ALTITUDE:
            self.elevate_wedge()
            # foothills occasionally
            if random.random() < FOOTHILL_FREQUENCY:
                self.create_foothill()

        # occasional zigzag turn
        if random.random() < 0.2:
            self.turn()

        self.steps_remaining -= 1
        return True
    
#-------------------- RIVER AGENT --------------------
# River agents are more complex. 
# They first search for a valid starting point on the coastline
#  and a valid ending point in the mountains. 
# Then they trace uphill to find a path to the mountain,
#  and once they reach it, 
# they switch to carving downhill toward the sea, 
# creating a riverbed along the way. 
#
class RiverAgent:
    def __init__(self, terrain):
        self.terrain = terrain
        self.path = []
        self.width = RIVER_INITIAL_WIDTH
        self.state = 'uphill'  # or 'downhill'
        self.valid = False
        self.start = None
        self.end = None
      
    def find_coastline_point(self):
        """Find a random point on the coastline."""
        attempts = 0
        while attempts < 100:
            x = random.randint(0, self.terrain.size - 1)
            y = random.randint(0, self.terrain.size - 1)
            h = self.terrain.get_height(x, y)
            
            # Check if on coastline
            if SEA_LEVEL <= h < SEA_LEVEL + 0.05:
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x + dx, y + dy
                    if self.terrain.get_height(nx, ny) < SEA_LEVEL:
                        return (x, y)
            attempts += 1
        return None

    def find_mountain_point(self):
        """Find a random point on the mountain ridge."""
        attempts = 0
        while attempts < 100:
            x = random.randint(0, self.terrain.size - 1)
            y = random.randint(0, self.terrain.size - 1)
            h = self.terrain.get_height(x, y)
            
            if h > MOUNTAIN_MIN_ALTITUDE + 0.1:
                return (x, y)
            attempts += 1
        return None
    
    def step_uphill(self):
            """Move uphill towards the mountain endpoint."""
            if not self.path:
                self.path.append(self.start)
            
            current = self.path[-1]
            
            # Check if reached mountain
            if current == self.end:
                self.state = 'downhill'
                return True
            
            # Find neighbor with highest elevation
            best_neighbor = None
            best_height = self.terrain.get_height(current[0], current[1])
            
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if 0 <= nx < self.terrain.size and 0 <= ny < self.terrain.size:
                    h = self.terrain.get_height(nx, ny)
                    if h > best_height and (nx, ny) not in self.path:
                        best_height = h
                        best_neighbor = (nx, ny)
            
            # Move uphill if found, otherwise step towards mountain
            if best_neighbor:
                self.path.append(best_neighbor)
            else:
                # Gradient towards mountain endpoint
                ex, ey = self.end
                cx, cy = current
                dx = 1 if ex > cx else (-1 if ex < cx else 0)
                dy = 1 if ey > cy else (-1 if ey < cy else 0)
                next_pos = (cx + dx, cy + dy)
                self.path.append(next_pos)
            
            return True
    
    def step_downhill(self):

        if not self.path:
            self.path.append(self.end)

        cx, cy = self.path[-1]
        current_height = self.terrain.get_height(cx, cy)

        # If already in sea → stop immediately
        if current_height <= SEA_LEVEL:
            self.state = 'finished'
            return False

        best_neighbor = None
        best_height = current_height

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < self.terrain.size and 0 <= ny < self.terrain.size:

                h = self.terrain.get_height(nx, ny)

                # Only consider neighbors that are LOWER
                if h < best_height:
                    best_height = h
                    best_neighbor = (nx, ny)

        if best_neighbor is None:
            self.state = 'finished'
            return False

        self.path.append(best_neighbor)

        # If we just stepped into sea → stop immediately
        if best_height <= SEA_LEVEL:
            self.state = 'finished'

        return True
    
    def initialize(self):
        """Step1> Initialize river endpoints."""
        self.start = self.find_coastline_point()
        self.end = self.find_mountain_point()
        self.valid = self.start is not None and self.end is not None
    
    def step(self):
            #  HARD STOP: if already in sea → never move again
            #if not self.path:
            #    return False
            #cx, cy = self.path[-1]
            #if self.terrain.get_height(cx, cy) <= SEA_LEVEL:
            #    self.state = 'finished'
            #    return False
            """Step 2 and 3 > Execute one step of the river agent."""
            if self.state == 'uphill':
                self.step_uphill()
            elif self.state == 'downhill':
                self.step_downhill()
                # Mark river on terrain
                for x, y in self.path:
                    if self.terrain.get_height(x, y) > SEA_LEVEL:
                        self.terrain.river_map[y][x] = True
                            
            return self.state != 'finished'

# -------------------- MAIN PROGRAM --------------------
#   
#
# The main program initializes the terrain and spawns agents in phases:
# 1. Coastline agents and smoothing agents run together until all coastline agents finish.
# 2. Once coastline agents are done, beach agents and mountain agents are spawned and run together.
# The main loop handles agent stepping, drawing the terrain, and user input for restarting or quitting.
#      
# ------------------------------------------------------ 
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Terrain Generation")
    clock = pygame.time.Clock()

    terrain = Terrain(MAP_SIZE)

    # Phase 1: Coastline & smoothing
    coastline_agents = []
    smoothing_agents = []
    beach_agents = []
    mountain_agents = []
    river_agents = []
    #------------------------------------------------------
    def make_CoastlineAgents(t):
        agents = []
        for _ in range(NUM_COASTLINE_AGENTS):
            edge = random.choice(['top','bottom','left','right'])
            if edge == 'top':
                x, y = random.randint(0, MAP_SIZE-1), 0
                dir = (0,1)
            elif edge == 'bottom':
                x, y = random.randint(0, MAP_SIZE-1), MAP_SIZE-1
                dir = (0,-1)
            elif edge == 'left':
                x, y = 0, random.randint(0, MAP_SIZE-1)
                dir = (1,0)
            else:
                x, y = MAP_SIZE-1, random.randint(0, MAP_SIZE-1)
                dir = (-1,0)
            agents.append(CoastlineAgent(t, x, y, dir))
        return agents
    #   ------------------------------------------------------ 
    def make_SmoothingAgents(t):
        agents = []
        for _ in range(NUM_SMOOTHING_AGENTS):
            x, y = random.randint(0, MAP_SIZE-1), random.randint(0, MAP_SIZE-1)
            agents.append(SmoothingAgent(t, x, y))
        return agents
    #------------------------------------------------------
    def make_BeachAgents(t):
        agents = []
        coastline_cells = []
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                h = t.get_height(x, y)
                if SEA_LEVEL <= h < SEA_LEVEL + 0.05:
                    coastline_cells.append((x, y))
        for _ in range(NUM_BEACH_AGENTS):
            if coastline_cells:
                x, y = random.choice(coastline_cells)
                agents.append(BeachAgent(t, x, y))
        return agents
    #------------------------------------------------------
    def make_MountainAgents(t):
        agents = []
        for _ in range(NUM_MOUNTAIN_AGENTS):
            x = random.randint(0, MAP_SIZE-1)
            y = random.randint(0, MAP_SIZE-1)
    #        if t.get_height(x, y) > MOUNTAIN_MIN_ALTITUDE:
            agents.append(MountainAgent(t, x, y))
        return agents
    #------------------------------------------------------
    def make_RiverAgents(t):
        agents = []
        for _ in range(NUM_RIVER_AGENTS):
            agent = RiverAgent(t)
            agent.initialize()
            if agent.valid:
                agents.append(agent)
        return agents

    #------------------------------------------------------         
    # INITIAL PHASE: spawn coastline and smoothing
    print("Coastline phase complete.")
    
    coastline_agents = make_CoastlineAgents(terrain)
    smoothing_agents = make_SmoothingAgents(terrain)

    phase = 0  # 0 = coast/smoothing, 1 = beach/mountain

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # restart
                    terrain = Terrain(MAP_SIZE)
                    coastline_agents = make_CoastlineAgents(terrain)
                    smoothing_agents = make_SmoothingAgents(terrain)
                    beach_agents = []
                    mountain_agents = []
                    phase = 0

        if phase == 0:
            # Coastline agents
            for agent in coastline_agents:
                agent.step()
            # Smoothing agents
            for agent in smoothing_agents:
                agent.step()

            # Check if all coastline agents are done
            if all(agent.lifespanTokens <= 0 for agent in coastline_agents):
                # spawn beach and mountain agents
                print("Spawning beach, mountain and river agents...")
                beach_agents = make_BeachAgents(terrain)
                mountain_agents = make_MountainAgents(terrain)
                phase = 1

        elif phase == 1:
            # Beach agents
            for agent in beach_agents:
                agent.step()
            # Mountain agents
            for agent in mountain_agents:
                agent.step()
             # Check if all beach and mountain agents are done
            if all(agent.steps_remaining <= 0 for agent in mountain_agents):
               river_agents = make_RiverAgents(terrain)
               phase = 2  

        elif phase == 2:
            for agent in river_agents:
                agent.step()       

        # Draw terrain
        terrain.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    # Print min/max for debug
    print(
        min(min(row) for row in terrain.height_map),
        max(max(row) for row in terrain.height_map)
    )
    pygame.quit()

if __name__ == "__main__":
    main()