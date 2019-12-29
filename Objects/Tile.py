# Created on 4 December 2019
# Defines functions and variables for Tile objects


from os.path import isfile
import pygame as pg
from random import randint
from Tools.constants import BLOCK_W, scale_to_fit
from Tools import objects as o
from Objects.tile_ids import AIR
from Objects.ItemTypes import Block


class Tile:
    def __init__(self, idx, hardness=0, img="", dim=(1, 1),
                 item_idx=0, item_name="", item_img=""):
        self.idx = idx
        self.hardness = hardness
        self.dim = dim

        # Tile spawns enemies
        self.spawner = False
        # Tile is interactable
        self.clickable = False
        # Tile brings up a ui when clicked
        self.has_ui = False
        # Has animation
        self.animation = False
        # Must be placed on a surface
        self.on_surface = False
        # Player can craft at this item
        self.crafting = False

        # Minimap color, does not need to be unique
        self.map_color = (64, 64, 255)
        # Load image if given
        img_dim = (BLOCK_W * dim[0], BLOCK_W * dim[1])
        if isfile(img):
            self.image = scale_to_fit(pg.image.load(img), *img_dim)
        else:
            self.image = pg.Surface(img_dim)

        # Number of bytes of data
        self.data_bytes = 0
        # List of drops, each drop is a item/amnt pair
        self.drops = []
        # Recipes for crafting blocks
        self.recipes = []

        # Add tile to list
        o.tiles[self.idx] = self
        # Add corresponding item to list
        if item_img == "":
            item_img = img
        self.create_item(item_idx, item_img, item_name)

    # Creates a generic item whiche places this block and shares this block's image resource
    # You can just create a generic block item or create a custom class and instantiate it
    def create_item(self, idx, img, name):
        Block(idx, self.idx, inv_img=img, name=name)

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
        if not o.world.contains_only(*pos, *self.dim, AIR):
            return False
        if self.on_surface:
            return not o.world.contains(pos[0], pos[1] + self.dim[1], self.dim[0], 1, AIR)
        else:
            return not o.world.adjacent(*pos, *self.dim, AIR, True)

    def activate(self, pos):
        pass
