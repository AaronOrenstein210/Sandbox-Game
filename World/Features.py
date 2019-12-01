from math import sqrt
from random import randint
from numpy import full, int16, vstack
from Tools.constants import AIR_ID
from Objects.Items.items import DIRT
from Objects.Items.items import ZOMBIE


def generate_mountain():
    w = 50
    r = int(w / 2)
    r_squared = pow(r, 2)

    blocks = full((r, w), AIR_ID, dtype=int16)

    def func(input_):
        return sqrt(r_squared - pow(input_ - r, 2))

    for x in range(w):
        dy = -int(func(x))
        fill_chunk(x, 1, r, dy, DIRT.idx, blocks)
        if abs(x - (w / 2)) <= 1:
            blocks[1][x] = ZOMBIE.idx

    num_zigzags = randint(2, 8)
    x = 0
    current_y = r
    dirt_row = full((1, w), DIRT.idx, dtype=int16)
    for j in range(num_zigzags):
        direction = 1 if j % 2 == 0 else -1
        zigzag_l = randint(w - 10, w)
        old_val = x
        while x >= old_val - zigzag_l if direction == -1 else x <= zigzag_l:
            blocks = vstack((blocks, dirt_row))
            dx = randint(1, 5) * direction
            current_y += 1
            fill_chunk(x, dx, current_y, -randint(6, 7), AIR_ID, blocks)
            x += dx

    return blocks, r


def fill_chunk(x, dx, y, dy, val, blocks):
    world_h, world_w = blocks.shape
    # Get smallest x and y
    min_x, max_x = x + min(0, dx), x + max(0, dx)
    min_y, max_y = y + min(0, dy), y + max(0, dy)
    # Make sure at least part of the chunk is in the world
    if min_x < world_w and min_y < world_h and max_x > 0 and max_y > 0:
        # Trim any parts of the chunk that are out of the world
        min_x, min_y = max(min_x, 0), max(min_y, 0)
        max_x, max_y = min(max_x, world_w), min(max_y, world_h)
        fill = full((max_y - min_y, max_x - min_x), val, dtype=int16)
        blocks[min_y:max_y, min_x:max_x] = fill
