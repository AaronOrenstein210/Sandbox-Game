# Created on 23 November 2019

from random import random, uniform
from os.path import isfile, isdir
import pygame as pg
from random import randint
from Tools.constants import BLOCK_W, scale_to_fit, update_dict
from Tools import game_vars
from Tools.tile_ids import AIR
from Objects import INV
from Objects.ItemTypes import Block
from Objects.Animation import Animation


class Tile:
    def __init__(self, idx, hardness=0, img="", dim=(1, 1), anim_delay=.25):
        self.idx = idx
        self.hardness = hardness
        self.dim = dim

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
        # Has an animation
        self.anim_idx = -1

        # Minimap color, does not need to be unique
        self.map_color = (64, 64, 255)
        # Load image if given
        img_dim = (BLOCK_W * dim[0], BLOCK_W * dim[1])
        if isfile(img) and img.endswith(".png") or img.endswith(".jpg"):
            self.image = scale_to_fit(pg.image.load(img), *img_dim)
        elif isdir(img):
            self.anim_idx = len(game_vars.animations)
            game_vars.animations.append(Animation(img, img_dim, delay=anim_delay))
            self.image = game_vars.animations[-1].frames[0]
        else:
            self.image = pg.Surface(img_dim)

        # List of drops, each drop is a item/amnt pair
        self.drops = []
        # Recipes for crafting blocks
        self.recipes = []

        # Add tile to list
        game_vars.tiles[self.idx] = self

    # Return Animation object if tile has animation
    def get_animation(self):
        pass

    def add_drop(self, item, min_amnt, max_amnt=-1):
        if max_amnt == -1:
            max_amnt = min_amnt
        self.drops.append([item, min_amnt, max_amnt])

    # Return what items to drop
    def get_drops(self):
        drops = []
        for drop in self.drops:
            drops.append([drop[0], randint(drop[1], drop[2])])
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

    def activate(self, pos):
        pass


class CraftingStation(Tile):
    def __init__(self, idx, **kwargs):
        Tile.__init__(self, idx, **kwargs)
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
        Tile.__init__(self, idx, **kwargs)
        self.clickable = True
        self.has_ui = True
        self.has_data = True


# SpawnBlocks are blocks that spawn enemies
class SpawnTile(Tile):
    def __init__(self, idx, entity, item_id=-1):
        self.entity = entity
        self.rarity = self.entity.rarity
        img = INV + "spawner_{}.png".format(self.rarity)
        Tile.__init__(self, idx, hardness=self.rarity, img=img)
        self.spawner = True
        self.map_color = (0, 0, 200) if self.rarity == 0 else (128, 0, 255) if self.rarity == 1 else (255, 0, 0)
        if item_id != -1:
            Block(item_id, idx, name=self.entity.name + " Spawner", img=img)

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
