# Created on 22 October 2019
# Generates the world

from pygame import Rect
from math import copysign
from Objects.Items.items import *
from World.Features import *

SURFACE, CAVE = 0, 0
surface_heights = []
taken = []


# Calls all world generation functions in order
def generate_world(blocks):
    dim = blocks.shape
    global SURFACE, CAVE
    SURFACE = dim[0] // 2
    CAVE = dim[0] * 2 // 3
    blocks.fill(AIR_ID)
    generate_surface(blocks)
    generate_underground(blocks)
    taken.append(Rect(dim[1] // 3, 0, dim[1] // 3, dim[0]))
    for i in range(3):
        rect = add_build(generate_mountain, blocks)
        if rect is not None:
            taken.append(rect)
    # TODO: More world generation
    centerx = int(blocks.shape[1] / 2)
    return centerx, min(surface_heights[centerx], surface_heights[centerx + 1])


def generate_surface(blocks):
    off = 0
    world_w = blocks.shape[1]
    for x in range(world_w):
        off += random_gen(off)
        surface_heights.append(SURFACE + off)
        fill_chunk(x, 1, SURFACE + off, CAVE - SURFACE - off, DIRT.idx, blocks)
        if randint(0, 100) == 1:
            blocks[SURFACE + off + 1][x] = CAT.idx


def generate_underground(blocks):
    off = 0
    world_w, world_h = blocks.shape[1], blocks.shape[0]
    for x in range(world_w):
        off += random_gen(off)
        fill_chunk(x, 1, CAVE + off, world_h - CAVE - off, STONE.idx, blocks)
        if off >= 0:
            fill_chunk(x, 1, CAVE, off, DIRT.idx, blocks)


def add_build(func, blocks):
    blocks, surface = func()
    rect = Rect(0, SURFACE, blocks.shape[1], blocks.shape[0])
    rect.x = randint(0, blocks.shape[1] - blocks.shape[1])
    rect.y = surface_heights[rect.x] - surface
    passed = False
    while not passed:
        passed = True
        for r in taken:
            if r.colliderect(rect):
                rect.x = randint(0, blocks.shape[1] - rect.w)
                rect.y = surface_heights[rect.x] - surface
                passed = False
                break
    return copy_chunk(blocks, rect.topleft, blocks)


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

    return Rect(point[0], point[1], struct_w, struct_h)


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
