# Created on 23 November 2019
# All mobs need to be defined here to create spawners for them

import math
from Objects import MOB
from NPCs.Entity import *
from NPCs.conditions import *
from Player.Stats import Stats
from Tools.constants import BLOCK_W, scale_to_fit
from Tools import item_ids as items
from Tools import objects as o


class Cat(Entity):
    def __init__(self):
        Entity.__init__(self, name="Cat", w=3, img=MOB + "cat.png", rarity=1,
                        stats=Stats(hp=15, max_speed=(3, 10)))

    def can_spawn(self, conditions):
        return conditions[SURFACE]


class Birdie(Entity):
    def __init__(self):
        Entity.__init__(self, name="Birdie", w=.75, aggressive=False, img=MOB + "birdie.png",
                        rarity=1, stats=Stats(hp=5, max_speed=(5, 5)))

    def ai(self):
        fly_random(self)

    def can_spawn(self, conditions):
        return True


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
        Entity.__init__(self, name="Doom Bunny", w=1, aggressive=True, img=MOB + "doom_bunny.png",
                        rarity=3, stats=Stats(hp=5, damage=100, defense=1, max_speed=(5, 20)))

    def ai(self):
        jump(self, abs(o.player.rect.centerx - self.rect.centerx) // BLOCK_W <= 10)

    def can_spawn(self, conditions):
        return True


class Helicopter(Entity):
    def __init__(self):
        Entity.__init__(self, name="Helicopter", w=1.5, aggressive=True, img=MOB + "helicopter.png",
                        rarity=1, stats=Stats(hp=5, damage=10, defense=1, max_speed=(10, 3)))

    def ai(self):
        fly_follow(self)

    def can_spawn(self, conditions):
        return True

    def get_drops(self):
        drops = [[items.LEAVES, randint(1, 5)]]
        if randint(1, 10) <= 7:
            drops.append([items.WOOD, randint(1, 5)])
        return drops


class Dragon(Entity):
    def __init__(self):
        Entity.__init__(self, name="Dragon", aggressive=True, w=5, img=MOB + "dragon_0.png",
                        rarity=3, stats=Stats(hp=100, damage=25, defense=10, max_speed=(15, 15)))
        self.rising_img = self.surface
        self.attacking_img = scale_to_fit(pg.image.load(MOB + "dragon_1.png"), w=5 * BLOCK_W)
        self.zero_gravity = True
        self.hits_blocks = False
        self.no_knockback = True
        self.stage = 0

    def ai(self):
        if self.stage == 0:
            orig_vx = self.v[0]
            self.v[1] = -15
            dx = self.pos[0] - o.player.pos[0]
            if abs(dx) > 10 * BLOCK_W:
                self.v[0] = copysign(15, -dx)
            else:
                self.v[0] = 0
            # When we get high enough, switch modes
            if self.pos[1] < o.player.pos[1] - 10 * BLOCK_W:
                d = [o.player.pos[0] - self.pos[0], self.pos[1] - o.player.pos[1]]
                r = math.sqrt((d[0] * d[0]) + (d[1] * d[1]))
                if r == 0:
                    self.v = [0, 15]
                else:
                    theta = math.asin(d[1] / r)
                    if d[0] < 0:
                        theta = math.pi - theta
                    self.v = [15 * math.cos(theta), -15 * math.sin(theta)]
                if orig_vx < 0:
                    self.surface = self.attacking_img
                else:
                    self.surface = pg.transform.flip(self.attacking_img, True, False)
                self.stage = 1
        # If we get too far away, switch modes
        else:
            dx = self.pos[0] - o.player.pos[0]
            dy = self.pos[1] - o.player.pos[1]
            if dy > 10 * BLOCK_W or (dy >= 0 and abs(dx) > 10 * BLOCK_W):
                self.surface = self.rising_img
                self.stage = 0

    def get_drops(self):
        drops = [[items.SHINY_STONE_1, randint(5, 15)],
                 [items.SHINY_STONE_2, randint(5, 10)]]
        if randint(0, 5) == 1:
            drops.append([items.SHINY_STONE_3, randint(1, 5)])
        return drops
