# Created on 23 November 2019
# All mobs need to be defined here to create spawners for them

from Objects.Items import MOB
from NPCs.Entity import Entity
from Player.Stats import Stats
from NPCs.conditions import *
from Tools.constants import FOLLOW, FLY


class Cat(Entity):
    def __init__(self):
        Entity.__init__(self, name="Cat", w=3, img=MOB + "cat.png", rarity=1,
                        stats=Stats(hp=15, max_speed=(3, 10)))

    def can_spawn(self, conditions):
        return conditions[SURFACE]


class Zombie(Entity):
    def __init__(self):
        Entity.__init__(self, name="Zombie", w=1.5, ai=FOLLOW, aggressive=True, img=MOB + "zombie.png",
                        rarity=2, stats=Stats(hp=50, damage=5, defense=5, max_speed=(5, 10)))

    def can_spawn(self, conditions):
        return conditions[SURFACE] and conditions[NIGHT]
