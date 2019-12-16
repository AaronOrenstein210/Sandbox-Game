# Created on 3 December 2019

import pygame as pg
from pygame.locals import *
from Objects import INV, USE, item_ids as items, tile_ids as tiles
from Objects.ItemTypes import *
from Tools.constants import *
from World.WorldGenerator import generate_world
from Player.ActiveUI import ActiveUI


class Dirt(Block):
    def __init__(self):
        Block.__init__(self, items.DIRT, tiles.DIRT, inv_img=INV + "dirt.png")
        self.name = "Dirt"


class Stone(Block):
    def __init__(self):
        Block.__init__(self, items.STONE, tiles.STONE, inv_img=INV + "stone.png")
        self.name = "Stone"


class Snow(Block):
    def __init__(self):
        Block.__init__(self, items.SNOW, tiles.SNOW, inv_img=INV + "snow.png")
        self.name = "Snow"


class CatSpawner(Block):
    def __init__(self):
        Block.__init__(self, items.CAT, tiles.CAT, inv_img=INV + "spawner_1.png")
        self.name = "Cat Spawner"


class ZombieSpawner(Block):
    def __init__(self):
        Block.__init__(self, items.ZOMBIE, tiles.ZOMBIE, inv_img=INV + "spawner_2.png")
        self.name = "Zombie Spawner"


class DimensionHopper(Block):
    def __init__(self):
        Block.__init__(self, items.DIMENSION_HOPPER, tiles.DIMENSION_HOPPER, inv_img=INV + "dimension_hopper.png")
        self.name = "Dimension Hopper"


class DimensionCreator(Item):
    def __init__(self):
        Item.__init__(self, items.DIMENSION_CREATOR, inv_img=INV + "dimension_creator.png",
                      use_img=USE + "dimension_creator.png")
        self.name = "Dimension Creator"
        self.consumable = True
        self.has_ui = True
        self.get_input = None

    def on_tick(self):
        return

    class UI(ActiveUI):
        def __init__(self):
            from UI.Operations import TextInput
            self.get_input = TextInput("Input World Name", char_limit=10)
            ActiveUI.__init__(self, self.get_input.surface, self.get_input.rect)

        def on_resize(self):
            self.rect.center = pg.display.get_surface().get_rect().center

        def process_events(self, events, mouse, keys):
            world_name = self.get_input.check_events(events)
            if world_name is not None:
                if world_name != "":
                    generate_world(o.universe_name, world_name)
                    o.player.inventory.use_item()
                o.player.use_time = 0
                o.player.active_ui = None


class Dematerializer(Item):
    def __init__(self):
        Item.__init__(self, items.DEMATERIALIZER, inv_img=INV + "dematerializer.png")
        self.name = "Dematerializer"
        self.use_time = 1000

    def on_left_click(self):
        o.player.can_move = False

    def on_tick(self):
        time_i = o.player.use_time
        Item.on_tick(self)
        progress = o.player.use_time / time_i
        spawn = [s * BLOCK_W for s in o.world_spawn]
        delta = [s - p for p, s in zip(o.player.pos, spawn)]
        if progress <= 0 or delta.count(0) == 2:
            o.player.can_move = True
            o.player.set_pos(spawn)
        else:
            # Get distance from spawn (distance left to go) and move player to that point
            pos = [s + progress * -d for s, d in zip(spawn, delta)]
            o.player.set_pos(pos)


class TimeWarp(Item):
    def __init__(self):
        Item.__init__(self, items.TIME_WARP, inv_img=INV + "time_warp.png")
        self.name = "Time Warp"

    def on_tick(self):
        mouse = pg.mouse.get_pressed()
        if mouse[BUTTON_LEFT - 1]:
            o.world_time = (o.world_time + (40 * o.dt)) % MS_PER_DAY
        elif mouse[BUTTON_RIGHT - 1]:
            o.world_time = (o.world_time - (60 * o.dt)) % MS_PER_DAY
        else:
            o.player.use_time = 0


class TestSword(Weapon):
    def __init__(self):
        Weapon.__init__(self, items.TEST_SWORD, damage=15, damage_type=MELEE,
                        inv_img=INV + "test_sword.png", use_img=USE + "test_sword.png")
        self.name = "Test Sword"


class TestPickaxe(Weapon):
    def __init__(self):
        Weapon.__init__(self, items.TEST_PICKAXE, damage=5, damage_type=MELEE,
                        inv_img=INV + "test_pickaxe.png", use_img=USE + "test_pickaxe.png")
        self.name = "Test Pickaxe"
        self.auto_use = True
        self.breaks_blocks = True


class Chest(Block):
    def __init__(self):
        Block.__init__(self, items.CHEST, tiles.CHEST, inv_img=INV + "chest.png")
        self.name = "Chest"
