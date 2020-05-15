# Created on 23 November 2019

from random import random, uniform
from os.path import isfile
import math
import pygame as pg
from random import randint
from Tools.constants import BLOCK_W, scale_to_fit, update_dict
from Tools import game_vars, constants as c
from Tools.tile_ids import AIR
from Objects import INV
from Objects.ItemTypes import Placeable, ItemInfo


class Tile:
    def __init__(self, idx, img="", dim=(1, 1)):
        self.idx = idx
        self.dim = dim

        # Hp and hardness of block
        self.hp = 0
        self.hardness = 0
        # Dictionaries of all world locations where a block has been damaged
        self.damage = {}

        # Tile stores data
        self.has_data = False
        # Tile spawns enemies
        self.spawner = False
        # Tile is interactable
        self.clickable = False
        # Tile brings up a ui when clicked
        self.has_ui = False
        # Must be placed on a surface
        self.on_surface = False
        # Player can craft at this item
        self.crafting = False
        # Image updates every tick
        self.img_updates = False
        # Emits light
        self.emits_light = False
        # Obstructs player movement
        self.barrier = True
        # Updates every tick
        self.updates = False

        # Minimap color, does not need to be unique
        self.map_color = (64, 64, 255)
        # Load image if given
        img_dim = (BLOCK_W * dim[0], BLOCK_W * dim[1])
        if isfile(img) and img.endswith(".png") or img.endswith(".jpg"):
            self.image = scale_to_fit(pg.image.load(img), *img_dim)
        else:
            self.image = pg.Surface(img_dim)

        # List of drops, each drop is a item/amnt pair
        self.drops = []
        # Recipes for crafting blocks
        self.recipes = []

        # Store index of animation here
        self.anim_idx = -1

        # Light magnitude and radius
        self.light_mag = 0
        self.light_r = 0
        # Light surface
        self.light_s = None

        # Add tile to list
        game_vars.tiles[self.idx] = self

    def tick(self, x, y, dt):
        pass

    def set_animation(self, animation):
        self.img_updates = True
        self.anim_idx = len(game_vars.animations)
        game_vars.animations.append(animation)
        self.image = animation.get_frame()

    # Return block image, default updates an animation if present
    def get_block_img(self, pos):
        data = game_vars.get_block_data(pos)
        if data and self.anim_idx != -1:
            self.image = game_vars.animations[self.anim_idx].get_frame()
        return self.image

    def add_drop(self, item, min_amnt, max_amnt=-1):
        if max_amnt == -1:
            max_amnt = min_amnt
        self.drops.append([item, min_amnt, max_amnt])

    # Return what items to drop
    def get_drops(self):
        drops = []
        for drop in self.drops:
            amnt = randint(drop[1], drop[2])
            if amnt > 0:
                drops.append(ItemInfo(drop[0], amnt))
        return drops

    # Called when block is broken, return True if successful,
    # false otherwise
    def on_break(self, pos):
        return True

    def on_place(self, pos):
        pass

    def can_place(self, pos):
        if not game_vars.contains_only(*pos, *self.dim, AIR):
            return False
        if self.on_surface:
            return not game_vars.contains(pos[0], pos[1] + self.dim[1], self.dim[0], 1, AIR)
        else:
            return not game_vars.adjacent(*pos, *self.dim, AIR, True)

    # Returns if the block was activated or not
    def activate(self, pos):
        return False

    # Hits the block with given power, returns if the block is broken or not
    def hit(self, x, y, power):
        # Check if we even do damage to the block
        if self.hardness == -1 or power < self.hardness:
            return False
        # Get current damage if available
        dmg = c.get_from_dict(x, y, self.damage)
        if dmg is None:
            dmg = 0
        # Update damage
        dmg += power - self.hardness + 1
        if dmg < self.hp:
            c.update_dict(x, y, dmg, self.damage)
            return False
        else:
            c.remove_from_dict(x, y, self.damage)
            return True


class CraftingStation(Tile):
    def __init__(self, idx, **kwargs):
        super().__init__(idx, **kwargs)
        self.barrier = False
        self.crafting = True
        self.recipes = self.get_recipes()
        i = 0
        # Optimize recipes and sort them
        while i < len(self.recipes):
            idxs = {}
            r = self.recipes[i]
            delete = False
            j = 0
            while not delete and j < len(r):
                item, amnt = r[j]
                # Repeat item, merge and delete
                if item in idxs.keys():
                    idx = idxs[item]
                    if idx == 0:
                        r[0][1] -= amnt
                        # This recipe produces nothing, remove it
                        if r[0][1] <= 0:
                            delete = True
                    else:
                        r[idx][1] += amnt
                    del r[j]
                else:
                    idxs[item] = j
                    j += 1
            if delete:
                del self.recipes[i]
            else:
                # Sort recipe ingredients
                ingredients = r[1:]
                ingredients.sort(key=lambda arr: arr[0])
                self.recipes[i] = [r[0]] + ingredients
                del ingredients
                i += 1

    def get_recipes(self):
        # Format = [[[result, amnt], [input1, amnt], [input2, amnt], ...], ...]
        return []


class FunctionalTile(Tile):
    def __init__(self, idx, **kwargs):
        super().__init__(idx, **kwargs)
        self.barrier = False
        self.clickable = True
        self.has_ui = True
        self.has_data = True


# SpawnBlocks are blocks that spawn enemies
class SpawnTile(Tile):
    def __init__(self, idx, entity, item_id=-1, **kwargs):
        self.entity = entity
        self.rarity = self.entity.rarity
        img = INV + "spawner_{}.png".format(self.rarity)
        super().__init__(idx, img=img, **kwargs)
        self.hardness = self.rarity
        self.spawner = True
        self.map_color = (0, 0, 200) if self.rarity == 0 else (128, 0, 255) if self.rarity == 1 else (255, 0, 0)
        if item_id != -1:
            Placeable(item_id, idx, name=self.entity.name + " Spawner", img=img)

    def spawn(self, pos, conditions):
        conditions.check_area(pos, 5 * self.rarity)
        if not self.entity.can_spawn(conditions.conditions):
            return
        air = get_spawn_spaces(pos, 5 * self.rarity, True)
        places = find_valid_spawns(air, *self.entity.dim)
        if len(places) > 0:
            chances = []
            for x_min, x_max, y in places:
                chances.append(x_max - x_min)
            num = random() * sum(chances)
            for idx, chance in enumerate(chances):
                if num < chance:
                    min_x, max_x, y = places[idx]
                    mob = type(self.entity)()
                    x = uniform(min_x, max_x - self.entity.dim[0])
                    y = y - self.entity.dim[1]
                    mob.set_pos(x * BLOCK_W, y * BLOCK_W)
                    return mob
                else:
                    num -= chance


# TODO: By row/col, not radius
class LightTile(Tile):
    def __init__(self, idx, magnitude=10, radius=5, **kwargs):
        super().__init__(idx, **kwargs)
        self.emits_light = True
        self.light_mag = magnitude
        self.light_r = int(max(min(radius, 255), 1) * BLOCK_W)
        # self.light_s = full((self.light_r * 2 + 1, self.light_r * 2 + 1), 0, dtype=uint8)
        self.light_s = pg.Surface((self.light_r * 2 + 1, self.light_r * 2 + 1), pg.SRCALPHA)
        for r in range(1, self.light_r + 1):
            dtheta = .5 / r
            theta = 0
            color_ = (0, 0, 0, 255 * (1 - (r / self.light_r) ** 2))
            while theta < 2 * math.pi:
                x, y = int(r * math.cos(theta)) + self.light_r, int(r * math.sin(theta)) + self.light_r
                self.light_s.set_at((x, y), color_)
                # self.light_s[x][y] = 255 - 255 * (r / self.light_r) ** 2
                theta += dtheta


class Block:
    def __init__(self, pos, idx, data):
        self.x, self.y = pos
        self.idx = idx
        self.data = data


def get_spawn_spaces(center, r, walking):
    # X range
    v1_min, v1_max = max(0, center[0] - r), min(game_vars.world_dim()[0] - 1, center[0] + r)
    # When calculating max, add 1 so that if we have only air but
    # there is a solid block just outside our range, we can still spawn
    # Y range
    v2_min, v2_max = max(0, center[1] - r), min(game_vars.world_dim()[1] - 1, center[1] + r + 1)
    air = {}

    # For all ranges, use max + 1 to be inclusive
    for v1 in range(v1_min, v1_max + 1):
        air_count = -1
        v2 = 0
        for v2 in reversed(range(v2_min, v2_max + 1)):
            block = game_vars.get_block_at(*(v1, v2) if walking else (v2, v1))
            if block != AIR:
                if air_count > 0:
                    # Coords of ground = current (solid) + 1 + air count
                    update_dict(v1, v2 + 1 + air_count, air_count, air)
                air_count = 0
            elif air_count != -1:
                air_count += 1
        if air_count > 0:
            # Coord of ground = current (air) + air count
            update_dict(v1, v2 + air_count, air_count, air)
    return air


def find_valid_spawns(air, dim1, dim2):
    spawns = []
    v1_vals = air.keys()
    for v1 in v1_vals:
        min_v1 = v1
        # v2 is the coordinate of the ground solid block
        v2_vals = air[v1].keys()
        for v2 in v2_vals:
            while v1 in v1_vals and v2 in air[v1].keys() and air[v1][v2] >= dim2:
                if v1 != min_v1:
                    air[v1].pop(v2)
                v1 += 1
            if v1 - min_v1 >= dim1:
                spawns.append((min_v1, v1, v2))
    return spawns
