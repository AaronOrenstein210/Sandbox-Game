# Created on 15 February 2020

from random import randint, uniform
import math
from pygame import Rect
from Tools import tile_ids as tiles, item_ids as items
from Tools import game_vars
from Tools.constants import random_sign
from World.WorldObjects import Biome, Structure, generate_noise, fill_chunk


class Forest(Biome):
    def __init__(self):
        super().__init__(items.FOREST)

    def generate_terrain(self, world, surface, x, dx):
        land = generate_noise(15, 25, 1, dx)
        stone = generate_noise(10, 25, 3, dx)

        free = 0
        for i, (val1, val2) in enumerate(zip(land, stone)):
            land_h = world.surface_h + val1
            stone_h = world.underground + val2
            fill_chunk(world.blocks, x + i, 1, land_h, stone_h - land_h, tiles.DIRT)
            fill_chunk(world.blocks, x + i, 1, stone_h, world.dim[1] - stone_h, tiles.STONE)
            surface[x + i] = land_h
            if free <= i and randint(1, 10) == 1:
                free = i + self.tree(world.blocks, x + i, land_h)

    # Tree
    def tree(self, blocks, left, bottom):
        if bottom < 5:
            return 0
        # Get random height
        h = min(randint(5, 9), bottom)
        top = bottom - h
        # Get leaf radius
        r = max(h // 3, 1)
        w = r * 2 + 1
        c = r + .5
        # Check number of spawners allowed
        num_birdie = 2 if h >= 9 else 1 if h >= 7 else 0
        num_helicopter = 1 if h >= 8 else 0
        # Go through the center of each x
        for dx in range(-r, r + 1):
            if left + dx < 0 or left + dx >= blocks.shape[1]:
                continue
            # Use pythagorean theorem to compute height of leaves
            dy = math.sqrt((r * r) - (dx * dx))
            y_min, y_max = top + int(c - dy), top + int(c + dy) + 1
            fill_chunk(blocks, left + dx, 1, y_min, y_max - y_min, tiles.LEAVES)
            # Add trunk if at the center
            if dx == 0:
                fill_chunk(blocks, left + dx, 1, top + r, h - r, tiles.WOOD)
            if num_birdie > 0 and randint(1, 10) == 1:
                blocks[randint(y_min, y_max), dx + left] = tiles.BIRDIE
                num_birdie -= 1
            elif num_helicopter > 0 and randint(1, 20) == 1:
                blocks[randint(y_min, y_max), dx + left] = tiles.HELICOPTER
                num_helicopter -= 1
        return w

    def get_ore_type(self, h_frac):
        chances_i = {tiles.SHINY_STONE_1: 65, tiles.SHINY_STONE_2: 35, tiles.SHINY_STONE_3: 0}
        chances_f = {tiles.SHINY_STONE_1: 25, tiles.SHINY_STONE_2: 45, tiles.SHINY_STONE_3: 30}
        return random_ore(h_frac, .66, 1, chances_i, chances_f)


class Mountain(Biome):
    def __init__(self):
        super().__init__(items.MOUNTAIN)

    def generate_terrain(self, world, surface, x, dx):
        land = generate_noise(15, 25, 1, dx)
        stone = generate_noise(10, 25, 3, dx)

        for i, (val1, val2) in enumerate(zip(land, stone)):
            land_h = world.surface_h + val1
            stone_h = world.underground + val2
            fill_chunk(world.blocks, x + i, 1, land_h, stone_h - land_h, tiles.DIRT)
            fill_chunk(world.blocks, x + i, 1, stone_h, world.dim[1] - stone_h, tiles.STONE)
            surface[x + i] = land_h
            chance = 75
            dy = 0
            while randint(1, 100) <= chance / pow(2, dy):
                world.blocks[land_h + dy, x + i] = tiles.SNOW
                dy += 1

    def get_ore_type(self, h_frac):
        chances_i = {tiles.SHINY_STONE_1: 45, tiles.SHINY_STONE_2: 25, tiles.GEODE: 30}
        chances_f = {tiles.SHINY_STONE_1: 20, tiles.SHINY_STONE_2: 25, tiles.GEODE: 55}
        return random_ore(h_frac, .66, 1, chances_i, chances_f)


class Valley(Biome):
    BOULDERS = [tiles.BOULDER1, tiles.BOULDER2, tiles.BOULDER3]

    def __init__(self):
        super().__init__(items.VALLEY)
        self.cave_freq = self.cave_freq * 3 // 4
        self.ore_freq *= 2
        self.ore_w_range = self.ore_h_range = [1, 4]

    def generate_terrain(self, world, surface, x, dx):
        land = generate_noise(50, min(dx // 2, 75), 1, dx)
        stone = generate_noise(10, 25, 3, dx)

        free = 0
        for i, (val1, val2) in enumerate(zip(land, stone)):
            land_h = world.surface_h + val1
            stone_h = world.underground + val2
            fill_chunk(world.blocks, x + i, 1, land_h, stone_h - land_h, tiles.DIRT)
            fill_chunk(world.blocks, x + i, 1, stone_h, world.dim[1] - stone_h, tiles.STONE)
            surface[x + i] = land_h
            if randint(1, 200) <= math.sqrt(abs(val1)):
                world.blocks[land_h + randint(1, 3)][x + i] = tiles.ZOMBIE
            if free < i and randint(1, 20) == 1:
                w = 0
                while w < 2 and i + w + 1 < len(land) and val1 == land[i + w + 1]:
                    w += 1
                idx = self.BOULDERS[randint(0, w)]
                w, h = game_vars.tiles[idx].dim
                fill_chunk(world.blocks, x + i, w, land_h, -h, tiles.AIR)
                world.blocks[land_h - h, x + i] = idx
                free = i + w

    def get_ore_type(self, h_frac):
        chances_i = {tiles.SHINY_STONE_2: 65, tiles.SHINY_STONE_3: 35}
        chances_f = {tiles.SHINY_STONE_2: 30, tiles.SHINY_STONE_3: 70}
        return random_ore(h_frac, .66, 1, chances_i, chances_f)


class Desert(Biome):
    def __init__(self):
        super().__init__(items.DESERT)

    def generate_terrain(self, world, surface, x, dx):
        land = generate_noise(20, 20, 3, dx)
        stone = generate_noise(10, 25, 3, dx)

        for i, (val1, val2) in enumerate(zip(land, stone)):
            land_h = world.surface_h + val1
            stone_h = world.underground + val2
            fill_chunk(world.blocks, x + i, 1, land_h, stone_h - land_h, tiles.SAND)
            fill_chunk(world.blocks, x + i, 1, stone_h, world.dim[1] - stone_h, tiles.STONE)
            surface[x + i] = land_h

    def get_ore_type(self, h_frac):
        return tiles.SAND if uniform(0, 10 * (h_frac - .66)) <= 1 else tiles.SHINY_STONE_1


# Returns random ore type with chances scaling based on height
# Takes in current height, height range, initial ore chances (@h=hmin),
# and final ore chances (@h=hmax)
def random_ore(h, h_min, h_max, chances_i, chances_f):
    h_frac = min(max((h - h_min) / h_max, 0), 1)
    chances = {}
    total_chance = 0
    for key in chances_i.keys():
        if key in chances_f.keys():
            chances[key] = (chances_f[key] - chances_i[key]) * h_frac + chances_i[key]
            total_chance += chances[key]
    num = uniform(0, total_chance)
    for key in chances.keys():
        if num <= chances[key]:
            return key
        else:
            num -= chances[key]


DRAGON_LAIR = 0


class DragonLair(Structure):
    def __init__(self):
        super().__init__(DRAGON_LAIR)
        self.biome_reqs = [items.FOREST]

    def get_rect(self, world_dim, surface):
        r = randint(20, 25)
        w, h = r * 2, r
        if random_sign() == -1:
            left = world_dim[0] // 2 - randint(world_dim[0] // 6 + w, world_dim[0] // 2)
        else:
            left = world_dim[0] // 2 + randint(world_dim[0] // 6, world_dim[0] // 2 - w)
        return Rect(left, surface[left] - h, w, h)

    def generate_structure(self, world, surface, rect):
        r = rect.w // 2
        left_side = rect.left <= world.dim[0] // 2
        for x in range(rect.left, rect.right):
            dx = x + .5 - rect.centerx
            dy = int(math.sqrt(r * r - dx * dx))
            dirt = min(dy, randint(3, 5))
            # From top to bottom: Air, Dirt, Stone
            arr = [tiles.AIR] * (rect.h - dy) + [tiles.DIRT] * dirt + [tiles.STONE] * (dy - dirt)
            # Check if we need to add air in the cave
            r_ = r / 3
            if -r_ < dx < r_:
                dh = int(math.sqrt(r_ * r_ - dx * dx))
                arr[-dh:] = [tiles.AIR] * dh
            if (dx <= r_ and not left_side) or (dx >= r_ and left_side):
                arr[-3:] = [tiles.AIR] * 3
            # Check to add stone pedestal and dragon egg
            if -.5 <= dx <= 1.5:
                arr[-1] = tiles.STONE
                if dx == .5:
                    arr[-2] = tiles.DRAGON_EGG
            # Add array
            world.blocks[rect.top:rect.bottom, x] = arr
            # Check if we need to fill in ground
            if surface[x] > rect.bottom:
                block_type = world.blocks[surface[x], x]
                fill_chunk(world.blocks, x, 1, rect.bottom, surface[x] - rect.bottom, block_type)
