import math
# =========================================
# L-SYSTEM DUNGEON GENERATOR (FULL SCRIPT)
# =========================================

# ---------
# 1. L-System definition
# ---------

AXIOM = "X"

RULES = {
    "X": "[+FX]F[+FX][-FX]FR",          # branching + reward at dead end
    "F": "FF-[-F+F]+[+F-F]"        # curvature → loops
}

ITERATIONS = 3


# ---------
# 2. Expand L-System
# ---------

def expand_lsystem(axiom, rules, iterations):
    result = axiom
    for _ in range(iterations):
        expanded = ""
        for char in result:
            expanded += rules.get(char, char)
        result = expanded
    return result


# ---------
# 3. Build dungeon grid
# ---------

def build_level(lsys_string, size=41):
    # Grid setup
    grid = [["#" for _ in range(size)] for _ in range(size)]

    # Turtle state
    x = y = size // 2
    direction = 0  # 0=N, 1=E, 2=S, 3=W
    stack = []

    grid[y][x] = "S"  # Start position

    for char in lsys_string:

        if char == "F":
            if direction == 0:
                y -= 1
            elif direction == 1:
                x += 1
            elif direction == 2:
                y += 1
            elif direction == 3:
                x -= 1

            if 0 <= x < size and 0 <= y < size:
                grid[y][x] = "."

        elif char == "+":
            direction = (direction + 1) % 4

        elif char == "-":
            direction = (direction - 1) % 4

        elif char == "[":
            stack.append((x, y, direction))

        elif char == "]":
            x, y, direction = stack.pop()

        elif char == "R":
            if 0 <= x < size and 0 <= y < size:
                grid[y][x] = "R"

    return grid


# ---------
# 4. Print dungeon
# ---------

def print_level(grid):
    for row in grid:
        print("".join(row))


# ---------
# 5. Run everything
# ---------

if __name__ == "__main__":
    lsystem_string = expand_lsystem(AXIOM, RULES, ITERATIONS)
    dungeon = build_level(lsystem_string)
    print_level(dungeon)
