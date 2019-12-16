# Created on 4 December 2019
# Defines functions and variables for Tile objects


from os.path import isfile
import pygame as pg
from random import randint
from Tools.constants import BLOCK_W
from Tools import objects as o


class Tile:
    def __init__(self, idx, hardness=0, img=""):
        self.idx = idx
        self.name = "No Name"
        self.hardness = hardness

        # Tile spawns enemies
        self.spawner = False
        # Tile is interactable
        self.clickable = False
        # Tile brings up a ui when clicked
        self.has_ui = False

        # Minimap color, does not need to be unique
        self.map_color = (64,64,255)
        # Load image if given
        self.image = pg.Surface((BLOCK_W, BLOCK_W))
        if isfile(img):
            self.image = pg.transform.scale(pg.image.load(img), (BLOCK_W, BLOCK_W))

        # Number of bytes of data
        self.data_bytes = 0
        # List of drops, each drop is a item/amnt pair
        self.drops = []

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
        return

    def activate(self, pos):
        return
