# Created on 5 December 2019

from Player.Inventory import *
from Player.Stats import Stats, STATS
from Objects.DroppedItem import DroppedItem
from Objects.ItemTypes import Weapon, ItemInfo
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
        self.selected_item = ItemInfo(-1, 0)
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

    def draw(self, mouse_pos, parent_pos=(0, 0)):
        self.update()
        d = pg.display.get_surface()
        d.blit(self.surface, (0, 0), area=self.rect)
        if self.open:
            self.crafting_toggle.draw()
            self.armor.draw(mouse_pos)
            if self.rect.collidepoint(*mouse_pos):
                pos = [mouse_pos[0] - self.rect.x, mouse_pos[1] - self.rect.y]
                self.draw_hover_item(pos)

    # Gets the item currently in the player's hand
    def get_held_item(self):
        return self.selected_item

    # Gets the item currently ready to be used (in hand or hotbar)
    def get_current_item(self):
        if self.selected_item.is_item:
            return self.selected_item
        else:
            return self.get_item(0, self.hot_bar_item)

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
                item = self.get_item(y, x)
                if item.is_item:
                    if self.armor.pick_up_item(item):
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
        item = self.get_item(row, col)
        prev_amnt = item.amnt
        if item.is_item and self.player.active_ui:
            # Get ui inventories
            invs = self.player.active_ui.get_inventories()
            # Go through the inventories until we get rid of the item
            for inv in invs:
                inv.pick_up_item(item)
                if not item.is_item:
                    break
            # If some item moved, tell the current active ui
            if item.amnt != prev_amnt:
                self.player.active_ui.on_inv_pickup()
        return prev_amnt != item.amnt

    def select_hotbar(self, idx):
        if idx != self.hot_bar_item:
            if self.hot_bar_item != -1:
                pg.draw.rect(self.surface, BKGROUND, (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.hot_bar_item = idx
            pg.draw.rect(self.surface, (128, 128, 0), (self.hot_bar_item * INV_W, 0, INV_W, INV_W), 2)
            self.on_change_held()

    # Runs when the current item is changed
    def on_change_held(self):
        # Update item stats
        self.player.item_stats.reset()
        if not self.selected_item.is_item:
            item = self.inv_items[0][self.hot_bar_item]
            if item.is_item:
                item_obj = game_vars.items[item.item_id]
                if isinstance(item_obj, Weapon):
                    item_obj.load_stats(self.player.item_stats, item.data)
        else:
            item_obj = game_vars.items[self.selected_item.item_id]
            if isinstance(item_obj, Weapon):
                item_obj.load_stats(self.player.item_stats, self.selected_item.data)

    # Use selected item
    def use_item(self):
        item = self.get_current_item()
        if item.is_item:
            # Reduce its amount and check if we have any left
            item.amnt -= 1
            if not item.is_item:
                self.on_change_held()

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
        if self.selected_item.is_item:
            drop = DroppedItem(self.selected_item.copy())
            self.selected_item.amnt = 0
        return drop

    # Craft the given recipe
    def craft(self, recipe):
        # Get result
        new_item = ItemInfo(*recipe[0])
        # First try to have the player hold the item
        if not self.selected_item.is_item:
            self.selected_item.set_info(new_item)
        # Then try to add it to whatever the player is holding
        elif self.selected_item.same_as(new_item):
            grab = min(new_item.amnt, self.selected_item.max_stack - self.selected_item.amnt)
            self.selected_item.amnt += grab
            new_item.amnt -= grab
        else:
            # Finally try to put it into the inventory
            if not self.pick_up_item(new_item):
                # Drop whatever is left
                game_vars.drop_item(DroppedItem(new_item), True)
        # Get the amounts of ingredients that are required
        parts = [r.copy() for r in recipe[1:]]
        # Remove ingredients
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                item = self.get_item(y, x)
                if item.is_item:
                    i = 0
                    while i < len(parts):
                        item_id, amnt = parts[i]
                        if item.item_id == item_id:
                            # Remove the item
                            transfer = min(item.amnt, amnt)
                            item.amnt -= transfer
                            parts[i][1] -= transfer
                            # Delete this item
                            if parts[i][1] <= 0:
                                del parts[i]
                                if len(parts) == 0:
                                    return
                                i -= 1
                        elif item_id > item.item_id:
                            break
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

    def left_click(self, pos):
        idx = pos[1] // INV_W
        if idx < len(self.ARMOR_ORDER):
            prev = self.inv_items[idx][0].data
            self.whitelist = self.ARMOR_ORDER[idx:idx + 1]
            super().left_click(pos)
            # If the armor data changed, recalculate stats
            if prev != self.inv_items[idx][0].data:
                self.recalculate_stat(idx)

    def right_click(self, pos):
        idx = pos[1] // self.rect.h
        if idx < len(self.ARMOR_ORDER):
            prev = self.inv_items[idx][0].data
            self.whitelist = [self.ARMOR_ORDER[idx]]
            super().right_click(pos)
            # If the armor data changed, recalculate stats
            if prev != self.inv_items[idx][0].data:
                self.recalculate_stat(idx)

    def room_for_item(self, item):
        for idx, item_id in enumerate(self.ARMOR_ORDER):
            if item.item_id == item_id:
                if not self.inv_items[idx][0].is_item:
                    return [(0, idx)]
                break
        return []

    def on_pick_up(self, row, col):
        self.recalculate_stat(row)

    def recalculate_stat(self, idx):
        self.stats[idx].reset()
        item = self.inv_items[idx][0]
        if item.is_item and item.data:
            game_vars.items[item.item_id].load_stats(self.stats[idx], item.data)


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
    data[:2] = BASIC_PICKAXE.to_bytes(2, byteorder)
    data[2:4] = (1).to_bytes(2, byteorder)
    return data
