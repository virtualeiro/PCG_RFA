import pygame
import math

pygame.init()

WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("L-System Tree")

clock = pygame.time.Clock()

# L-system parameters
axiom = "F"
rule = {"F": "F[-F]F[+F][F]"}
angle = 30
iterations = 0


def generate_lsystem(n):
    current = axiom
    for _ in range(n):
        next_string = ""
        for c in current:
            next_string += rule.get(c, c)
        current = next_string
    return current


def draw_lsystem(sequence, length):
    x = WIDTH // 2
    y = HEIGHT - 50
    heading = -90  # start pointing up

    stack = []

    for command in sequence:

        if command == "F":
            new_x = x + length * math.cos(math.radians(heading))
            new_y = y + length * math.sin(math.radians(heading))

            pygame.draw.line(screen, (0, 255, 100), (x, y), (new_x, new_y), 1)

            x, y = new_x, new_y

        elif command == "+":
            heading += angle

        elif command == "-":
            heading -= angle

        elif command == "[":
            stack.append((x, y, heading))

        elif command == "]":
            x, y, heading = stack.pop()


running = True

while running:

    screen.fill((10, 10, 20))

    seq = generate_lsystem(iterations)

    length = 120 / (iterations + 1)

    draw_lsystem(seq, length)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:
                iterations += 1
                if iterations > 6:
                    iterations = 0

    pygame.display.flip()
    clock.tick(30)

pygame.quit()