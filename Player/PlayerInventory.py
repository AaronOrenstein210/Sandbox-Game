# Created on 5 December 2019

from Player.Inventory import *
from Objects.item_ids import *

hotbar_controls = {
    K_1: 0, K_2: 1, K_3: 2, K_4: 3,
    K_5: 4, K_6: 5, K_7: 6, K_8: 7,
    K_9: 8, K_0: 9
}


class PlayerInventory(Inventory):
    def __init__(self):
        Inventory.__init__(self)
        # Defines current selected item
        self.selected_item, self.selected_amnt = -1, 0
        # Defines current hotbar item
        self.hot_bar_item = -1
        # Checks if the inventory is open or not
        self.open = True
        self.toggle()

    def load(self, data):
        Inventory.load(self, data)
        self.select_hotbar(0)

    def toggle(self):
        self.open = not self.open
        self.rect.h = INV_W * (self.dim[1] if self.open else 1)

    def left_click(self, pos):
        if self.open:
            return Inventory.left_click(self, pos)
        else:
            self.select_hotbar(int(pos[0] / INV_W))
            return 0

    def right_click(self, pos):
        if self.open:
            return Inventory.right_click(self, pos)
        return 0

    def select_hotbar(self, idx):
        if idx != self.hot_bar_item:
            if self.hot_bar_item != -1:
                draw_rect(self.surface, BKGROUND, (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.hot_bar_item = idx
            draw_rect(self.surface, (128, 128, 0), (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)

    def get_cursor_display(self):
        return o.items[self.selected_item].image if self.selected_item != -1 else None

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

    def new_inventory(self):
        data = bytearray(4 * self.dim[0] * self.dim[1])
        items = [TEST_SWORD, TEST_PICKAXE, DIMENSION_HOPPER, DIMENSION_CREATOR,
                 CHEST, DEMATERIALIZER]
        amnts = [1, 1, 10, 10, 10, 1]
        i = 0
        for item, amnt in zip(items, amnts):
            data[i: i + 2] = amnt.to_bytes(2, byteorder)
            data[i + 2:i + 4] = item.to_bytes(2, byteorder)
            i += 4
        data[i:200] = (0).to_bytes(200 - i, byteorder)
        return data
