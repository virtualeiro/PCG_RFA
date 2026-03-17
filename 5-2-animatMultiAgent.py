import pygame
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


# -----------------------------
# ENUMS
# -----------------------------

class IntentionType(Enum):
    PerformPlan = "PerformPlan"


# -----------------------------
# ATTITUDE
# -----------------------------

@dataclass
class Attitude:
    label: Enum
    representation: Dict


# -----------------------------
# ENVIRONMENT
# -----------------------------

class Environment:
    def __init__(self):
        self.water = [(100, 100)]
        self.food = [(800, 100)]
        self.beds = [(450, 500)]

    def draw(self, screen):
        for w in self.water:
            pygame.draw.circle(screen, (0, 0, 255), w, 12)

        for f in self.food:
            pygame.draw.circle(screen, (0, 255, 0), f, 12)

        for b in self.beds:
            pygame.draw.rect(screen, (200, 100, 50), (*b, 20, 10))


# -----------------------------
# AGENT
# -----------------------------

class AnimatBDI:

    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.speed = 1.2

        self.beliefs = [{
            "hunger": random.randint(10, 50),
            "thirst": random.randint(30, 80),
            "fatigue": random.randint(0, 30),
            "energy": 60,
            "temperature": 37,
        }]

        self.current_intention: Optional[Attitude] = None

        self.targets = {
            "hunger": 45,
            "thirst": 40,
            "fatigue": 30,
        }

    # -----------------------------
    # DRIVE
    # -----------------------------
    def drive(self, current, target):
        return max(0, current - target)

    # -----------------------------
    # DESIRES
    # -----------------------------
    def generate_desires(self):
        m = self.beliefs[0]
        desires = []

        desires.append(("Drink", self.drive(m["thirst"], self.targets["thirst"])))
        desires.append(("Eat", self.drive(m["hunger"], self.targets["hunger"])))
        desires.append(("Rest", self.drive(m["fatigue"], self.targets["fatigue"])))

        return sorted(desires, key=lambda x: x[1], reverse=True)

    # -----------------------------
    # DELIBERATION
    # -----------------------------
    def deliberate(self, desires):
        if not desires:
            return None

        action = desires[0][0]
        self.current_intention = Attitude(
            IntentionType.PerformPlan,
            {"action": action}
        )
        return self.current_intention

    # -----------------------------
    # TARGET SELECTION
    # -----------------------------
    def get_target(self, env, action):
        if action == "Drink":
            return pygame.Vector2(env.water[0])
        if action == "Eat":
            return pygame.Vector2(env.food[0])
        if action == "Rest":
            return pygame.Vector2(env.beds[0])

    # -----------------------------
    # MOVEMENT
    # -----------------------------
    def move_towards(self, target):
        direction = target - self.pos
        if direction.length() > 1:
            direction = direction.normalize()
            self.pos += direction * self.speed

    # -----------------------------
    # ACTION EXECUTION
    # -----------------------------
    def execute(self, env):
        if not self.current_intention:
            return

        action = self.current_intention.representation["action"]
        target = self.get_target(env, action)

        self.move_towards(target)

        # check arrival
        if self.pos.distance_to(target) < 10:
            m = self.beliefs[0]

            if action == "Drink":
                m["thirst"] -= 60

            elif action == "Eat":
                m["hunger"] -= 60

            elif action == "Rest":
                m["fatigue"] -= 40

    # -----------------------------
    # METABOLISM
    # -----------------------------
    def update_body(self):
        m = self.beliefs[0]
        m["hunger"] += 0.05
        m["thirst"] += 0.08
        m["fatigue"] += 0.03

    # -----------------------------
    # DRAW
    # -----------------------------
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), self.pos, 6)


# -----------------------------
# MAIN
# -----------------------------

def main():
    env = Environment()

    agents = [
        AnimatBDI(random.randint(50, 850), random.randint(50, 550))
        for _ in range(10)
    ]

    running = True

    while running:
        screen.fill((30, 30, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # update agents
        for agent in agents:
            desires = agent.generate_desires()
            agent.deliberate(desires)
            agent.execute(env)
            agent.update_body()
            agent.draw(screen)

        env.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()