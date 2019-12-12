# Created on 4 December 2019
# Defines specific types of items

from Objects.Item import Item
from Tools import objects as o


class Block(Item):
    def __init__(self, idx, block_id, inv_img=""):
        Item.__init__(self, idx, inv_img=inv_img, use_img=inv_img)
        self.block_id = block_id
        self.consumable = True
        self.auto_use = True
        self.swing = True
        self.placeable = True


class Weapon(Item):
    def __init__(self, idx, damage=1, damage_type=0, projectiles=(),
                 inv_img="", use_img=""):
        Item.__init__(self, idx, inv_img=inv_img, use_img=use_img)
        self.swing = True
        self.is_weapon = True
        self.damage = damage
        self.damage_type = damage_type
        self.projectiles = projectiles

    def use_anim(self, time_used, arm, left, player_center, rect):
        Item.use_anim(self, time_used, arm, left, player_center, rect)
        o.player.attack(self.damage, self.polygon)
