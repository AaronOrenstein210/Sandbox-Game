# Created on 22 October 2019
# Generates the world

from numpy import full, int16
from random import randint, choice
import random, math
import pygame as pg
from Objects.tile_ids import *
from UI.Operations import CompleteTask, loading_bar
from Tools import objects as o
from World import world_zones as zones

FOREST, MOUNTAIN, VALLEY = range(3)


class WorldGenerator:
    def __init__(self, world):
        self.world = world
        self.surface = []

    def generate(self, dim, biomes):
        self.world.new_world(dim)
        self.surface = [-1] * dim[0]
        zones.set_world_heights(dim[1])
        # Generate biomes
        current = [-1, -1, -1]
        section_w = 100
        min_w, max_w = section_w * 9 // 10, section_w * 11 / 10
        x = 0
        while x < dim[0]:
            # Get random biome type and width
            if dim[0] - x >= section_w * 3 // 2:
                dx = randint(min_w, max_w)
            else:
                dx = dim[0] - x
            biome = choice(biomes)
            # If it is a new biome, generate the old biome and start a new entry
            if current[0] != biome:
                if current[0] != -1:
                    self.generate_biome(*current)
                current = [biome, x, dx]
            # Otherwise increase the length of the biome
            else:
                current[2] += dx
            x += dx
        self.generate_biome(*current)
        self.add_snow()
        # Save file
        centerx = dim[0] // 2
        self.world.spawn = [centerx,
                            min(self.surface[centerx], self.surface[centerx + 1]) - math.ceil(o.player.dim[1])]
        self.surface.clear()
        CompleteTask(self.world.save_part, [2], loading_bar, ["Saving New World"],
                     can_exit=False).run_now()

    def add_snow(self):
        for x, y in enumerate(self.surface):
            if zones.surface - y >= 20:
                # Add some snow
                chance = 25
                while randint(1, 25) <= chance:
                    self.world.blocks[y][x] = SNOW
                    y += 1
                    chance /= 1.5

    # Wrapper for generating a specific biome
    def generate_biome(self, biome, x, dx):
        x2 = x + dx
        if x >= self.world.dim[0] or x2 <= 0:
            return
        else:
            if x < 0:
                x = 0
            if x2 > self.world.dim[0]:
                x2 = self.world.dim[0]
        if biome == FOREST:
            self.forest(x, x2)
        elif biome == MOUNTAIN:
            self.mountains(x, x2)
        elif biome == VALLEY:
            self.valley(x, x2)

    # Smooth left boundary between biomes
    # X is the left-most index of the biome
    def smooth_left(self, x):
        next_x = x - 1
        if 0 <= next_x < self.world.dim[0] and self.surface[next_x] != -1:
            # Positive if we are higher, negative if lower
            diff = self.surface[next_x] - self.surface[x]
            if abs(diff) > 5:
                # If the y diff is over 30 self.world.blocks, make y:x ratio bigger (steeper curve)
                # 1 <= y/x <= 2.5
                dx = int(abs(diff) / min(2, max(1, diff / 30)))
                # The left side is higher if we are lower
                higher_left = diff < 0
                if higher_left:
                    x_min = x
                    x_max = min(self.world.dim[0], x + dx)
                else:
                    x_min = max(0, x - dx)
                    x_max = x
                dx = x_max - x_min
                for x1 in range(x_min, x_max):
                    if self.surface[x1] == -1:
                        break
                    # Start high if higher left
                    frac = abs(x1 - (x_max if higher_left else x_min)) / dx
                    dy = int(s_curve(frac) * abs(diff))
                    self.fill_chunk(x1, 1, self.surface[x1], -dy, DIRT)
                    self.surface[x1] -= dy

    # Smooth right boundary between biomes
    # X is the right-most index of the biome
    def smooth_right(self, x):
        next_x = x + 1
        if 0 <= next_x < self.world.dim[0] and self.surface[next_x] != -1:
            # Positive if we are higher, negative if lower
            diff = self.surface[next_x] - self.surface[x]
            if abs(diff) > 5:
                # If the y diff is over 30 self.world.blocks, make y:x ratio bigger (steeper curve)
                # 1 <= y/x <= 2.5
                dx = int(abs(diff) / min(2, max(1, diff / 30)))
                # The left side is higher if we are higher
                higher_left = diff >= 0
                if higher_left:
                    x_min = next_x
                    x_max = min(self.world.dim[0], next_x + dx)
                else:
                    x_min = max(0, next_x - dx)
                    x_max = next_x
                dx = x_max - x_min
                for x1 in range(x_min, x_max):
                    if self.surface[x1] == -1:
                        break
                    # Start high if higher left
                    frac = abs(x1 - (x_max if higher_left else x_min)) / dx
                    dy = int(s_curve(frac) * abs(diff))
                    self.fill_chunk(x1, 1, self.surface[x1], -dy, DIRT)
                    self.surface[x1] -= dy

    # Forest biome
    def forest(self, x1, x2):
        noise1 = generate_noise(15, 50, 1, x2 - x1)
        noise2 = generate_noise(10, 25, 3, x2 - x1)

        for dx, (val1, val2) in enumerate(zip(noise1, noise2)):
            surface = zones.surface - val1
            border = zones.underground - val2
            self.fill_chunk(x1 + dx, 1, border, surface - border, DIRT)
            self.surface[x1 + dx] = surface
            self.fill_chunk(x1 + dx, 1, self.world.dim[1], border - self.world.dim[1], STONE)
            # Add spawners
            if randint(1, 150) == 1:
                self.world.blocks[surface + randint(1, 3)][x1 + dx] = CAT
            elif randint(1, 100) == 1:
                self.world.blocks[surface + randint(1, 4)][x1 + dx] = DOOM_BUNNY
            # Add trees
            if randint(0, 10) == 1:
                self.tree(x1 + dx, 5, 10)

        self.smooth_left(x1)
        self.smooth_right(x2 - 1)

    # Mountain biome
    def mountains(self, x1, x2):
        noise1 = generate_noise(50, 35, 5, x2 - x1)
        noise2 = generate_noise(10, 25, 3, x2 - x1)

        for dx, (val1, val2) in enumerate(zip(noise1, noise2)):
            surface = zones.surface - val1
            border = zones.underground - val2
            self.fill_chunk(x1 + dx, 1, border, surface - border, DIRT)
            self.surface[x1 + dx] = surface
            self.fill_chunk(x1 + dx, 1, self.world.dim[1], border - self.world.dim[1], STONE)

        self.smooth_left(x1)
        self.smooth_right(x2 - 1)

    # Valley biome
    def valley(self, x1, x2):
        noise1 = generate_noise(-50, (x2 - x1) // 2, 0, x2 - x1)
        noise2 = generate_noise(10, 25, 3, x2 - x1)

        for dx, (val1, val2) in enumerate(zip(noise1, noise2)):
            surface = zones.surface - val1
            border = zones.underground - val2
            self.fill_chunk(x1 + dx, 1, border, surface - border, DIRT)
            self.surface[x1 + dx] = surface
            self.fill_chunk(x1 + dx, 1, self.world.dim[1], border - self.world.dim[1], STONE)
            if randint(1, 200) <= math.sqrt(abs(zones.surface - surface)):
                self.world.blocks[surface + randint(1, 3)][x1 + dx] = ZOMBIE

        self.smooth_left(x1)
        self.smooth_right(x2 - 1)

    # Tree
    def tree(self, x, h_min, h_max):
        # Get random height
        h = randint(h_min, h_max)
        # Get leaf radius
        r = max(h // 3, 1)
        w = r * 2 + 1
        tree = full((h, w), -1, dtype=int16)
        # Add leaves
        i = .5
        c_x = w / 2
        c_y = r + .5
        # Check number of spawners allowed
        num_birdie = 2 if h >= 9 else 1 if h >= 7 else 0
        num_helicopter = 1 if h >= 8 else 0
        # Go through the center of each x
        while i <= w - .5:
            # Use pythagorean theorem to compute height of leaves
            dx = c_x - i
            dy = math.sqrt((r * r) - (dx * dx))
            y_min, y_max = int(c_y - dy), int(c_y + dy) + 1
            tree[y_min:y_max, int(i)] = [LEAVES] * (y_max - y_min)
            if num_birdie > 0 and randint(1, 10) == 1:
                tree[randint(y_min, y_max), int(i)] = BIRDIE
                num_birdie -= 1
            elif num_helicopter > 0 and randint(1, 20) == 1:
                tree[randint(y_min, y_max), int(i)] = HELICOPTER
                num_helicopter -= 1
            i += 1
        # Add trunk
        tree[r:, r] = [WOOD] * (h - r)
        # Add tree to world
        self.add_chunk(tree, [x - r, self.surface[x] - h])

    def add_chunk(self, chunk, point):
        point = list(point)
        world_h, world_w = self.world.blocks.shape
        struct_h, struct_w = chunk.shape
        # Make sure at least some of the shape is in the world
        if not (0 <= point[0] <= world_w - struct_w or
                0 <= point[1] <= world_h - struct_h):
            return

        # Trim the shape as needed
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

        # Ignore -1 values (Air values are good)
        for dy in range(struct_h):
            for dx in range(struct_w):
                val = chunk[dy][dx]
                if val != -1:
                    self.world.blocks[point[1] + dy][point[0] + dx] = val

    def fill_chunk(self, x, dx, y, dy, val):
        world_h, world_w = self.world.blocks.shape
        # Get smallest x and y
        min_x, max_x = x + min(0, dx), x + max(0, dx)
        min_y, max_y = y + min(0, dy), y + max(0, dy)
        # Make sure at least part of the chunk is in the world
        if min_x < world_w and min_y < world_h and max_x > 0 and max_y > 0:
            # Trim any parts of the chunk that are out of the world
            min_x, min_y = max(min_x, 0), max(min_y, 0)
            max_x, max_y = min(max_x, world_w), min(max_y, world_h)
            fill = full((max_y - min_y, max_x - min_x), val, dtype=int16)
            self.world.blocks[min_y:max_y, min_x:max_x] = fill


def get_random_biome():
    return randint(0, 2)


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
