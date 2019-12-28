# Created on 23 November 2019
# All mobs need to be defined here to create spawners for them

from Objects import MOB
from NPCs.Entity import Entity, follow_player, jump
from NPCs.conditions import *
from Player.Stats import Stats
from Tools.constants import BLOCK_W
from Tools import objects as o


class Cat(Entity):
    def __init__(self):
        Entity.__init__(self, name="Cat", w=3, img=MOB + "cat.png", rarity=1,
                        stats=Stats(hp=15, max_speed=(3, 10)))

    def can_spawn(self, conditions):
        return conditions[SURFACE]


class Zombie(Entity):
    def __init__(self):
        Entity.__init__(self, name="Zombie", w=1.5, aggressive=True, img=MOB + "zombie.png",
                        rarity=2, stats=Stats(hp=50, damage=5, defense=5, max_speed=(5, 10)))

    def ai(self):
        follow_player(self)

    def can_spawn(self, conditions):
        return conditions[NIGHT]


class DoomBunny(Entity):
    def __init__(self):
        Entity.__init__(self, name="Doom Bunny", aggressive=True, img=MOB + "doom_bunny.png",
                        rarity=3, stats=Stats(hp=5, damage=100, defense=1, max_speed=(5, 20)))

    def ai(self):
        jump(self, abs(o.player.rect.centerx - self.rect.centerx) // BLOCK_W <= 10)

    def can_spawn(self, conditions):
        return True
