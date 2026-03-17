import turtle
import random

# Define grammar rules
symbols = ['circle', 'square', 'triangle']
colors = ['red', 'blue', 'green']

def draw_shape(shape, color):
    turtle.fillcolor(color)
    turtle.begin_fill()
    if shape == 'circle':
        turtle.circle(30)
    elif shape == 'square':
        for _ in range(4):
            turtle.forward(60)
            turtle.right(90)
    elif shape == 'triangle':
        for _ in range(3):
            turtle.forward(60)
            turtle.right(120)
    turtle.end_fill()
    turtle.forward(80)

# Generate a sequence using grammar
sequence = [random.choice(symbols) for _ in range(5)]
color_sequence = [random.choice(colors) for _ in range(5)]

# Draw the shapes
turtle.speed(1)
for shape, color in zip(sequence, color_sequence):
    draw_shape(shape, color)

turtle.done()