import pygame
import random
import sys

# -------------------------
# CONFIG
# -------------------------
TILE_SIZE = 16
GRID_WIDTH = 60
GRID_HEIGHT = 40
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE
TARGET_FILL = 0.30 #Stop when 30% of the dungeon has been dug.
FPS = 10

WALL_COLOR = (30, 30, 30)
FLOOR_COLOR = (170, 170, 170)
AGENT_COLOR = (220, 40, 40)
BG_COLOR = (10, 10, 10)


class BlindDigger:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [["#" for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        self.x = random.randint(1, GRID_WIDTH - 2)
        self.y = random.randint(1, GRID_HEIGHT - 2)

        self.directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        self.direction = random.choice(self.directions)

        self.PC = 5  # chance change direction
        self.PR = 5  # chance add room
        self.floor_count = 0
        self.target_fill = int(GRID_WIDTH * GRID_HEIGHT * TARGET_FILL)

    def in_bounds(self, x, y):
        return 1 <= x < GRID_WIDTH - 1 and 1 <= y < GRID_HEIGHT - 1

    def dig_tile(self, x, y):
        if self.grid[y][x] == "#":
            self.grid[y][x] = "."
            self.floor_count += 1

    def dig_room(self, cx, cy):
        w = random.randint(3, 7)
        h = random.randint(3, 7)

        start_x = cx - w // 2
        start_y = cy - h // 2

        for y in range(start_y, start_y + h):
            for x in range(start_x, start_x + w):
                if self.in_bounds(x, y):
                    self.dig_tile(x, y)

    def step(self):
        if self.floor_count >= self.target_fill:
            return

        # Dig current tile
        self.dig_tile(self.x, self.y)

        # Move
        dx, dy = self.direction
        new_x = self.x + dx
        new_y = self.y + dy

        if self.in_bounds(new_x, new_y):
            self.x, self.y = new_x, new_y
        else:
            self.direction = random.choice(self.directions)
            return

        # Roll for direction change
        NC = random.randint(0, 100)
        if NC < self.PC:
            self.direction = random.choice(self.directions)
            self.PC = 0
        else:
            self.PC += 5

        # Roll for room placement
        NR = random.randint(0, 100)
        if NR < self.PR:
            self.dig_room(self.x, self.y)
            self.PR = 0
        else:
            self.PR += 5


def draw(screen, digger):
    screen.fill(BG_COLOR)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            if digger.grid[y][x] == "#":
                pygame.draw.rect(screen, WALL_COLOR, rect)
            else:
                pygame.draw.rect(screen, FLOOR_COLOR, rect)

    # Draw agent in red
    agent_rect = pygame.Rect(
        digger.x * TILE_SIZE,
        digger.y * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE
    )
    pygame.draw.rect(screen, AGENT_COLOR, agent_rect)

    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Blind Digger Dungeon Generator")
    clock = pygame.time.Clock()

    digger = BlindDigger()

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    digger.reset()

        digger.step()
        draw(screen, digger)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()