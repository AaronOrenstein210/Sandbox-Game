# Created on 31 October 2019
# Defines functions and variables for handling items

from sys import byteorder
from numpy import full, int16
from math import ceil
from pygame import Surface
from pygame.draw import rect as draw_rect
from pygame.locals import *
from Tools.constants import INV_W, INV_IMG_W
from Tools import constants as c
from Tools import objects as o

BKGROUND = (0, 255, 0, 64)


class Inventory:
    def __init__(self):
        self.dim = (10, 5)
        self.rect = Rect(0, 0, INV_W * self.dim[0], INV_W * self.dim[1])
        self.surface = Surface((INV_W * self.dim[0], INV_W * self.dim[1]), SRCALPHA)
        self.surface.fill(BKGROUND)
        # Contains all items in the inventory
        self.inv_items = full((self.dim[1], self.dim[0]), -1, dtype=int16)
        self.inv_amnts = full((self.dim[1], self.dim[0]), 0, dtype=int16)
        # How long we've been right clicking
        self.holding_r = 0

    def load(self, data):
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                self.inv_amnts[y][x] = int.from_bytes(data[:2], byteorder)
                if self.inv_amnts[y][x] == 0:
                    self.inv_items[y][x] = -1
                else:
                    self.inv_items[y][x] = int.from_bytes(data[2:4], byteorder)
                data = data[4:]
        self.draw_inventory()

    def write(self):
        data = bytearray(4 * self.dim[0] * self.dim[1])
        pos = 0
        for y, (row1, row2) in enumerate(zip(self.inv_amnts, self.inv_items)):
            for x, (amnt, item) in enumerate(zip(row1, row2)):
                amnt, item = int(amnt), int(item)
                if item == -1 or amnt <= 0:
                    data[pos:pos + 4] = (0).to_bytes(4, byteorder)
                else:
                    data[pos: pos + 2] = amnt.to_bytes(2, byteorder)
                    data[pos + 2:pos + 4] = item.to_bytes(2, byteorder)
                pos += 4
        return data

    def draw_inventory(self):
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                # Update item
                self.update_item(y, x)
                # Draw black border
                draw_rect(self.surface, SRCALPHA,
                          (x * INV_W, y * INV_W, INV_W, INV_W), (INV_W - INV_IMG_W) // 2)

    def update_item(self, y, x):
        rect = Rect(0, 0, INV_IMG_W, INV_IMG_W)
        rect.center = ((x + .5) * INV_W, (y + .5) * INV_W)
        draw_rect(self.surface, BKGROUND, rect)
        val = self.inv_items[y][x]
        if val != -1:
            img = o.items[val].inv_img
            img_rect = img.get_rect(center=rect.center)
            self.surface.blit(img, img_rect)
            text = c.inv_font.render(str(self.inv_amnts[y][x]), 1, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.bottomright = rect.bottomright
            self.surface.blit(text, text_rect)

    def left_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        inv = o.player.inventory
        item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
        # Remove whatever item our mouse was over from the inventory
        if inv.selected_item == -1:
            if self.inv_items[y][x] == -1:
                return 0
            inv.selected_item, inv.selected_amnt = self.inv_items[y][x], self.inv_amnts[y][x]
            self.inv_items[y][x] = -1
            self.inv_amnts[y][x] = 0
        else:
            # Add selected item to inventory
            if inv.selected_item == item:
                max_stack = o.items[item].max_stack
                amnt_ = min(max_stack, amnt + inv.selected_amnt)
                self.inv_amnts[y][x] = amnt_
                inv.selected_amnt -= amnt_ - amnt
                if inv.selected_amnt == 0:
                    inv.selected_item = -1
            # Swap out items
            else:
                new_item = [self.inv_items[y][x], self.inv_amnts[y][x]]
                self.inv_items[y][x], self.inv_amnts[y][x] = inv.selected_item, inv.selected_amnt
                inv.selected_item, inv.selected_amnt = new_item
        self.update_item(y, x)
        return 500

    def right_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
        # Make sure we clicked on an item
        if amnt > 0:
            inv = o.player.inventory
            ideal_grab = ceil(o.dt / self.calc_wait_time())
            max_grab = o.items[item].max_stack - inv.selected_amnt
            grab_amnt = min(ideal_grab, max_grab, amnt)
            if grab_amnt > 0:
                inv.selected_item = item
                inv.selected_amnt += grab_amnt
                self.inv_amnts[y][x] -= grab_amnt
                if self.inv_amnts[y][x] == 0:
                    self.inv_items[y][x] = -1
                self.holding_r += o.dt
                self.update_item(y, x)
                return self.calc_wait_time()
        self.holding_r = 0
        return 0

    def calc_wait_time(self):
        # min 1 second
        return 1000 / (self.holding_r / 100 + 1)


def new_inventory(dim):
    return bytearray(4 * dim[0] * dim[1])
