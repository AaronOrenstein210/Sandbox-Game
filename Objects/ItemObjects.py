# Created on 3 December 2019

from pygame.locals import *
from Objects import INV
from Objects.ItemTypes import *
from Tools.constants import *
from Tools import objects as o, item_ids as items
from NPCs.Mobs import Dragon


# Don't create items that place blocks here, see the tile class
# for implementing blocks

# Useable Items
class SnowBall(Item):
    def __init__(self):
        super().__init__(items.SNOW_BALL, img=INV + "snow_ball.png", name="Snow Ball")
        self.max_stack = 99


class DragonClaw(Item):
    def __init__(self):
        super().__init__(items.DRAGON_CLAW, img=INV + "dragon_claw.png", name="Dragon Claw")
        self.consumable = True

    def on_left_click(self):
        d = Dragon()
        d.set_pos(o.player.pos[0] + randint(15, 30) * BLOCK_W * random_sign(),
                  o.player.pos[1] + randint(15, 30) * BLOCK_W * random_sign())
        o.player.handler.entities.append(d)


class Dematerializer(Item):
    def __init__(self):
        super().__init__(items.DEMATERIALIZER, img=INV + "dematerializer.png",
                         name="Dematerializer")
        self.use_time = 1000

    def on_left_click(self):
        o.player.can_move = False

    def on_tick(self):
        time_i = o.player.use_time
        Item.on_tick(self)
        progress = o.player.use_time / time_i
        spawn = [s * BLOCK_W for s in o.world.spawn]
        delta = [s - p for p, s in zip(o.player.pos, spawn)]
        if progress <= 0 or delta.count(0) == 2:
            o.player.can_move = True
            o.player.spawn()
        else:
            # Get distance from spawn (distance left to go) and move player to that point
            pos = [s + progress * -d for s, d in zip(spawn, delta)]
            o.player.set_pos(pos)


class TimeWarp(Item):
    def __init__(self):
        super().__init__(items.TIME_WARP, img=INV + "time_warp.png", name="Time Warp")
        self.right_click = True

    def on_tick(self):
        mouse = pg.mouse.get_pressed()
        if mouse[BUTTON_LEFT - 1]:
            o.world_time = (o.world_time + (40 * o.dt)) % MS_PER_DAY
        elif mouse[BUTTON_RIGHT - 1]:
            o.world_time = (o.world_time - (60 * o.dt)) % MS_PER_DAY
        else:
            o.player.use_time = 0


# Biome Items
class ForestBiome(Item):
    def __init__(self):
        super().__init__(items.FOREST, img=INV + "forest.png", name="Forest Biome")


class MountainBiome(Item):
    def __init__(self):
        super().__init__(items.MOUNTAIN, img=INV + "mountain.png", name="Mountain Biome")


class ValleyBiome(Item):
    def __init__(self):
        super().__init__(items.VALLEY, img=INV + "valley.png", name="Valley Biome")


class SmallWorld(Item):
    def __init__(self):
        super().__init__(items.SMALL_WORLD, img=INV + "small_world.png", name="Small World")


class MedWorld(Item):
    def __init__(self):
        super().__init__(items.MED_WORLD, img=INV + "med_world.png", name="Medium World")


class LargeWorld(Item):
    def __init__(self):
        super().__init__(items.LARGE_WORLD, img=INV + "large_world.png", name="Large World")


class BonusStructure(Item):
    def __init__(self):
        super().__init__(items.BONUS_STRUCTURE, img=INV + "bonus_structure.png", name="Bonus Structure")


# Ore items
class IronOre(Item):
    def __init__(self):
        super().__init__(items.IRON_ORE, img=INV + "iron_ore.png", name="Iron Ore")


class GoldOre(Item):
    def __init__(self):
        super().__init__(items.GOLD_ORE, img=INV + "gold_ore.png", name="Gold Ore")


class Pyrite(Item):
    def __init__(self):
        super().__init__(items.PYRITE, img=INV + "pyrite.png", name="Pyrite Chunk")


class Sphalerite(Item):
    def __init__(self):
        super().__init__(items.SPHALERITE, img=INV + "sphalerite.png", name="Sphalerite Crystal")


class Obsidian(Item):
    def __init__(self):
        super().__init__(items.OBSIDIAN, img=INV + "obsidian.png", name="Obsidian Shard")


# Weapons/Tools
class TestSword(Weapon):
    def __init__(self):
        super().__init__(items.TEST_SWORD, damage=15, damage_type=MELEE,
                         img=INV + "test_sword.png", name="Test Sword")


class TestPickaxe(Weapon):
    def __init__(self):
        super().__init__(items.TEST_PICKAXE, damage=5, damage_type=MELEE,
                         img=INV + "test_pickaxe.png", name="Test Pickaxe")
        self.auto_use = True
        self.breaks_blocks = True
