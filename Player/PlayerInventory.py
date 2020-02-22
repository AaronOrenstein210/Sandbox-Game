# Created on 5 December 2019

from Player.Inventory import *
from Objects.DroppedItem import DroppedItem

hotbar_controls = {
    K_1: 0, K_2: 1, K_3: 2, K_4: 3,
    K_5: 4, K_6: 5, K_7: 6, K_8: 7,
    K_9: 8, K_0: 9
}


class PlayerInventory(Inventory):
    def __init__(self):
        super().__init__((10, 5))
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

    def draw_hover_item(self, pos):
        if self.open:
            super().draw_hover_item(pos)

    def left_click(self, pos):
        if self.open:
            Inventory.left_click(self, pos)
        else:
            self.select_hotbar(int(pos[0] / INV_W))

    def right_click(self, pos):
        if self.open:
            Inventory.right_click(self, pos)

    def select_hotbar(self, idx):
        if idx != self.hot_bar_item:
            if self.hot_bar_item != -1:
                pg.draw.rect(self.surface, BKGROUND, (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.hot_bar_item = idx
            pg.draw.rect(self.surface, (128, 128, 0), (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)

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

    def get_all_items(self):
        results = []
        for row1, row2 in zip(self.inv_items, self.inv_amnts):
            for item, amnt in zip(row1, row2):
                if item == -1:
                    continue
                # Special conditions
                if len(results) == 0 or results[-1][0] < item:
                    results.append([item, amnt])
                # Place item into results
                else:
                    i = 0
                    while i < len(results) and results[i][0] < item:
                        i += 1
                    if results[i][0] == item:
                        results[i][1] += amnt
                    else:
                        results.insert(i, [item, amnt])
        return results

    def craft(self, recipe):
        # Get result
        item, amnt = recipe[0]
        # First try to have the player hold the item
        if self.selected_item == -1:
            self.selected_item = item
            self.selected_amnt = amnt
        # Then try to add it to whatever the player is holding
        elif self.selected_item == item:
            grab = min(amnt, o.items[item].max_stack - self.selected_amnt)
            self.selected_amnt += grab
            amnt -= grab
        else:
            # Finally try to put it into the inventory
            item_obj = DroppedItem(item, amnt)
            if not self.pick_up_item(item_obj):
                # Drop whatever is left
                o.player.drop_item(item_obj, True)
        # Get the amounts of ingredients that are required
        parts = [r.copy() for r in recipe[1:]]
        # Remove ingredients
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                inv_item = self.inv_items[y][x]
                if inv_item != -1:
                    i = 0
                    while i < len(parts):
                        item, amnt = parts[i]
                        if item == inv_item:
                            # Remove the item
                            transfer = min(self.inv_amnts[y][x], amnt)
                            self.inv_amnts[y][x] -= transfer
                            parts[i][1] -= transfer
                            # Check if we need to update this item
                            if transfer > 0:
                                self.update_item(y, x)
                            # Delete this item
                            if parts[i][1] <= 0:
                                del parts[i]
                                if len(parts) == 0:
                                    return
                                i -= 1
                        i += 1

    def new_inventory(self):
        from Tools.item_ids import BASIC_PICKAXE
        data = bytearray(4 * self.dim[0] * self.dim[1])
        data[:2] = (1).to_bytes(2, byteorder)
        data[2:4] = BASIC_PICKAXE.to_bytes(2, byteorder)
        return data
