from statistics import mean

import pygame
import random
import math
import sys
import time
"""Possible questins>
What metrics would you design to evaluate “good track generation”?
How would you combine multiple metrics into a single fitness score?
Should evaluation prioritize human perception, AI performance, or geometric properties?
What is missing from the current evaluation system?

Can a track be considered “good” if only one type of agent performs well on it?
How does the agent shape what we perceive as a “good” generated track?
Define 3 metrics to evaluate track quality. Implement them.

What does the agent-s lap time actually measure: track quality, AI skill, or both?
How sensitive is performance to the lookahead distance parameter?
What happens to evaluation if the agent is too strong or too weak?
What would you define as a failure case of generation in this system?
Would increasing NUM_POINTS improve or reduce reliability?
"""
# =========================================================
# CONFIG
# =========================================================

WIDTH, HEIGHT = 640, 640

NUM_POINTS = 10
TRACK_WIDTH = 50
TENSION = 0.35

BACKGROUND = (30, 30, 30)
ROAD_COLOR = (90, 90, 90)
BORDER_COLOR = (255, 255, 255)
CENTER_COLOR = (220, 220, 0)

AGENT_COLOR = (255, 80, 80)

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stable Racing AI")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# =========================================================
# ANGLE UTILS
# =========================================================

def angle_difference(a, b):
    return math.atan2(
        math.sin(a - b),
        math.cos(a - b)
    )

# =========================================================
# BEZIER
# =========================================================

def cubic_bezier(p0, p1, p2, p3, steps=24):

    points = []

    for i in range(steps + 1):

        t = i / steps

        x = (
            (1 - t) ** 3 * p0[0]
            + 3 * (1 - t) ** 2 * t * p1[0]
            + 3 * (1 - t) * t**2 * p2[0]
            + t**3 * p3[0]
        )

        y = (
            (1 - t) ** 3 * p0[1]
            + 3 * (1 - t) ** 2 * t * p1[1]
            + 3 * (1 - t) * t**2 * p2[1]
            + t**3 * p3[1]
        )

        points.append((x, y))

    return points

# =========================================================
# TRACK
# =========================================================

class Track:

    def __init__(self):

        self.points = self.generate_points()
        self.path = self.get_smooth_path()

    def generate_points(self):

        pts = []

        cx = WIDTH // 2
        cy = HEIGHT // 2

        for i in range(NUM_POINTS):

            angle = (2 * math.pi / NUM_POINTS) * i

            radius = random.randint(150, 240)

            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

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

            curve = cubic_bezier(
                p0,
                p1,
                p2,
                p3
            )

            path.extend(curve)

        return path

    def compute_road_edges(self):

        left = []
        right = []

        for i in range(len(self.path)):

            p = self.path[i]
            p_next = self.path[
                (i + 1) % len(self.path)
            ]

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

            left.append((
                p[0] + nx * offset,
                p[1] + ny * offset
            ))

            right.append((
                p[0] - nx * offset,
                p[1] - ny * offset
            ))

        return left, right

    def draw(self, surface):

        left, right = self.compute_road_edges()

        polygon = left + right[::-1]

        pygame.draw.polygon(
            surface,
            ROAD_COLOR,
            polygon
        )

        pygame.draw.lines(
            surface,
            BORDER_COLOR,
            True,
            left,
            3
        )

        pygame.draw.lines(
            surface,
            BORDER_COLOR,
            True,
            right,
            3
        )

        pygame.draw.lines(
            surface,
            CENTER_COLOR,
            True,
            self.path,
            1
        )

# =========================================================
# AI AGENT
# =========================================================

class AIAgent:

    def __init__(self, track):

        self.track = track

        self.path_index = 0

        self.x, self.y = track.path[0]

        next_pt = track.path[5]

        self.angle = math.atan2(
            next_pt[1] - self.y,
            next_pt[0] - self.x
        )

        self.radius = 8

        self.speed = 2.5

        self.max_speed = 4.5
        self.min_speed = 1.5

        self.turn_smoothing = 0.12

        self.lap_start_time = time.time()

        self.lap_times = []

        self.steering_history = []
        self.speed_history = []
        self.deviation_history = []

    def update(self):

        path = self.track.path

        # =================================================
        # FOLLOW LOCAL TRACK TANGENT
        # =================================================

        look = get_lookahead_point(
        path,
        self.path_index,
        distance=50
        )

        desired_angle = math.atan2(
            look[1] - self.y,
            look[0] - self.x
        )

        angle_diff = angle_difference(
            desired_angle,
            self.angle
        )

        # =================================================
        # FUTURE CURVE LOOKAHEAD
        # =================================================

        future_index = (
            self.path_index + 25
        ) % len(path)

        future_a = path[future_index]

        future_b = path[
            (future_index + 1)
            % len(path)
        ]

        future_dx = (
            future_b[0] - future_a[0]
        )

        future_dy = (
            future_b[1] - future_a[1]
        )

        future_angle = math.atan2(
            future_dy,
            future_dx
        )

        future_diff = angle_difference(
            future_angle,
            desired_angle
        )

        curve_strength = abs(future_diff)

        # =================================================
        # SPEED CONTROL
        # =================================================

        target_speed = (
            self.max_speed
            - curve_strength * 14
        )

        target_speed = max(
            self.min_speed,
            min(
                self.max_speed,
                target_speed
            )
        )

        # braking stronger than acceleration
        if target_speed < self.speed:

            self.speed += (
                target_speed - self.speed
            ) * 0.2

        else:

            self.speed += (
                target_speed - self.speed
            ) * 0.03

        # =================================================
        # STEERING
        # =================================================

        steering = (
            angle_diff
            * self.turn_smoothing
        )

        max_steer = 0.08

        steering = max(
            -max_steer,
            min(max_steer, steering)
        )

        self.angle += steering
        self.steering_history.append(abs(steering))
        self.speed_history.append(self.speed)
        # =================================================
        # MOVE
        # =================================================

        self.x += (
            math.cos(self.angle)
            * self.speed
        )

        self.y += (
            math.sin(self.angle)
            * self.speed
        )

        # =================================================
        # ADVANCE PATH INDEX
        # =================================================

        target = path[self.path_index]

        distance = math.hypot(
            target[0] - self.x,
            target[1] - self.y
        )
        self.deviation_history.append(distance)

        if distance < 24:

            self.path_index += 1

            # LAP COMPLETE
            if self.path_index >= len(path):

                self.path_index = 0

                lap_time = (
                    time.time()
                    - self.lap_start_time
                )

                self.lap_times.append(
                    lap_time
                )

                self.lap_start_time = time.time()

                print(
                    f"Lap {len(self.lap_times)}:"
                    f" {lap_time:.2f}s"
                )

    def draw(self, surface):

        pygame.draw.circle(
            surface,
            AGENT_COLOR,
            (int(self.x), int(self.y)),
            self.radius
        )

        # direction line
        lx = (
            self.x
            + math.cos(self.angle) * 20
        )

        ly = (
            self.y
            + math.sin(self.angle) * 20
        )

        pygame.draw.line(
            surface,
            (255,255,255),
            (self.x, self.y),
            (lx, ly),
            2
        )

    def get_average_lap(self):

        if not self.lap_times:
            return 0

        return (
            sum(self.lap_times)
            / len(self.lap_times)
        )
    
def get_lookahead_point(path, index, distance=40):
        total = 0
        i = index

        while total < distance:
            p1 = path[i % len(path)]
            p2 = path[(i + 1) % len(path)]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            seg = math.hypot(dx, dy)
            if total + seg >= distance:
                t = (distance - total) / seg
                return (
                    p1[0] + dx * t,
                    p1[1] + dy * t
                )

            total += seg
            i += 1

        return path[index]

# =========================================================
# TRACK EVALUATOR
# =========================================================

class TrackEvaluator:

    def __init__(self, track, agent):

        self.track = track
        self.agent = agent

    # =====================================================
    # CURVATURE
    # =====================================================

    def compute_curvature(self):

        path = self.track.path

        curvatures = []
        # compute angle difference between consecutive segments
        # higher curvature means sharper turns, zero means straight line
        # curvature variance measures how much variety of turns there are
        for i in range(len(path)):
            # use previous and next points to compute local curvature
            # this is a simple approximation, not true curvature
            # we could also use more points for a smoother estimate
            p0 = path[i - 1] # previous point
            p1 = path[i] # current point
            p2 = path[(i + 1) % len(path)] # next point
            # compute angle of segments p0->p1 and p1->p2
            # meaningful curvature is only defined for points that are not too close together 
            # because atan2 returns unstable angles for very short segments
            #atan2 is a function that computes the angle of a vector (y, x) in radians, taking into account the correct quadrant
             
            a1 = math.atan2(
                p1[1] - p0[1],
                p1[0] - p0[0]
            )

            a2 = math.atan2(
                p2[1] - p1[1],
                p2[0] - p1[0]
            )

            diff = abs(angle_difference(a2, a1))

            curvatures.append(diff)

        avg_curvature = (
            sum(curvatures) / len(curvatures)
        )

        # Calculate squared differences
        squared_diffs = []

        for c in curvatures:
            # Calculate how far this point is from the average
            diff = c - avg_curvature            
            # Square it and add it to our list
            squared_diffs.append(diff ** 2)

        # Calculate the mean of those differences
        variance = sum(squared_diffs) / len(curvatures)

        return avg_curvature, variance

    # =====================================================
    # TRACK LENGTH
    # =====================================================

    def compute_track_length(self):

        path = self.track.path

        total = 0

        for i in range(len(path)):

            p1 = path[i]
            p2 = path[(i + 1) % len(path)]

            total += math.hypot(
                p2[0] - p1[0],
                p2[1] - p1[1]
            )

        return total

    # =====================================================
    # STEERING STABILITY
    # =====================================================

    def steering_stability(self):

        data = self.agent.steering_history

        if len(data) < 2:
            return 0

        mean = sum(data) / len(data)

        # 1. Calculate the squared distance from the mean for every point
        squared_differences = [(x - mean) ** 2 for x in data]

        # 2. The variance is the average of those squared distances
        variance = sum(squared_differences) / len(data)

        return variance

    # =====================================================
    # CENTERLINE DEVIATION
    # =====================================================

    def path_deviation(self):

        data = self.agent.deviation_history

        if not data:
            return 0

        return sum(data) / len(data)

    # =====================================================
    # AVERAGE SPEED
    # =====================================================

    def average_speed(self):

        data = self.agent.speed_history

        if not data:
            return 0

        return sum(data) / len(data)

    # =====================================================
    # SELF INTERSECTIONS
    # =====================================================
    # tracks with self intersections are usually unplayable and should be heavily penalized
    #This function checks if any two segments of the track intersect, 
    # which would indicate a self-intersection.
    #a1, a2 are the endpoints of one segment, and b1, b2 are the endpoints of another segment.
    def segment_intersect(
        self,
        a1, a2,
        b1, b2
    ): 
    #  It uses the concept of counter-clockwise (ccw) orientation to determine if two line segments intersect.
    #p1, p2, p3 are three points in 2D space. 
    #The function returns True if the points are arranged in a counter-clockwise order, and False otherwise.

    # The function checks if the line segments a1-a2 and b1-b2 intersect by comparing the orientations of the points.
    # If the segments intersect, it returns True; otherwise, it returns False.
    #This is done by checking if the points of one segment are on opposite sides of the other segment, and vice versa.
    #To accomplish this it uses the ccw function to determine the orientation of the points 
    # and checks if the orientations differ, which would indicate an intersection.
    #because if the segments intersect, the points of one segment will be on opposite sides of the other segment, and the orientations will differ.
    #e.g. 
    # if a1, b1, b2 are in counter-clockwise order but a2, b1, b2 are not,
    # it means that a1 and a2 are on opposite sides of the line formed by b1 and b2, 
    # which is a condition for intersection.    
    # If any two segments of the track intersect, it indicates a self-intersection, 
    # which is usually undesirable in track design and should be penalized in the fitness evaluation.
    #eg p1 = (0, 0), p2 = (1, 1), p3 = (0, 1) would return True because they are in counter-clockwise order,
    # while p1 = (0, 0), p2 = (1, 1), p3 = (1, 0) would return False because they are in clockwise order.

        def ccw(p1, p2, p3):
            return (
                (p3[1] - p1[1]) *
                (p2[0] - p1[0])
            ) > (
                (p2[1] - p1[1]) *
                (p3[0] - p1[0])
            )

        return (
            ccw(a1, b1, b2)
            != ccw(a2, b1, b2)
        ) and (
            ccw(a1, a2, b1)
            != ccw(a1, a2, b2)
        )

    def count_intersections(self):
        path = self.track.path
        intersections = 0
        for i in range(len(path) - 1):
            a1 = path[i]
            a2 = path[i + 1]
            for j in range(i + 10, len(path) - 1):
                b1 = path[j]
                b2 = path[j + 1]

                if self.segment_intersect(
                    a1, a2,
                    b1, b2
                ):
                    intersections += 1

        return intersections

    # =====================================================
    # FINAL FITNESS
    # =====================================================

    def compute_fitness(self):

        curvature, curvature_var = (
            self.compute_curvature()
        )

        stability = (
            self.steering_stability()
        )

        deviation = (
            self.path_deviation()
        )

        avg_speed = (
            self.average_speed()
        )

        intersections = (
            self.count_intersections()
        )

        # ================================================
        # NORMALIZED FITNESS
        # ================================================

        fitness = 0

        # smooth flowing tracks
        fitness += avg_speed * 20

        # reward moderate curvature variety
        fitness += curvature_var * 200

        # penalize unstable steering
        fitness -= stability * 300

        # penalize leaving center
        fitness -= deviation * 2

        # massive penalty
        fitness -= intersections * 1000

        return {
            "fitness": fitness,
            "curvature": curvature,
            "curvature_var": curvature_var,
            "stability": stability,
            "deviation": deviation,
            "avg_speed": avg_speed,
            "intersections": intersections
        }

# =========================================================
# CREATE WORLD
# =========================================================

track = Track()
agent = AIAgent(track)
evaluator = TrackEvaluator(track, agent)
# =========================================================
# MAIN LOOP
# =========================================================

running = True

while running:

    clock.tick(60)

    # =====================================================
    # EVENTS
    # =====================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:

                track = Track()
                agent = AIAgent(track)
                evaluator = TrackEvaluator(track, agent)

    # =====================================================
    # UPDATE
    # =====================================================

    agent.update()

    # =====================================================
    # DRAW
    # =====================================================

    screen.fill(BACKGROUND)

    track.draw(screen)

    agent.draw(screen)

    current_time = (
        time.time()
        - agent.lap_start_time
    )

    metrics = evaluator.compute_fitness()

    lines = [

        f"Current Lap: {current_time:.2f}s",
        f"Fitness: {metrics['fitness']:.1f}",
        f"Curvature: {metrics['curvature']:.3f}",
        f"Curvature Var: {metrics['curvature_var']:.3f}",
        f"Stability: {metrics['stability']:.5f}",
        f"Deviation: {metrics['deviation']:.2f}",
        f"Intersections: {metrics['intersections']}",
        (
            f"Last Lap: "
            f"{agent.lap_times[-1]:.2f}s"
            
            if agent.lap_times
            else "Last Lap: --"
        ),

        (
            f"Average Lap: "
            f"{agent.get_average_lap():.2f}s"
        ),

        f"Laps: {len(agent.lap_times)}",

        "SPACE = New Track"
    ]

    for i, text in enumerate(lines):

        img = font.render(
            text,
            True,
            (255,255,255)
        )

        screen.blit(
            img,
            (20, 20 + i * 30)
        )

    pygame.display.flip()

pygame.quit()
sys.exit()