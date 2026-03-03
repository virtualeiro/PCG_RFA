import pygame
import random
from collections import deque

# ------------------------
CELL_SIZE = 5
ROOM_SIZE = 50
ROWS, COLS = 3, 3
FPS = 30

ROCK_PROB = 60
CA_STEPS = 2
T_THRESHOLD = 5

NEIGHBORS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

# Colors
ROCK_COLOR = (50,50,50)
EMPTY_COLOR = (200,200,200)
WALL_COLOR = (255,50,20)

# ------------------------
# Generate a single room using CA
def generate_room(size, rock_prob=ROCK_PROB, steps=CA_STEPS, T=T_THRESHOLD):
    grid = [[0 for _ in range(size)] for _ in range(size)]
    # initial rocks
    for y in range(size):
        for x in range(size):
            if random.randint(0,99)<rock_prob:
                grid[y][x]=1
    # CA iterations
    for _ in range(steps):
        new_grid=[[0]*size for _ in range(size)]
        for y in range(size):
            for x in range(size):
                count=sum(grid[y+dy][x+dx] for dx,dy in NEIGHBORS if 0<=x+dx<size and 0<=y+dy<size)
                new_grid[y][x]=1 if count>=T else 0
        grid=new_grid
    # mark walls
    wall_grid=[[0]*size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            if grid[y][x]==1:
                for dx,dy in NEIGHBORS:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<size and 0<=ny<size and grid[ny][nx]==0:
                        wall_grid[y][x]=2
                        break
                if wall_grid[y][x]!=2:
                    wall_grid[y][x]=1
    return wall_grid

# ------------------------
# Largest empty region
def largest_empty(grid):
    size=len(grid)
    visited=[[False]*size for _ in range(size)]
    max_region=[]
    for y in range(size):
        for x in range(size):
            if grid[y][x]==0 and not visited[y][x]:
                q=deque()
                q.append((x,y))
                region=[]
                visited[y][x]=True
                while q:
                    cx,cy=q.popleft()
                    region.append((cx,cy))
                    for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx,ny=cx+dx,cy+dy
                        if 0<=nx<size and 0<=ny<size and grid[ny][nx]==0 and not visited[ny][nx]:
                            visited[ny][nx]=True
                            q.append((nx,ny))
                if len(region)>len(max_region):
                    max_region=region
    return max_region

# ------------------------
# Drill simple straight tunnel
def drill_tunnel(grid1, grid2):
    empty1=largest_empty(grid1)
    empty2=largest_empty(grid2)
    if not empty1 or not empty2:
        return
    x1,y1=random.choice(empty1)
    x2,y2=random.choice(empty2)
    # horizontal then vertical
    for x in range(min(x1,x2), max(x1,x2)+1):
        if 0<=y1<ROOM_SIZE and 0<=x<ROOM_SIZE:
            grid1[y1][x]=0
        if 0<=y2<ROOM_SIZE and 0<=x<ROOM_SIZE:
            grid2[y2][x]=0
    for y in range(min(y1,y2), max(y1,y2)+1):
        if 0<=y<ROOM_SIZE and 0<=x2<ROOM_SIZE:
            grid1[y][x2]=0
        if 0<=y<ROOM_SIZE and 0<=x2<ROOM_SIZE:
            grid2[y][y2]=0

# ------------------------
# Apply CA to a large combined grid
def apply_ca(grid, steps=2, T=5):
    H=len(grid)
    W=len(grid[0])
    for _ in range(steps):
        new_grid=[[0]*W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                count=0
                for dx,dy in NEIGHBORS:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<W and 0<=ny<H and grid[ny][nx]!=0:
                        count+=1
                new_grid[y][x]=1 if count>=T else 0
        grid=new_grid
    # mark walls
    for y in range(H):
        for x in range(W):
            if grid[y][x]==1:
                for dx,dy in NEIGHBORS:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<W and 0<=ny<H and grid[ny][nx]==0:
                        grid[y][x]=2
                        break
    return grid

# ------------------------
# Draw dungeon
def draw(screen,dungeon):
    screen.fill((0,0,0))
    H=len(dungeon)
    W=len(dungeon[0])
    for y in range(H):
        for x in range(W):
            val=dungeon[y][x]
            color=EMPTY_COLOR if val==0 else WALL_COLOR if val==2 else ROCK_COLOR
            pygame.draw.rect(screen,color,(x*CELL_SIZE,y*CELL_SIZE,CELL_SIZE,CELL_SIZE))
    pygame.display.flip()

# ------------------------
# Main
def main():
    pygame.init()
    screen = pygame.display.set_mode((COLS*ROOM_SIZE*CELL_SIZE, ROWS*ROOM_SIZE*CELL_SIZE))
    pygame.display.set_caption("CA Dungeon with Connections")
    clock = pygame.time.Clock()

    def generate_dungeon():
        # Step 1: generate rooms
        dungeon_rooms = [[generate_room(ROOM_SIZE) for _ in range(COLS)] for _ in range(ROWS)]

        # Step 2: connect neighbors
        for y in range(ROWS):
            for x in range(COLS):
                if x < COLS-1:
                    drill_tunnel(dungeon_rooms[y][x], dungeon_rooms[y][x+1])
                if y < ROWS-1:
                    drill_tunnel(dungeon_rooms[y][x], dungeon_rooms[y+1][x])

        # Step 3: combine rooms into a single grid
        H = ROWS * ROOM_SIZE
        W = COLS * ROOM_SIZE
        combined = [[0]*W for _ in range(H)]
        for ry,row in enumerate(dungeon_rooms):
            for rx,room in enumerate(row):
                for y in range(ROOM_SIZE):
                    for x in range(ROOM_SIZE):
                        combined[ry*ROOM_SIZE+y][rx*ROOM_SIZE+x] = room[y][x]

        # Step 4: apply 2 more CA iterations to smooth
        combined = apply_ca(combined, steps=2, T=T_THRESHOLD)
        return combined

    dungeon = generate_dungeon()

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # quit on ESC
                elif event.key == pygame.K_SPACE:
                    dungeon = generate_dungeon()  # regenerate on SPACE
        draw(screen, dungeon)

    pygame.quit()

if __name__=="__main__":
    main()