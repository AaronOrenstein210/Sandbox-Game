# Created on 31 October 2019
# Defines functions and variables for handling items

from sys import byteorder
from numpy import full, int16
from math import ceil
import pygame as pg
from pygame.locals import *
from Tools.constants import INV_W, INV_IMG_W
from Tools import constants as c
from Tools import game_vars

BKGROUND = (0, 255, 0, 64)


class Inventory:
    def __init__(self, dim, whitelist=(), max_stack=999):
        self.dim = dim
        self.whitelist = whitelist
        self.max_stack = max_stack
        self.rect = Rect(0, 0, INV_W * self.dim[0], INV_W * self.dim[1])
        self.surface = pg.Surface((INV_W * self.dim[0], INV_W * self.dim[1]), SRCALPHA)
        self.surface.fill(BKGROUND)
        # Contains all items in the inventory
        self.inv_items = full((self.dim[1], self.dim[0]), -1, dtype=int16)
        self.inv_amnts = full((self.dim[1], self.dim[0]), 0, dtype=int16)
        # Stores (col,row):bytes pairs
        self.inv_data = {}
        # How long we've been right clicking
        self.holding_r = 0

    @property
    def num_bytes(self):
        return 4 * self.dim[0] * self.dim[1] + sum(len(data) for data in self.inv_data.values())

    # Returns wait time after right clicking as a function of time spent right clicking
    @property
    def wait_time(self):
        return max(.75 / (self.holding_r + 1), .01)

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

    # Functions to set inventory slot values
    def set_at(self, row, col, item=-1, amnt=0, data=None):
        if 0 <= row < self.dim[1] and 0 <= col < self.dim[0]:
            if amnt <= 0 or item == -1:
                amnt = 0
                item = -1
                data = None
            self.inv_amnts[row][col] = amnt
            self.inv_items[row][col] = item
            self.inv_data[(col, row)] = data
            self.update_item(row, col)

    def set_item_at(self, row, col, item=-1):
        if 0 <= row < self.dim[1] and 0 <= col < self.dim[0]:
            self.inv_items[row][col] = item
            if item == -1:
                self.inv_amnts[row][col] = 0
                self.inv_data[(col, row)] = None
            self.update_item(row, col)

    def set_amnt_at(self, row, col, amnt=0):
        if 0 <= row < self.dim[1] and 0 <= col < self.dim[0]:
            self.inv_amnts[row][col] = amnt
            if amnt <= 0:
                self.inv_items[row][col] = -1
                self.inv_data[(col, row)] = None
            self.update_item(row, col)

    def set_data_at(self, row, col, data=None):
        if 0 <= row < self.dim[1] and 0 <= col < self.dim[0]:
            self.inv_data[(col, row)] = data

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
            inv.set_at(-1, -1, item=item, amnt=amnt, data=data)
            # Remove item from our inventory
            self.set_at(y, x)
        elif len(self.whitelist) == 0 or inv.selected_item in self.whitelist:
            # Add item to item or to empty slot
            if (inv.selected_item == item and inv.selected_data == data) or amnt == 0:
                if amnt == 0:
                    max_stack = self.max_stack
                else:
                    max_stack = min(game_vars.items[item].max_stack, self.max_stack)
                amnt_ = min(max_stack, amnt + inv.selected_amnt)
                self.set_at(y, x, item=inv.selected_item, amnt=amnt_, data=inv.selected_data)
                inv.set_amnt_at(-1, -1, amnt=inv.selected_amnt - (amnt_ - amnt))
            # Swap out items
            elif inv.selected_amnt <= self.max_stack:
                self.set_at(y, x, item=inv.selected_item, amnt=inv.selected_amnt, data=inv.selected_data)
                inv.set_at(-1, -1, item=item, amnt=amnt, data=data)
        # If the item changed, set use time
        if self.inv_amnts[y][x] != amnt or self.inv_items[y][x] != item:
            game_vars.player.use_time = .3

    def right_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
        data = self.inv_data.get((x, y))
        inv = game_vars.player.inventory
        # Make sure we can pickup the clicked item
        same_item = inv.selected_item == item and inv.selected_data == data
        if amnt > 0 and (inv.selected_amnt == 0 or same_item):
            # If we haven't held down right, just add dt
            if self.holding_r == 0:
                self.holding_r += game_vars.dt
            # Otherwise, add the time since we last processed a right click
            else:
                self.holding_r += self.wait_time
            wait_time = self.wait_time
            # Do click
            ideal_grab = ceil(game_vars.dt / wait_time)
            max_grab = game_vars.items[item].max_stack - inv.selected_amnt
            grab_amnt = min(ideal_grab, max_grab, amnt)
            if grab_amnt > 0:
                # Update inventory
                self.set_amnt_at(y, x, amnt=self.inv_amnts[y][x] - grab_amnt)
                # Update selected item, first check if we need to set item data and type
                if inv.selected_amnt == 0:
                    inv.set_at(-1, -1, item=item, amnt=grab_amnt, data=data)
                else:
                    inv.set_amnt_at(-1, -1, amnt=inv.selected_amnt + grab_amnt)
                game_vars.player.use_time = wait_time

    def is_empty(self):
        for amnt in self.inv_amnts.flatten():
            if amnt != 0:
                return False
        return True


def new_inventory(dim):
    return bytearray(4 * dim[0] * dim[1])
