# Created on 16 February 2020
import math
from random import randint, uniform
from pygame import Rect
from Tools import tile_ids as tiles
from Tools.constants import random_sign
from Tools import game_vars


class Biome:
    def __init__(self, idx):
        # Max and min width and height of caves
        self.cave_w_range = self.cave_h_range = [3, 8]
        # Number of blocks per cave
        self.cave_freq = 750
        # Max and min width and height of ore chunks
        self.ore_w_range = self.ore_h_range = [2, 5]
        # Number of blocks per ore spawn
        self.ore_freq = 1000
        game_vars.biomes[idx] = self

    # Calls all generate functions
    def generate(self, world, surface, x, dx):
        self.generate_terrain(world, surface, x, dx)
        underground_rect = Rect(x, world.underground, dx, world.dim[1] - world.underground)
        self.generate_ore(world, underground_rect)
        self.generate_caves(world, underground_rect)

    # Generates terrain of surface and underground
    def generate_terrain(self, world, surface, x, dx):
        land = generate_noise(15, 25, 1, dx)
        stone = generate_noise(10, 25, 3, dx)

        for i, (val1, val2) in enumerate(zip(land, stone)):
            land_h = world.surface + val1
            stone_h = world.underground + val2
            fill_chunk(world.blocks, x + i, 1, land_h, stone_h - land_h, tiles.DIRT)
            fill_chunk(world.blocks, x + i, 1, stone_h, world.dim[1] - stone_h, tiles.STONE)
            surface[x + i] = land_h

    # Generates caves underground
    def generate_caves(self, world, rect):
        w, h = world.dim
        num_caves = rect.w * rect.h // self.cave_freq
        # Caves
        for i in range(num_caves):
            x, y = randint(rect.left, rect.right), randint(rect.top, rect.bottom)
            r_x, r_y = randint(*self.cave_w_range), randint(*self.cave_h_range)
            while r_x > 0 and r_y > 0:
                for dx in range(max(-x, -r_x), min(w - x, r_x)):
                    dy = int(math.sqrt(1 - (dx * dx / r_x / r_x)) * r_y)
                    min_y, max_y = y - dy - randint(-1, 1), y + dy + randint(-1, 1)
                    fill_chunk(world.blocks, x + dx, 1, min_y, max_y - min_y, tiles.AIR)
                x += random_sign() * r_x // randint(1, 2)
                y += r_y // randint(1, 2)
                r_x //= 2
                r_y //= 2

    # Spawns ore chunks underground
    def generate_ore(self, world, rect):
        w, h = world.dim
        num_chunks = rect.w * rect.h // self.ore_freq
        # Ore chunks
        for i in range(num_chunks):
            x, y = randint(rect.left, rect.right), randint(rect.top, rect.bottom)
            r_x, r_y = randint(*self.ore_w_range), randint(*self.ore_h_range)
            ore = self.get_ore_type(y / h)
            for dx in range(max(-x, -r_x), min(w - x, r_x)):
                dy = int(math.sqrt(1 - (dx * dx / r_x / r_x)) * r_y)
                min_y, max_y = max(0, y - dy - randint(-1, 1)), min(h, y + dy + randint(-1, 1))
                fill_chunk(world.blocks, x + dx, 1, min_y, max_y - min_y, ore)

    # Returns type of ore to spawn based on fraction of world height (from the top)
    def get_ore_type(self, h_frac):
        return tiles.SHINY_STONE_1


class Structure:
    def __init__(self, idx):
        self.biome_reqs = []
        game_vars.structures[idx] = self

    def generate(self, world, surface, rects):
        for i in range(10):
            rect = self.get_rect(world.dim, surface)
            good = True
            for r in rects:
                if rect.colliderect(r):
                    good = False
                    break
            if good:
                self.generate_structure(world, surface, rect)
                rects.append(rect)
                return

    def get_rect(self, world_dim, surface):
        return Rect(0, 0, 0, 0)

    def generate_structure(self, world, surface, rect):
        pass

    def can_spawn(self, biomes):
        reqs = self.biome_reqs.copy()
        for biome in biomes:
            if biome in reqs:
                reqs.remove(biome)
        return len(reqs) == 0


def fill_chunk(blocks, x, dx, y, dy, val):
    # Make sure there's actually something to fill
    if dx <= 0 or dy <= 0:
        return
    world_h, world_w = blocks.shape
    # Get smallest x and y
    min_x, max_x = x + min(0, dx), x + max(0, dx)
    min_y, max_y = y + min(0, dy), y + max(0, dy)
    # Make sure at least part of the chunk is in the world
    if min_x < world_w and min_y < world_h and max_x > 0 and max_y > 0:
        # Trim any parts of the chunk that are out of the world
        min_x, min_y = max(min_x, 0), max(min_y, 0)
        max_x, max_y = min(max_x, world_w), min(max_y, world_h)
        blocks[min_y:max_y, min_x:max_x] = [[val] * (max_x - min_x)] * (max_y - min_y)


def generate_noise(amp, wl, octaves, w):
    def interpolate(p1, p2, t):
        angle = t * math.pi / 2
        f = math.sin(angle)
        return p1 * (1 - f) + p2 * f

    def get_noise(div):
        amp_ = int(amp / div)
        if amp_ == 0:
            amp_ = 1
        wl_ = int(wl / div)
        if wl_ == 0:
            wl_ = 1
        vals = []
        a, b = 0, uniform(0, 1)
        for t in range(w):
            if t != 0 and t % wl_ == 0:
                a = b
                if w - t >= wl_ * 2:
                    b = uniform(0, 1)
                else:
                    b = 0
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
