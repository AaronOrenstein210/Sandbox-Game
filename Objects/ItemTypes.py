# Created on 4 December 2019
# Defines specific types of items

from Objects.Item import Item
from Tools import objects as o


class Block(Item):
    def __init__(self, idx, block_id, **kwargs):
        Item.__init__(self, idx, **kwargs)
        self.block_id = block_id
        self.consumable = True
        self.auto_use = True
        self.swing = True
        self.placeable = True

    def on_left_click(self):
        if o.player.place_block(*o.player.get_cursor_block_pos(), self.block_id) and self.consumable:
            o.player.inventory.use_item()


class Weapon(Item):
    def __init__(self, idx, damage=1, damage_type=0, projectiles=(), **kwargs):
        Item.__init__(self, idx, **kwargs)
        self.swing = True
        self.is_weapon = True
        self.damage = damage
        self.damage_type = damage_type
        self.projectiles = projectiles
        self.max_stack = 1

    def on_left_click(self):
        # Break blocks if necessary
        if self.breaks_blocks:
            if o.player.break_block(*o.player.get_cursor_block_pos()) and self.consumable:
                o.player.inventory.use_item()
        elif self.consumable:
            o.player.inventory.use_item()

    def use_anim(self, time_used, arm, left, player_center, rect):
        Item.use_anim(self, time_used, arm, left, player_center, rect)
        o.player.attack(self.damage, self.polygon)
