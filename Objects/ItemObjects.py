# Created on 3 December 2019

from pygame.locals import *
from Objects import INV, USE, item_ids as items
from Objects.ItemTypes import *
from Tools.constants import *
from Tools import objects as o
from World.World import World
from World.WorldGenerator import get_random_biome
from Player.ActiveUI import ActiveUI
from NPCs.Mobs import Dragon


# Don't create items that place blocks here, see the tile class
# for implementing blocks

class SnowBall(Item):
    def __init__(self):
        Item.__init__(self, items.SNOW_BALL, inv_img=INV + "snow_ball.png", name="Snow Ball")
        self.max_stack = 99


class DragonClaw(Item):
    def __init__(self):
        Item.__init__(self, items.DRAGON_CLAW, inv_img=INV + "dragon_claw.png", name="Dragon Claw")
        self.consumable = True

    def on_left_click(self):
        d = Dragon()
        d.set_pos(o.player.pos[0] + randint(15, 30) * BLOCK_W * random_sign(),
                  o.player.pos[1] + randint(15, 30) * BLOCK_W * random_sign())
        o.player.handler.entities.append(d)


class DimensionCreator(Item):
    def __init__(self):
        Item.__init__(self, items.DIMENSION_CREATOR, inv_img=INV + "dimension_creator.png", name="Dimension Creator")
        self.consumable = True
        self.has_ui = True
        self.get_input = None

    def on_left_click(self):
        pass

    def on_tick(self):
        pass

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
                    new = World(o.world.universe, world_name)
                    new.generator.generate([1000, 500], [get_random_biome() for i in range(5)])
                    del new
                    o.player.inventory.use_item()
                o.player.use_time = 0
                o.player.active_ui = None


class Dematerializer(Item):
    def __init__(self):
        Item.__init__(self, items.DEMATERIALIZER, inv_img=INV + "dematerializer.png",
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
            o.player.set_pos(spawn)
        else:
            # Get distance from spawn (distance left to go) and move player to that point
            pos = [s + progress * -d for s, d in zip(spawn, delta)]
            o.player.set_pos(pos)


class TimeWarp(Item):
    def __init__(self):
        Item.__init__(self, items.TIME_WARP, inv_img=INV + "time_warp.png", name="Time Warp")
        self.right_click = True

    def on_tick(self):
        mouse = pg.mouse.get_pressed()
        if mouse[BUTTON_LEFT - 1]:
            o.world_time = (o.world_time + (40 * o.dt)) % MS_PER_DAY
        elif mouse[BUTTON_RIGHT - 1]:
            o.world_time = (o.world_time - (60 * o.dt)) % MS_PER_DAY
        else:
            o.player.use_time = 0


class ForestBiome(Item):
    def __init__(self):
        Item.__init__(self, items.FOREST, inv_img=INV + "forest.png", name="Forest Biome")


class MountainBiome(Item):
    def __init__(self):
        Item.__init__(self, items.MOUNTAIN, inv_img=INV + "mountain.png", name="Mountain Biome")


class ValleyBiome(Item):
    def __init__(self):
        Item.__init__(self, items.VALLEY, inv_img=INV + "valley.png", name="Valley Biome")


class TestSword(Weapon):
    def __init__(self):
        Weapon.__init__(self, items.TEST_SWORD, damage=15, damage_type=MELEE,
                        inv_img=INV + "test_sword.png", use_img=USE + "test_sword.png", name="Test Sword")


class TestPickaxe(Weapon):
    def __init__(self):
        Weapon.__init__(self, items.TEST_PICKAXE, damage=5, damage_type=MELEE,
                        inv_img=INV + "test_pickaxe.png", use_img=USE + "test_pickaxe.png", name="Test Pickaxe")
        self.auto_use = True
        self.breaks_blocks = True
