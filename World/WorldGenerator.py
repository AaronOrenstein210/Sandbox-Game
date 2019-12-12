# Created on 22 October 2019
# Generates the world

from numpy import full, int16, vstack
from math import copysign, sqrt
from random import randint
import random, math
import pygame as pg
from Objects.tile_ids import *
from UI.Operations import CompleteTask
from Tools import objects as o
from World import world_zones as zones

# Defines world zones
surface_heights = []
taken = []
block_data = {}


# Calls all world generation functions in order
def generate_world(universe, name, dim=(500, 1000)):
    global surface_heights
    surface_heights = [-1] * dim[1]
    blocks = full(dim, AIR, dtype=int16)
    zones.set_world_heights(dim[0])
    forest(blocks, dim[1] // 3, dim[1] * 2 // 3)
    if randint(0, 1) == 0:
        mountains(blocks, 0, dim[1] // 3)
        valley(blocks, dim[1] * 2 // 3, dim[1])
    else:
        mountains(blocks, dim[1] * 2 // 3, dim[1])
        valley(blocks, 0, dim[1] // 3)
    # Save file
    centerx = dim[1] // 2
    spawn = (centerx, min(surface_heights[centerx], surface_heights[centerx + 1]) - math.ceil(o.player.dim[1]))
    file = "saves/universes/" + universe + "/" + name + ".wld"
    CompleteTask(o.save_world_part, task_args=[file, 1, blocks, spawn, block_data], draw_args=("Saving New World",),
                 can_exit=False).run_now()


def generate_noise(amp, wl, octaves, w):
    def interpolate(p1, p2, t):
        angle = t * math.pi
        f = (1 - math.cos(angle)) * .5
        return p1 * (1 - f) + p2 * f

    def get_noise(div):
        amp_ = int(amp / div)
        if amp_ == 0:
            amp_ = 1
        wl_ = int(wl / div)
        if wl_ == 0:
            wl_ = 1
        vals = []
        a, b = random.uniform(0, 1), random.uniform(0, 1)
        for t in range(w):
            if t % wl_ == 0:
                a = b
                b = random.uniform(0, 1)
                vals.append(a * amp_)
            else:
                vals.append(interpolate(a, b, (t % wl_) / wl_) * amp_)
        return vals

    noise = get_noise(1)
    for i in range(1, octaves + 1):
        octave = get_noise(pow(2, i))
        noise = [noise[j] + val for j, val in enumerate(octave)]
    noise = [int(n) for n in noise]
    return noise


def s_curve(x):
    return x * x * x * (x * ((x * 6) - 15) + 10)


def smooth_s_curve(x, left, blocks):
    next_x = x - 1 if left else x + 1
    if 0 <= next_x < blocks.shape[1] and surface_heights[next_x] != -1:
        # Positive if we are higher, negative if lower
        diff = surface_heights[next_x] - surface_heights[x]
        if abs(diff) > 5:
            # If the y diff is over 30 blocks, make y:x ratio bigger (steeper curve)
            # 1 <= y/x <= 2.5
            dx = int(abs(diff) / min(2, max(1, diff / 30)))
            # The left side is higher if we are looking at our left side and
            # We are smaller or the opposite
            higher_left = (left and diff < 0) or (not left and diff >= 0)
            if higher_left:
                # If we are using our right side, we need to use next x
                x_min = x if left else next_x
                x_max = min(blocks.shape[1], x + dx)
            else:
                x_min = max(0, x - dx)
                # If we are using our right side, we need to use next_x
                x_max = x if left else next_x
            dx = x_max - x_min
            for x1 in range(x_min, x_max):
                if surface_heights[x1] == -1:
                    break
                # Start high if higher left
                frac = (dx - abs(x1 - x_min) if higher_left else abs(x1 - x_min)) / dx
                dy = int(s_curve(frac) * abs(diff))
                fill_chunk(x1, 1, surface_heights[x1], -dy, DIRT, blocks)
                surface_heights[x1] -= dy
            # Return new x
            if left:
                return x if dx < 0 else x + dx
            else:
                return x if dx >= 0 else x + dx
    return x


def forest(blocks, x1, x2):
    noise1 = generate_noise(15, 50, 1, x2 - x1)
    noise2 = generate_noise(10, 25, 3, x2 - x1)

    for dx, (val1, val2) in enumerate(zip(noise1, noise2)):
        surface = zones.surface - val1
        border = zones.underground - val2
        fill_chunk(x1 + dx, 1, border, surface - border, DIRT, blocks)
        surface_heights[x1 + dx] = surface
        fill_chunk(x1 + dx, 1, blocks.shape[0], border - blocks.shape[0], STONE, blocks)
        if randint(1, 150) == 1:
            blocks[surface + randint(1, 3)][x1 + dx] = CAT

    smooth_s_curve(x1, True, blocks)
    smooth_s_curve(x2 - 1, False, blocks)


def mountains(blocks, x1, x2):
    noise1 = generate_noise(50, 35, 5, x2 - x1)
    noise2 = generate_noise(10, 25, 3, x2 - x1)

    for dx, (val1, val2) in enumerate(zip(noise1, noise2)):
        surface = zones.surface - val1
        border = zones.underground - val2
        fill_chunk(x1 + dx, 1, border, surface - border, DIRT, blocks)
        surface_heights[x1 + dx] = surface
        fill_chunk(x1 + dx, 1, blocks.shape[0], border - blocks.shape[0], STONE, blocks)
        # Add some snow
        chance, y = 25, surface
        while randint(1, 25) <= chance:
            blocks[y][x1 + dx] = SNOW
            y -= 1
            chance /= 1.5

    smooth_s_curve(x1, True, blocks)
    smooth_s_curve(x2 - 1, False, blocks)


def valley(blocks, x1, x2):
    noise1 = generate_noise(-50, (x2 - x1) // 2, 0, x2 - x1)
    noise2 = generate_noise(10, 25, 3, x2 - x1)

    for dx, (val1, val2) in enumerate(zip(noise1, noise2)):
        surface = zones.surface - val1
        border = zones.underground - val2
        fill_chunk(x1 + dx, 1, border, surface - border, DIRT, blocks)
        surface_heights[x1 + dx] = surface
        fill_chunk(x1 + dx, 1, blocks.shape[0], border - blocks.shape[0], STONE, blocks)
        if randint(1, 200) <= math.sqrt(abs(zones.surface - surface)):
            blocks[surface + randint(1, 5)][x1 + dx] = ZOMBIE

    smooth_s_curve(x1, True, blocks)
    smooth_s_curve(x2 - 1, False, blocks)


def generate_mountain():
    w = 50
    r = int(w / 2)
    r_squared = pow(r, 2)

    blocks = full((r, w), AIR, dtype=int16)

    def func(input_):
        return sqrt(r_squared - pow(input_ - r, 2))

    for x in range(w):
        dy = -int(func(x))
        fill_chunk(x, 1, r, dy, DIRT, blocks)
        if abs(x - (w / 2)) <= 1:
            blocks[1][x] = ZOMBIE

    num_zigzags = randint(2, 8)
    x = 0
    current_y = r
    dirt_row = full((1, w), DIRT, dtype=int16)
    for j in range(num_zigzags):
        direction = 1 if j % 2 == 0 else -1
        zigzag_l = randint(w - 10, w)
        old_val = x
        while x >= old_val - zigzag_l if direction == -1 else x <= zigzag_l:
            blocks = vstack((blocks, dirt_row))
            dx = randint(1, 5) * direction
            current_y += 1
            fill_chunk(x, dx, current_y, -randint(6, 7), AIR, blocks)
            x += dx

    return blocks


def add_build(func, blocks):
    chunk = func()
    rect = pg.Rect(0, zones.surface, chunk.shape[1], chunk.shape[0])
    rect.x = randint(0, blocks.shape[1] - chunk.shape[1])
    rect.y = surface_heights[rect.x] - 6
    passed = False
    while not passed:
        passed = True
        for r in taken:
            if r.colliderect(rect):
                rect.x = randint(0, blocks.shape[1] - rect.w)
                rect.y = surface_heights[rect.x] - surface
                passed = False
                break
    return copy_chunk(chunk, rect.topleft, blocks)


def copy_chunk(chunk, point, blocks):
    point = list(point)
    world_h, world_w = blocks.shape
    if point[0] >= world_w or point[1] >= world_h:
        return

    struct_h, struct_w = chunk.shape
    if point[0] < 0:
        chunk = chunk[:, abs(point[0]):]
        point[0] = 0
    if point[0] > world_w - struct_w:
        chunk = chunk[:, :world_w - struct_w - point[0]]
    if point[1] < 0:
        chunk = chunk[abs(point[1]):, :]
        point[1] = 0
    if point[1] > world_h - struct_h:
        chunk = chunk[:world_h - struct_h - point[1], :]
    struct_h, struct_w = chunk.shape

    blocks[point[1]:point[1] + struct_h, point[0]:point[0] + struct_w] = chunk

    return pg.Rect(point[0], point[1], struct_w, struct_h)


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


# World generation
def random_gen(last_dif):
    same_direction = 25 / pow(2, abs(last_dif))
    num = randint(1, 100)
    # No change
    if num <= 50:
        return 0
    # Keep going same direction
    if num <= 50 + same_direction:
        return int(copysign(1, last_dif))
    # Go opposite direction
    else:
        return int(copysign(1, -last_dif))
