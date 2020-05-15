# Created on 31 October 2019
# Defines functions and variables for handling items

from sys import byteorder
from math import ceil
import pygame as pg
from pygame.locals import *
from Objects.ItemTypes import ItemInfo
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
        self.inv_items = [[ItemInfo(-1, 0) for i in range(dim[0])] for j in range(dim[1])]
        # Inventory slots that need to be updated
        self.updates = []
        # How long we've been right clicking
        self.holding_r = 0

    @property
    def num_bytes(self):
        return sum(i.num_bytes for row in self.inv_items for i in row)

    # Returns wait time after right clicking as a function of time spent right clicking
    @property
    def wait_time(self):
        return max(.75 / (self.holding_r + 1), .01)

    @property
    def empty(self):
        return not any(i.is_item for row in self.inv_items for i in row)

    # Loads the inventory and returns leftover data
    def load(self, data):
        if not data or len(data) < self.dim[0] * self.dim[1]:
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
                item = ItemInfo(-1, 0)
                self.inv_items[y][x] = item
                item.item_id = int.from_bytes(data[:2], byteorder)
                # Item defaults to nothing if it doesn't exist
                if item.item_id not in game_vars.items.keys():
                    item.amnt = 0
                else:
                    item.amnt = int.from_bytes(data[2:4], byteorder)
                    if item.is_item:
                        # Check for item data
                        if game_vars.items[item.item_id].has_data:
                            # Get length of data
                            if len(data) < 6:
                                print("Missing bytes for item data as row {}, col {}".format(y, x))
                                error = True
                                break
                            length = int.from_bytes(data[4:6], byteorder)
                            # Get data
                            if len(data) < length + 6:
                                print("Missing bytes for item data as row {}, col {}".format(y, x))
                                error = True
                                break
                            item.data = data[6:length + 6]
                            data = data[length + 2:]
                data = data[4:]
            if error:
                break
        self.draw_inventory()
        return data

    # Format what(#bytes): item(2) amnt(2) [length(2) data(length)] ...
    def write(self):
        return b"".join(i.write() for row in self.inv_items for i in row)

    def draw_inventory(self):
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                # Update item
                self.update_item(y, x)
                # Draw black border
                pg.draw.rect(self.surface, SRCALPHA,
                             (x * INV_W, y * INV_W, INV_W, INV_W), (INV_W - INV_IMG_W) // 2)

    def draw(self, mouse_pos, parent_pos=(0, 0)):
        self.update()
        rect = self.rect.move(*parent_pos)
        pg.display.get_surface().blit(self.surface, rect)
        if rect.collidepoint(*mouse_pos):
            pos = [mouse_pos[0] - rect.x, mouse_pos[1] - rect.y]
            self.draw_hover_item(pos)

    # Draws the description for the item under the given position
    def draw_hover_item(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        # Make sure were are over legitimate position
        if 0 <= x < self.dim[0] and 0 <= y < self.dim[1]:
            # Make sure there is an item there
            item = self.inv_items[y][x]
            if item.is_item:
                game_vars.items[item.item_id].draw_description(item.data)

    # Call this to get the item at (row,col) and indicate that this item must be updated
    def get_item(self, row, col):
        if 0 <= col < self.dim[0] and 0 <= row < self.dim[1]:
            if (row, col) not in self.updates:
                self.updates.append((row, col))
            return self.inv_items[row][col]
        print("get_item(): Invalid item coords: {}, {}".format(col, row))
        return None

    def update(self):
        for (row, col) in self.updates:
            self.update_item(row, col)
            self.updates.remove((row, col))

    def update_item(self, y, x):
        rect = Rect(0, 0, INV_IMG_W, INV_IMG_W)
        rect.center = ((x + .5) * INV_W, (y + .5) * INV_W)
        pg.draw.rect(self.surface, BKGROUND, rect)
        item = self.inv_items[y][x]
        if item.is_item:
            img = game_vars.items[item.item_id].inv_img
            img_rect = img.get_rect(center=rect.center)
            self.surface.blit(img, img_rect)
            text = c.inv_font.render(str(item.amnt), 1, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.bottomright = rect.bottomright
            self.surface.blit(text, text_rect)

    # Automatically moves item to the player inventory
    def auto_move_item(self, row, col):
        # Make sure there is an item
        item = self.get_item(row, col)
        if item.is_item:
            # Try to get the player inventory to pick up the item
            game_vars.player.inventory.pick_up_item(item)
            # Since this is not the player inventory, try to update the current ui inventory
            if game_vars.player.active_ui:
                game_vars.player.active_ui.on_inv_pickup()

    # Check if there is room for the given item in inventory
    def room_for_item(self, item):
        # Make sure this item is in the whitelist
        if len(self.whitelist) > 0 and item.item_id not in self.whitelist:
            return []
        empty = []
        good = []
        item_amnt = item.amnt
        max_stack = min(item.max_stack, self.max_stack)
        for y, row in enumerate(self.inv_items):
            for x, inv_item in enumerate(row):
                if not inv_item.is_item:
                    empty.append((x, y))
                elif inv_item.same_as(item) and inv_item.amnt != max_stack:
                    if inv_item.amnt + item_amnt <= max_stack:
                        return good + [(x, y)]
                    else:
                        good.append((x, y))
                        item_amnt -= max_stack - inv_item.amnt
        return good + empty[:1]

    # Try to pick up the given item, returns if we picked up any of it
    def pick_up_item(self, item, space=None):
        max_stack = min(item.max_stack, self.max_stack)
        if space is None:
            space = self.room_for_item(item)
        for (x, y) in space:
            inv_item = self.get_item(y, x)
            # Add to existing item
            if inv_item.is_item:
                # Fill up item to max value
                if item.amnt + inv_item.amnt > max_stack:
                    item.amnt -= max_stack - inv_item.amnt
                    inv_item.amnt = max_stack
                # Add all of the item
                else:
                    inv_item.amnt += item.amnt
                    item.amnt = 0
            # Add to empty slot
            else:
                transfer = min(item.amnt, max_stack)
                inv_item.set_vals(item=item.item_id, amnt=transfer, data=item.data)
                item.amnt -= transfer
            self.on_pick_up(y, x)
            # Check if we are done
            if item.amnt == 0:
                return True
        return False

    # Defines what to do when an item is picked up
    # This is necessary as an inventory picking up an item is often not detectable
    def on_pick_up(self, row, col):
        pass

    # Get list of inventory contents, sorted by item id and duplicates combined
    def get_materials(self):
        results = []
        for row in self.inv_items:
            for item in row:
                if item.is_item:
                    # Special conditions
                    if len(results) == 0 or results[-1][0] < item.item_id:
                        results.append([item.item_id, item.amnt])
                    # Place item into results
                    else:
                        i = 0
                        while i < len(results) and results[i][0] < item.item_id:
                            i += 1
                        if results[i][0] == item.item_id:
                            results[i][1] += item.amnt
                        else:
                            results.insert(i, [item.item_id, item.amnt])
        return results

    def left_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        if not pg.key.get_mods() & KMOD_SHIFT:
            p_item = game_vars.player.inventory.get_held_item()
            item = self.get_item(y, x)
            prev = item.copy()
            # Stop if we are holding nothing and clicked on nothing
            if not (p_item.is_item or item.is_item):
                return
            # Pick up item
            if not p_item.is_item:
                # Add item to selected item
                p_item.set_vals(item=item.item_id, amnt=item.amnt, data=item.data)
                # Remove item from our inventory
                item.amnt = 0
            elif len(self.whitelist) == 0 or p_item.item_id in self.whitelist:
                # Add item to item or to empty slot
                if not item.is_item or (p_item.item_id == item.item_id and p_item.data == item.data):
                    max_stack = min(item.max_stack, self.max_stack) if item.is_item else self.max_stack
                    new_amnt = min(max_stack, item.amnt + p_item.amnt)
                    p_item.amnt -= new_amnt - item.amnt
                    item.set_vals(item=p_item.item_id, amnt=new_amnt, data=p_item.data)
                # Swap out items
                elif p_item.amnt <= self.max_stack:
                    item.set_info(p_item)
                    p_item.set_info(prev)
            # If the item changed, set use time
            if item != prev:
                game_vars.player.use_time = .3
        else:
            self.auto_move_item(y, x)

    def right_click(self, pos):
        x, y = int(pos[0] / INV_W), int(pos[1] / INV_W)
        item = self.get_item(y, x)
        p_item = game_vars.player_inventory().get_held_item()
        # Make sure we can pickup the clicked item
        if item.is_item and (not p_item.is_item or item.same_as(p_item)):
            # If we haven't held down right, just add dt
            if self.holding_r == 0:
                self.holding_r += game_vars.dt
            # Otherwise, add the time since we last processed a right click
            else:
                self.holding_r += self.wait_time
            wait_time = self.wait_time
            # Do click
            ideal_grab = ceil(game_vars.dt / wait_time)
            max_grab = item.max_stack - p_item.amnt
            grab_amnt = min(ideal_grab, max_grab, item.amnt)
            if grab_amnt > 0:
                # Update inventory
                item.amnt -= grab_amnt
                # Update selected item, first check if we need to set item data and type
                if p_item.is_item:
                    p_item.amnt += grab_amnt
                else:
                    p_item.set_vals(item=item.item_id, amnt=grab_amnt, data=item.data)
                game_vars.player.use_time = wait_time


def new_inventory(dim):
    return bytearray(4 * dim[0] * dim[1])
