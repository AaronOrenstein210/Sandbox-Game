# Created on 31 October 2019
# Defines functions and variables for handling items

from sys import byteorder
from numpy import full, int16
from math import ceil
from pygame import Surface
from pygame.draw import rect as draw_rect
from pygame.locals import *
from Tools.lists import items
from Tools.constants import INV_W
from Tools import constants as c

hotbar_controls = {
    K_1: 0, K_2: 1, K_3: 2, K_4: 3,
    K_5: 4, K_6: 5, K_7: 6, K_8: 7,
    K_9: 8, K_0: 9
}

IMG_W = INV_W * 4 // 5
BKGROUND = (0, 255, 0, 64)


class Inventory:
    def __init__(self):
        self.dim = (10, 5)
        self.rect = Rect(0, 0, INV_W * self.dim[0], INV_W)
        self.surface = Surface((INV_W * self.dim[0], INV_W * self.dim[1]), SRCALPHA)
        self.surface.fill(BKGROUND)
        # Contains all items in the inventory
        self.inv_items = full((self.dim[1], self.dim[0]), -1, dtype=int16)
        self.inv_amnts = full((self.dim[1], self.dim[0]), 0, dtype=int16)
        # Defines current selected item
        self.selected_item, self.selected_amnt = -1, 0
        # Defines current hotbar item
        self.hot_bar_item = -1
        # Checks if the inventory is open or not
        self.open = False
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
        self.select_hotbar(0)

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

    def toggle(self):
        self.open = not self.open
        self.rect.h = INV_W * (self.dim[1] if self.open else 1)

    def draw_inventory(self):
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                # Update item
                self.update_item(y, x)
                # Draw black border
                draw_rect(self.surface, SRCALPHA, (x * INV_W, y * INV_W, INV_W, INV_W), (INV_W - IMG_W) // 2)

    def update_item(self, y, x):
        rect = Rect(0, 0, IMG_W, IMG_W)
        rect.center = ((x + .5) * INV_W, (y + .5) * INV_W)
        draw_rect(self.surface, BKGROUND, rect)
        val = self.inv_items[y][x]
        if val != -1:
            img = items[val].get_icon_display(IMG_W)
            img_rect = img.get_rect(center=rect.center)
            self.surface.blit(img, img_rect)
            text = c.inv_font.render(str(self.inv_amnts[y][x]), 1, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.bottomright = rect.bottomright
            self.surface.blit(text, text_rect)

    def select_hotbar(self, idx):
        if idx != self.hot_bar_item:
            if self.hot_bar_item != -1:
                draw_rect(self.surface, BKGROUND, (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.hot_bar_item = idx
            draw_rect(self.surface, (128, 128, 0), (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)

    def left_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        if self.open:
            item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
            # Remove whatever item our mouse was over from the inventory
            if self.selected_item == -1:
                self.selected_item, self.selected_amnt = self.inv_items[y][x], self.inv_amnts[y][x]
                self.inv_items[y][x] = -1
                self.inv_amnts[y][x] = 0
            else:
                # Add selected item to inventory
                if self.selected_item == item:
                    max_stack = items[item].max_stack
                    amnt_ = min(max_stack, amnt + self.selected_amnt)
                    self.inv_amnts[y][x] = amnt_
                    self.selected_amnt -= amnt_ - amnt
                    if self.selected_amnt == 0:
                        self.selected_item = -1
                # Swap out items
                else:
                    new_item = [self.inv_items[y][x], self.inv_amnts[y][x]]
                    self.inv_items[y][x], self.inv_amnts[y][x] = self.selected_item, self.selected_amnt
                    self.selected_item, self.selected_amnt = new_item
            self.update_item(y, x)
            return .5
        else:
            self.select_hotbar(x)
        return 0

    def right_click(self, pos, dt):
        if self.open:
            x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
            item, amnt = self.inv_items[y][x], self.inv_amnts[y][x]
            # Make sure we clicked on an item
            if amnt > 0:
                wait_time = 1 / (15 * self.holding_r + 1)
                grab_amnt = min(ceil(dt / wait_time / 1000), items[item].max_stack - self.selected_amnt, amnt)
                if grab_amnt > 0:
                    self.selected_item = item
                    self.selected_amnt += grab_amnt
                    self.inv_amnts[y][x] -= grab_amnt
                    if self.inv_amnts[y][x] == 0:
                        self.inv_items[y][x] = -1
                    self.holding_r += dt / 1000
                    self.update_item(y, x)
                    return 1 / (10 * self.holding_r + 1)
        self.holding_r = 0
        return 0

    def get_cursor_display(self):
        return items[self.selected_item].get_dropped_display() if self.selected_item != -1 else None

    def get_held_item(self):
        return self.selected_item if self.selected_item != -1 else self.inv_items[0][self.hot_bar_item]

    def use_item(self):
        # We are using an item held by the cursor
        if self.selected_item != -1:
            # Reduce its amount and check if we have any left
            self.selected_amnt -= 1
            if self.selected_amnt == 0:
                self.selected_item = -1
        # Using an item from our hot bar
        else:
            # Reduce its amount and check if we have any left
            self.inv_amnts[0][self.hot_bar_item] -= 1
            if self.inv_amnts[0][self.hot_bar_item] == 0:
                self.inv_items[0][self.hot_bar_item] = -1
            self.update_item(0, self.hot_bar_item)

    def key_pressed(self, key, up):
        global hotbar_controls
        if not up and key == K_ESCAPE:
            self.toggle()
        elif key in hotbar_controls.keys():
            self.select_hotbar(hotbar_controls[key])

    def scroll(self, up):
        self.select_hotbar(min(max(0, self.hot_bar_item + (-1 if up else 1)), 9))

    def drop_item(self):
        drop = None
        if self.selected_item != -1:
            drop = (self.selected_item, self.selected_amnt)
            self.selected_item = -1
            self.selected_amnt = 0
        return drop

    def room_for_item(self, item):
        empty = []
        good = []
        item_amnt = item.amnt
        for y, row in enumerate(self.inv_items):
            for x, val in enumerate(row):
                amnt = self.inv_amnts[y][x]
                if val == -1:
                    empty.append((x, y))
                elif val == item.idx and amnt != item.max_stack:
                    if amnt + item_amnt <= item.max_stack:
                        return [(x, y)]
                    else:
                        good.append((x, y))
                        item_amnt -= item.max_stack - amnt
        return good + empty[:1]

    def pick_up_item(self, item, space=None):
        if space is None:
            space = self.room_for_item(item)
        for x, y in space:
            # Add to existing item
            if self.inv_items[y][x] != -1:
                # Fill up item to max value
                if item.amnt + self.inv_amnts[y][x] > item.max_stack:
                    item.amnt -= item.max_stack - self.inv_amnts[y][x]
                    self.inv_amnts[y][x] = item.max_stack
                # Add all of the item
                else:
                    self.inv_amnts[y][x] += item.amnt
                    item.amnt = 0
            # Add to empty slot
            else:
                self.inv_items[y][x] = item.idx
                self.inv_amnts[y][x] = item.amnt
                item.amnt = 0
            # Update item
            self.update_item(y, x)
            # Check if we are done
            if item.amnt == 0:
                return True
        return False
