# Created on 5 December 2019

from Player.Inventory import *
from Player.Stats import Stats, STATS
from Objects.DroppedItem import DroppedItem
from Objects.ItemTypes import Weapon
from Tools import game_vars, item_ids as items

hotbar_controls = {
    K_1: 0, K_2: 1, K_3: 2, K_4: 3,
    K_5: 4, K_6: 5, K_7: 6, K_8: 7,
    K_9: 8, K_0: 9
}

DIM = (10, 5)


class PlayerInventory(Inventory):
    def __init__(self, player):
        super().__init__(DIM)
        # Armor inventory
        self.armor = ArmorInventory(player)
        self.armor.draw_inventory()
        self.armor.rect.left = self.rect.right
        # Crafting ui toggle button
        button_w = INV_W // 2
        self.crafting_toggle = UIButton("res/images/crafting_toggle.png",
                                        pg.Rect(self.armor.rect.bottomleft, (button_w, button_w)))
        # Defines current selected item
        self.selected_item, self.selected_amnt = -1, 0
        self.selected_data = None
        # Defines current hotbar item
        self.hot_bar_item = -1
        # Checks if the inventory is open or not
        self.open = True
        self.toggle()
        # Player that this inventory belongs to
        self.player = player

    def load(self, data):
        result = self.armor.load(super().load(data))
        self.select_hotbar(0)
        return result

    def write(self):
        return super().write() + self.armor.write()

    # Functions to set inventory slot values
    def set_at(self, row, col, item=-1, amnt=0, data=None):
        if row == col == -1:
            prev = self.selected_item
            if amnt <= 0 or item == -1:
                amnt = 0
                item = -1
                data = None
            self.selected_item = item
            self.selected_amnt = amnt
            self.selected_data = data
            if self.selected_item != prev:
                self.on_change_held()

        else:
            super().set_at(row, col, item=item, amnt=amnt, data=data)

    def set_amnt_at(self, row, col, amnt=0):
        if row == col == -1:
            self.selected_amnt = amnt
            if amnt <= 0:
                self.selected_item = -1
                self.selected_data = None
                self.on_change_held()
        else:
            super().set_amnt_at(row, col, amnt=amnt)

    def set_item_at(self, row, col, item=-1):
        if row == col == -1:
            prev = self.selected_item
            self.selected_item = item
            if item == -1:
                self.selected_amnt = 0
                self.selected_data = None
            if self.selected_item != prev:
                self.on_change_held()
        else:
            super().set_item_at(row, col, item=item)

    def set_data_at(self, row, col, data=None):
        if row == col == -1:
            self.selected_data = None
        else:
            super().set_data_at(row, col, data=data)

    def draw(self, pos):
        d = pg.display.get_surface()
        d.blit(self.surface, (0, 0), area=self.rect)
        if self.open:
            self.crafting_toggle.draw()
            self.armor.draw(pos)
            if self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                self.draw_hover_item(pos)

    # Sets the data of the item currently being used
    def set_item_data(self, data):
        if self.selected_amnt == 0 or self.selected_item == -1:
            self.inv_data[(self.hot_bar_item, 0)] = data
        else:
            self.selected_data = data

    # Gets the data of teh item currently being used
    def get_held_data(self):
        if self.selected_amnt == 0 or self.selected_item == -1:
            return self.inv_data.get((self.hot_bar_item, 0))
        else:
            return self.selected_data

    def toggle(self):
        self.open = not self.open
        self.rect.h = INV_W * (self.dim[1] if self.open else 1)

    def draw_hover_item(self, pos):
        if self.open:
            super().draw_hover_item(pos)

    # Perform left click
    def left_click(self, pos):
        if self.rect.collidepoint(*pos):
            pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
            if self.open:
                super().left_click(pos)
            else:
                self.select_hotbar(int(pos[0] / INV_W))
            return True
        elif self.open:
            if self.armor.rect.collidepoint(*pos):
                pos = [pos[0] - self.armor.rect.x, pos[1] - self.armor.rect.y]
                self.armor.left_click(pos)
                return True
            elif self.crafting_toggle.rect.collidepoint(*pos):
                self.player.crafting_open = not self.player.crafting_open
                self.player.use_time = .3
                return True
        return False

    # Perform right click
    def right_click(self, pos):
        if self.open:
            if self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                x, y = pos[0] // INV_W, pos[1] // INV_W
                # Try to move the item to the armor inventory, if that fails, just right click
                amnt = self.inv_amnts[y][x]
                if amnt != 0:
                    item_obj = DroppedItem(self.inv_items[y][x], amnt, data=self.inv_data.get((x, y)))
                    if self.armor.pick_up_item(item_obj):
                        self.set_amnt_at(y, x, amnt=item_obj.amnt)
                        return True
                Inventory.right_click(self, pos)
                return True
            elif self.armor.rect.collidepoint(*pos):
                pos = [pos[0] - self.armor.rect.x, pos[1] - self.armor.rect.y]
                self.armor.right_click(pos)
                return True
        return False

    # Auto moves item to all inventories in active ui
    def auto_move_item(self, row, col):
        # Make sure we are clicking an item and there is a ui up
        amnt = self.inv_amnts[row][col]
        if amnt != 0 and self.player.active_ui:
            # Get ui inventories
            invs = self.player.active_ui.get_inventories()
            # Go through the inventories until we get rid of the item
            item = self.inv_items[row][col]
            data = self.inv_data.get((col, row))
            item_obj = DroppedItem(item, amnt, data=data)
            for inv in invs:
                inv.pick_up_item(item_obj)
                if item_obj.amnt <= 0:
                    break
            self.set_amnt_at(row, col, amnt=item_obj.amnt)
            # If some item moved, tell the current active ui
            if amnt != item_obj.amnt:
                self.player.active_ui.on_inv_pickup()
        return amnt != self.inv_amnts[row][col]

    def select_hotbar(self, idx):
        if idx != self.hot_bar_item:
            if self.hot_bar_item != -1:
                pg.draw.rect(self.surface, BKGROUND, (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.hot_bar_item = idx
            pg.draw.rect(self.surface, (128, 128, 0), (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.on_change_held()

    # Get item to draw under cursor
    def get_cursor_item(self):
        return [int(self.selected_item), int(self.selected_amnt)]

    # Get the current held item
    def get_held_item(self):
        return self.selected_item if self.selected_item != -1 else self.inv_items[0][self.hot_bar_item]

    # Runs when the current item is changed
    def on_change_held(self):
        # Update item stats
        self.player.item_stats.reset()
        if self.selected_item == -1:
            item_id = self.inv_items[0][self.hot_bar_item]
            if item_id != -1:
                item = game_vars.items[item_id]
                if isinstance(item, Weapon):
                    item.load_stats(self.player.item_stats, self.inv_data.get((self.hot_bar_item, 0)))
        else:
            item = game_vars.items[self.selected_item]
            if isinstance(item, Weapon):
                item.load_stats(self.player.item_stats, self.selected_data)

    # Use selected item
    def use_item(self):
        # We are using an item held by the cursor
        if self.selected_item != -1:
            # Reduce its amount and check if we have any left
            self.selected_amnt -= 1
            if self.selected_amnt == 0:
                self.selected_item = -1
                self.selected_data = None
        # Using an item from our hot bar
        else:
            # Reduce its amount and check if we have any left
            self.inv_amnts[0][self.hot_bar_item] -= 1
            if self.inv_amnts[0][self.hot_bar_item] == 0:
                self.inv_items[0][self.hot_bar_item] = -1
                self.inv_data[(self.hot_bar_item, 0)] = None
            self.update_item(0, self.hot_bar_item)

    # Pressed a certain key
    def key_pressed(self, key):
        if key == K_ESCAPE:
            self.toggle()
        elif key in hotbar_controls.keys():
            self.select_hotbar(hotbar_controls[key])

    # Scroll the hotbar
    def scroll(self, up):
        self.select_hotbar(min(max(0, self.hot_bar_item + (-1 if up else 1)), 9))

    # Drop the currently held item
    def drop_item(self):
        drop = None
        if self.selected_item != -1:
            drop = DroppedItem(self.selected_item, self.selected_amnt, data=self.selected_data)
            self.selected_item = -1
            self.selected_amnt = 0
            self.selected_data = None
        return drop

    # Get list of inventory contents, sorted by item id and duplicates combined
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

    # Craft the given recipe
    def craft(self, recipe):
        # Get result
        item, amnt = recipe[0]
        data = game_vars.items[item].new()
        # First try to have the player hold the item
        if self.selected_item == -1:
            self.selected_item = item
            self.selected_amnt = amnt
            self.selected_data = data
        # Then try to add it to whatever the player is holding
        elif self.selected_item == item and self.selected_data == data:
            grab = min(amnt, game_vars.items[item].max_stack - self.selected_amnt)
            self.selected_amnt += grab
            amnt -= grab
        else:
            # Finally try to put it into the inventory
            item_obj = DroppedItem(item, amnt, data=data)
            if not self.pick_up_item(item_obj):
                # Drop whatever is left
                game_vars.drop_item(item_obj, True)
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
                            if self.inv_amnts[y][x] <= 0:
                                self.inv_items[y][x] = -1
                                self.inv_data[(x, y)] = None
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


class ArmorInventory(Inventory):
    DIM = (1, 4)
    ARMOR_ORDER = [items.HELMET, items.CHESTPLATE, items.LEGGINGS, items.BOOTS]

    def __init__(self, player):
        super().__init__(self.DIM, max_stack=1)
        # These stat objects are created ONCE
        self.stats = [Stats(STATS) for i in range(len(self.ARMOR_ORDER))]
        for s in self.stats:
            player.stats.add_stats(s)

    def load(self, data):
        data = super().load(data)
        for idx in range(self.DIM[1]):
            self.recalculate_stat(idx)
        return data

    def draw(self, pos):
        pg.display.get_surface().blit(self.surface, self.rect)
        if self.rect.collidepoint(*pos):
            pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
            self.draw_hover_item(pos)

    def left_click(self, pos):
        idx = pos[1] // INV_W
        if idx < len(self.ARMOR_ORDER):
            prev = self.inv_data.get((0, idx))
            self.whitelist = self.ARMOR_ORDER[idx:idx + 1]
            super().left_click(pos)
            # If the armor data changed, recalculate stats
            if prev != self.inv_data.get((0, idx)):
                self.recalculate_stat(idx)

    def right_click(self, pos):
        idx = pos[1] // self.rect.h
        if idx < len(self.ARMOR_ORDER):
            prev = self.inv_data.get((0, idx))
            self.whitelist = [self.ARMOR_ORDER[idx]]
            super().right_click(pos)
            # If the armor data changed, recalculate stats
            if prev != self.inv_data.get((0, idx)):
                self.recalculate_stat(idx)

    def room_for_item(self, item):
        for idx, item_id in enumerate(self.ARMOR_ORDER):
            if item.idx == item_id:
                if self.inv_amnts[idx][0] == 0:
                    return [(0, idx)]
                break
        return []

    def on_pick_up(self, row, col):
        self.recalculate_stat(row)

    def recalculate_stat(self, idx):
        self.stats[idx].reset()
        data = self.inv_data.get((0, idx))
        if data:
            game_vars.items[self.inv_items[idx][0]].load_stats(self.stats[idx], data)


class UIButton:
    def __init__(self, img, rect):
        # Load image and rectangle
        self.img = c.load_image(img, rect.w, rect.h)
        self.rect = self.img.get_rect(center=rect.center)
        # This is the image but lighter for when it is being hovered over
        self.selected = self.img.copy()
        self.selected.fill([75] * 3, special_flags=BLEND_RGB_ADD)

    def draw(self):
        pos = pg.mouse.get_pos()
        if self.rect.collidepoint(*pos):
            pg.display.get_surface().blit(self.selected, self.rect)
        else:
            pg.display.get_surface().blit(self.img, self.rect)


# Returns data for an empty inventory


def new_inventory():
    from Tools.item_ids import BASIC_PICKAXE
    slots = DIM[0] * DIM[1] + ArmorInventory.DIM[0] * ArmorInventory.DIM[1]
    data = bytearray(4 * slots + 1)
    data[:2] = (1).to_bytes(2, byteorder)
    data[2:4] = BASIC_PICKAXE.to_bytes(2, byteorder)
    return data
