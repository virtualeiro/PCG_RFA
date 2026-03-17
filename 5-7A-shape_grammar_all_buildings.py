import pygame
import random
#---------- Shape Grammar Building Generator ----------
# This code implements a simple shape grammar system to generate a cityscape 
# with buildings of varying heights, floor counts, and roof types. 
# Each building is randomly sized and placed, split into floors, 
# and decorated with windows and a roof
# The city is regenerated when the user presses the spacebar.
#---------- Shape Grammar Building Generator ----------
#Rules:
#1- Split vertically → floors
#2- Building → stack of smaller rectangles (floors)
#3- Add windows
#4- Floor → Floor + grid of windows
#5- Roof variation
#6- Building → FlatRoof | TriangleRoof
#7- Press SPACE to generate a new building.
#--------------------------------------------------------
pygame.init()

WIDTH = 900
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shape Grammar Building Generator")

clock = pygame.time.Clock()


# ---------- Shape Grammar Classes ----------

class Building:

    def __init__(self, x, width, height):
        self.x = x
        self.width = width
        self.height = height

        self.floors = []
        self.roof_type = random.choice(["flat", "triangle"])

        self.apply_rules()

    # Rule 1: Split vertically into floors
    def apply_rules(self):

        floor_count = random.randint(3, 8)
        floor_height = self.height // floor_count

        for i in range(floor_count):

            y = HEIGHT - (i + 1) * floor_height
            floor = Floor(self.x, y, self.width, floor_height)

            self.floors.append(floor)

    def draw(self, surface):

        for f in self.floors:
            f.draw(surface)

        # Rule 3: Roof variation
        if self.roof_type == "flat":

            pygame.draw.rect(
                surface,
                (70, 70, 70),
                (self.x, HEIGHT - self.height - 10, self.width, 10)
            )

        else:

            top = HEIGHT - self.height

            points = [
                (self.x, top),
                (self.x + self.width / 2, top - 30),
                (self.x + self.width, top)
            ]

            pygame.draw.polygon(surface, (120, 60, 60), points)


class Floor:

    def __init__(self, x, y, width, height):

        self.rect = pygame.Rect(x, y, width, height)

        self.windows = []
        self.generate_windows()

    # Rule 2: Add windows in grid
    def generate_windows(self):

        cols = random.randint(2, 5)
        rows = 1

        margin = 10

        w = (self.rect.width - margin * (cols + 1)) / cols
        h = self.rect.height / 2

        for c in range(cols):

            wx = self.rect.x + margin + c * (w + margin)
            wy = self.rect.y + self.rect.height / 4

            window = pygame.Rect(wx, wy, w, h)
            self.windows.append(window)

    def draw(self, surface):

        pygame.draw.rect(surface, (180, 180, 200), self.rect)

        for w in self.windows:
            pygame.draw.rect(surface, (255, 230, 120), w)


# ---------- Scene ----------

def generate_city():

    buildings = []

    x = 50

    while x < WIDTH - 100:

        w = random.randint(80, 140)
        h = random.randint(200, 400)

        b = Building(x, w, h)
        buildings.append(b)

        x += w + random.randint(20, 60)

    return buildings


buildings = generate_city()


# ---------- Main Loop ----------

running = True

while running:

    screen.fill((30, 30, 40))

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:
                buildings = generate_city()

    for b in buildings:
        b.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()