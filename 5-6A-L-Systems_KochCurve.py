import pygame
import math

# Window setup
WIDTH, HEIGHT = 1000, 700
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Koch Curve L-System")

clock = pygame.time.Clock()

# L-system parameters
axiom = "F"
#rule = {"F": "F+F-F-F+F"} 90
rule = {"F": "F+F--F+F"}
angle = 60
iterations = 1

def generate_lsystem(n):
    current = axiom
    for _ in range(n):
        next_string = ""
        for c in current:
            next_string += rule.get(c, c)
        current = next_string
    return current

def draw_lsystem(sequence, length):
    x, y = WIDTH * 0.1, HEIGHT * 0.7
    heading = 0

    for command in sequence:
        if command == "F":
            new_x = x + length * math.cos(math.radians(heading))
            new_y = y - length * math.sin(math.radians(heading))

            pygame.draw.line(screen, (255,255,255), (x,y), (new_x,new_y), 1)

            x, y = new_x, new_y

        elif command == "+":
            heading += angle
        elif command == "-":
            heading -= angle


running = True

while running:
    screen.fill((0,0,0))

    seq = generate_lsystem(iterations)
    # The length of each segment decreases with each iteration 
    # to keep the curve within bounds
    length = 1400 / (3 ** iterations) if iterations > 0 else 400

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