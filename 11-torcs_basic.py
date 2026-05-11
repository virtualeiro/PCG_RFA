import pygame
import random
import math
import sys

# -----------------------------------
# SIMPLE SINGLE TRACK GENERATOR
# -----------------------------------

WIDTH, HEIGHT = 640, 640
NUM_POINTS = 10
TRACK_WIDTH = 50
TENSION = 0.35

BACKGROUND = (30, 30, 30)
ROAD_COLOR = (90, 90, 90)
BORDER_COLOR = (255, 255, 255)
CENTER_COLOR = (200, 200, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Procedural Race Track")

clock = pygame.time.Clock()


# -----------------------------------
# BEZIER CURVE
# -----------------------------------
def cubic_bezier(p0, p1, p2, p3, steps=24):
    points = []

    for i in range(steps + 1):
        t = i / steps

        x = (
            (1 - t) ** 3 * p0[0]
            + 3 * (1 - t) ** 2 * t * p1[0]
            + 3 * (1 - t) * t ** 2 * p2[0]
            + t ** 3 * p3[0]
        )

        y = (
            (1 - t) ** 3 * p0[1]
            + 3 * (1 - t) ** 2 * t * p1[1]
            + 3 * (1 - t) * t ** 2 * p2[1]
            + t ** 3 * p3[1]
        )

        points.append((x, y))

    return points


# -----------------------------------
# TRACK CLASS
# -----------------------------------
class Track:

    def __init__(self):
        self.points = self.generate_points()

    def generate_points(self):
        pts = []

        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        for i in range(NUM_POINTS):

            angle = (2 * math.pi / NUM_POINTS) * i

            radius = random.randint(150, 260)

            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            pts.append((x, y))

        return pts

    def compute_tangents(self):

        tangents = []

        n = len(self.points)

        for i in range(n):

            p_prev = self.points[i - 1]
            p_next = self.points[(i + 1) % n]

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

            p1 = (
                p0[0] + tangents[i][0],
                p0[1] + tangents[i][1]
            )

            j = (i + 1) % n

            p3 = self.points[j]

            p2 = (
                p3[0] - tangents[j][0],
                p3[1] - tangents[j][1]
            )

            curve = cubic_bezier(p0, p1, p2, p3)

            path.extend(curve)

        return path

    def compute_road_edges(self, path):

        left_edge = []
        right_edge = []

        for i in range(len(path)):

            p = path[i]
            p_next = path[(i + 1) % len(path)]

            dx = p_next[0] - p[0]
            dy = p_next[1] - p[1]

            length = math.hypot(dx, dy)

            if length == 0:
                continue

            dx /= length
            dy /= length

            nx = -dy
            ny = dx

            offset = TRACK_WIDTH / 2

            left = (
                p[0] + nx * offset,
                p[1] + ny * offset
            )

            right = (
                p[0] - nx * offset,
                p[1] - ny * offset
            )

            left_edge.append(left)
            right_edge.append(right)

        return left_edge, right_edge

    def draw(self, surface):

        path = self.get_smooth_path()

        left, right = self.compute_road_edges(path)

        if len(left) < 2:
            return

        road_polygon = left + right[::-1]

        # Road
        pygame.draw.polygon(surface, ROAD_COLOR, road_polygon)

        # Borders
        pygame.draw.lines(surface, BORDER_COLOR, True, left, 3)
        pygame.draw.lines(surface, BORDER_COLOR, True, right, 3)

        # Center line
        pygame.draw.lines(surface, CENTER_COLOR, True, path, 1)

        # Optional control points
        for p in self.points:
            pygame.draw.circle(surface, (255, 80, 80), (int(p[0]), int(p[1])), 5)


# -----------------------------------
# CREATE TRACK
# -----------------------------------
track = Track()


# -----------------------------------
# MAIN LOOP
# -----------------------------------
running = True

while running:

    screen.fill(BACKGROUND)

    track.draw(screen)

    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            # Press SPACE to generate a new track
            if event.key == pygame.K_SPACE:
                track = Track()

    clock.tick(60)

pygame.quit()
sys.exit()