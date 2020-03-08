# Created on 31 October 2019
# Defines functions and variables for handling items

from sys import byteorder
from time import time
from numpy import full, int16
from math import ceil
import pygame as pg
from pygame.locals import *
from Tools.constants import INV_W, INV_IMG_W
from Tools import constants as c
from Tools import game_vars

BKGROUND = (0, 255, 0, 64)


class Inventory:
    def __init__(self, dim, items_list=(), max_stack=999):
        self.dim = dim
        self.items_list = items_list
        self.max_stack = max_stack
        self.rect = Rect(0, 0, INV_W * self.dim[0], INV_W * self.dim[1])
        self.surface = pg.Surface((INV_W * self.dim[0], INV_W * self.dim[1]), SRCALPHA)
        self.surface.fill(BKGROUND)
        # Contains all items in the inventory
        self.inv_items = full((self.dim[1], self.dim[0]), -1, dtype=int16)
        self.inv_amnts = full((self.dim[1], self.dim[0]), 0, dtype=int16)
        # Stores [row,col]:bytes pairs
        self.inv_data = {}
        # How long we've been right clicking
        self.holding_r = 0

    @property
    def num_bytes(self):
        return 4 * self.dim[0] * self.dim[1] + sum(len(data) for data in self.inv_data.values())

    # Loads the inventory and returns leftover data
    def load(self, data):
        if len(data) < self.dim[0] * self.dim[1]:
            print("Missing item/amount data")
            return
        # Load items
        error = False
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                if len(data) < 4:
                    print("Missing data at row {} / {}, col {} / {}".format(y, self.dim[1], x, self.dim[0]))
                    error = True
                    break
                val = int.from_bytes(data[2:4], byteorder)
                # Item defaults to nothing if it doesn't exist
                if val not in game_vars.items.keys():
                    self.inv_amnts[y][x] = 0
                    self.inv_items[y][x] = -1
                else:
                    self.inv_amnts[y][x] = int.from_bytes(data[:2], byteorder)
                    if self.inv_amnts[y][x] == 0:
                        self.inv_items[y][x] = -1
                    else:
                        self.inv_items[y][x] = val
                        # Check for item data
                        if game_vars.items[val].has_data:
                            data = data[4:]
                            # Get length of data
                            if len(data) < 2:
                                print("Missing bytes for item data as row {}, col {}".format(y, x))
                                error = True
                                break
                            length = int.from_bytes(data[:2], byteorder)
                            # Get data
                            if len(data) < length + 2:
                                print("Missing bytes for item data as row {}, col {}".format(y, x))
                                error = True
                                break
                            self.inv_data[(x, y)] = data[2:length + 2]
                            data = data[length + 2:]
                            # Continue because we already took off 4 bytes
                            continue
                data = data[4:]
            if error:
                break
        self.draw_inventory()
        return data

    # Format what(#bytes): amnt(2) item(2) [length(2) data(length)] ...
    def write(self):
        data = bytearray()
        for y, (row1, row2) in enumerate(zip(self.inv_amnts, self.inv_items)):
            for x, (amnt, item) in enumerate(zip(row1, row2)):
                amnt, item = int(amnt), int(item)
                if item == -1 or amnt <= 0:
                    data += bytearray(4)
                else:
                    data += amnt.to_bytes(2, byteorder)
                    data += item.to_bytes(2, byteorder)
                    # Check if this item saves extra data
                    if game_vars.items[item].has_data:
                        # Get the data
                        item_data = self.inv_data[(x, y)]
                        # If it exists, save it
                        if item_data:
                            data += len(item_data).to_bytes(2, byteorder)
                            data += item_data
                        # Otherwise, indicate that the data has length 0
                        else:
                            data += bytearray(2)
        return data

    def draw_inventory(self):
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                # Update item
                self.update_item(y, x)
                # Draw black border
                pg.draw.rect(self.surface, SRCALPHA,
                             (x * INV_W, y * INV_W, INV_W, INV_W), (INV_W - INV_IMG_W) // 2)

    def update_item(self, y, x):
        rect = Rect(0, 0, INV_IMG_W, INV_IMG_W)
        rect.center = ((x + .5) * INV_W, (y + .5) * INV_W)
        pg.draw.rect(self.surface, BKGROUND, rect)
        val = self.inv_items[y][x]
        if val != -1:
            img = game_vars.items[val].inv_img
            img_rect = img.get_rect(center=rect.center)
            self.surface.blit(img, img_rect)
            text = c.inv_font.render(str(self.inv_amnts[y][x]), 1, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.bottomright = rect.bottomright
            self.surface.blit(text, text_rect)

    # Draws the description for the item under the given position
    def draw_hover_item(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        # Make sure were are over  legitimate position
        if 0 <= x < self.inv_items.shape[1] and 0 <= y < self.inv_items.shape[0]:
            # Make sure there is an item there
            item = self.inv_items[y][x]
            if item != -1:
                game_vars.items[item].draw_description(self.inv_data.get((x, y)))

    def left_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        inv = game_vars.player.inventory
        item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
        data = self.inv_data.get((x, y))
        # Stop if he are holding nothing and clicked on nothing
        if inv.selected_amnt == 0 and amnt == 0:
            return
        # Pick up item
        if inv.selected_amnt == 0:
            # Add item to selected item
            inv.selected_item, inv.selected_amnt = item, amnt
            inv.selected_data = data
            # Remove item from our inventory
            self.inv_items[y][x] = -1
            self.inv_amnts[y][x] = 0
            self.inv_data[(x, y)] = None
        elif len(self.items_list) == 0 or inv.selected_item in self.items_list:
            # Add item to item or to empty slot
            if (inv.selected_item == item and inv.selected_data == data) or amnt == 0:
                if amnt == 0:
                    max_stack = self.max_stack
                else:
                    max_stack = min(game_vars.items[item].max_stack, self.max_stack)
                amnt_ = min(max_stack, amnt + inv.selected_amnt)
                self.inv_amnts[y][x] = amnt_
                self.inv_items[y][x] = inv.selected_item
                self.inv_data[(x, y)] = inv.selected_data
                inv.selected_amnt -= amnt_ - amnt
                if inv.selected_amnt == 0:
                    inv.selected_item = -1
                    inv.selected_data = None
            # Swap out items
            elif inv.selected_amnt <= self.max_stack:
                self.inv_items[y][x], self.inv_amnts[y][x] = inv.selected_item, inv.selected_amnt
                self.inv_data[(x, y)] = inv.selected_data
                inv.selected_item, inv.selected_amnt = item, amnt
                inv.selected_data = data
        # If the item changed, redraw
        if self.inv_amnts[y][x] != amnt or self.inv_items[y][x] != item:
            self.update_item(y, x)
            game_vars.player.use_time = .3

    def right_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
        data = self.inv_data.get((x, y))
        inv = game_vars.player.inventory
        # Make sure we can pickup the clicked item
        same_item = inv.selected_item == item and inv.selected_data == data
        if amnt > 0 and (inv.selected_amnt == 0 or same_item):
            # Calculate wait time
            t = time()
            wait_time = (t - self.holding_r) * 19 // 20
            if wait_time > 1:
                wait_time = 1
            elif wait_time < .01:
                wait_time = .01
            self.holding_r = t
            # Do click
            ideal_grab = ceil(game_vars.dt / wait_time)
            max_grab = game_vars.items[item].max_stack - inv.selected_amnt
            grab_amnt = min(ideal_grab, max_grab, amnt)
            if grab_amnt > 0:
                # Updata inventory
                self.inv_amnts[y][x] -= grab_amnt
                if self.inv_amnts[y][x] == 0:
                    self.inv_items[y][x] = -1
                    self.inv_data[(x, y)] = None
                # Update selected item, first check if we need to pass item data
                if inv.selected_amnt == 0:
                    inv.selected_data = data
                inv.selected_item = item
                inv.selected_amnt += grab_amnt
                self.update_item(y, x)
                game_vars.player.use_time = wait_time

    def is_empty(self):
        for amnt in self.inv_amnts.flatten():
            if amnt != 0:
                return False
        return True


def new_inventory(dim):
    return bytearray(4 * dim[0] * dim[1])
