# Created on 3 December 2019

from sys import byteorder
from pygame.locals import *
from Objects import INV
from Objects.ItemTypes import *
from Tools.constants import *
from Tools import game_vars, item_ids as i, tile_ids as t
from NPCs.Entity import Projectile
from NPCs.Mobs import Dragon


# Don't create items that place blocks here, see the tile class
# for implementing blocks

# Useable Items
class SnowBall(Item):
    def __init__(self):
        super().__init__(i.SNOW_BALL, img=INV + "snow_ball.png", name="Snow Ball")
        self.max_stack = 99
        self.auto_use = True
        self.consumable = True

    def on_left_click(self):
        super().on_left_click()
        game_vars.shoot_projectile(self.P1(game_vars.player_pos(), game_vars.global_mouse_pos()))

    def get_description(self, data):
        return "Fun to throw!"

    class P1(Projectile):
        def __init__(self, pos, target):
            super().__init__(pos, target, w=.5, img=INV + "snow_ball.png", speed=15)
            self.hurts_mobs = True
            self.bounce = True


class DragonClaw(Item):
    def __init__(self):
        super().__init__(i.DRAGON_CLAW, img=INV + "dragon_claw.png", name="Dragon Claw")
        self.consumable = True

    def on_left_click(self):
        game_vars.spawn_entity(Dragon(),
                               [p + randint(15, 30) * BLOCK_W * random_sign() for p in game_vars.player_pos()])

    def get_description(self, data):
        return "A claw, torn from a defeated dragon\nIt holds many magical properties"


class Dematerializer(Item):
    def __init__(self):
        super().__init__(i.DEMATERIALIZER, img=INV + "dematerializer.png",
                         name="Dematerializer")
        self.use_time = 1

    def on_left_click(self):
        game_vars.player.can_move = False

    def on_tick(self):
        time_i = game_vars.player.use_time
        Item.on_tick(self)
        progress = game_vars.player.use_time / time_i
        spawn = [s * BLOCK_W for s in game_vars.world.spawn]
        delta = [s - p for p, s in zip(game_vars.player.pos, spawn)]
        if progress <= 0 or delta.count(0) == 2:
            game_vars.player.can_move = True
            game_vars.player.spawn()
        else:
            # Get distance from spawn (distance left to go) and move player to that point
            pos = [s + progress * -d for s, d in zip(spawn, delta)]
            game_vars.player.set_pos(pos)

    def get_description(self, data):
        return "Teleports the user back to spawn"


class Waypoint(Item):
    def __init__(self):
        super().__init__(i.WAYPOINT, img=INV + 'waypoint.png', name="Waypoint")
        self.right_click = True
        self.has_data = True

    def on_left_click(self):
        data = game_vars.get_current_item_data()
        if data:
            pos = [int.from_bytes(data[2 * j:2 * (j + 1)], byteorder) * BLOCK_W for j in range(2)]
            game_vars.player.set_pos(pos)

    def on_right_click(self):
        pos = game_vars.player_topleft(True)
        data = int(pos[0]).to_bytes(2, byteorder)
        data += int(pos[1]).to_bytes(2, byteorder)
        game_vars.set_current_item_data(data)

    def get_description(self, data):
        if data:
            waypoint = "({}, {})".format(int.from_bytes(data[:2], byteorder),
                                         int.from_bytes(data[2: 4], byteorder))
        else:
            waypoint = "Not Set"
        return "Right click to set waypoint\nLeft click to teleport" \
               "to waypoint\nCurrent Waypoint: {}".format(waypoint)


class TimeWarp(Item):
    def __init__(self):
        super().__init__(i.TIME_WARP, img=INV + "time_warp.png", name="Time Warp")
        self.right_click = True

    def on_tick(self):
        mouse = pg.mouse.get_pressed()
        w = game_vars.world
        if mouse[BUTTON_LEFT - 1]:
            w.time = (w.time + (40 * game_vars.dt)) % SEC_PER_DAY
        elif mouse[BUTTON_RIGHT - 1]:
            w.time = (w.time - (60 * game_vars.dt)) % SEC_PER_DAY
        else:
            game_vars.player.use_time = 0

    def get_description(self, data):
        return "Left click to move time forwards, right click to move time backwards"


# Biome Items
class ForestBiome(Item):
    def __init__(self):
        super().__init__(i.FOREST, img=INV + "forest.png", name="Forest Biome")

    def get_description(self, data):
        return "Contains the essence of the Forest"


class MountainBiome(Item):
    def __init__(self):
        super().__init__(i.MOUNTAIN, img=INV + "mountain.png", name="Mountain Biome")

    def get_description(self, data):
        return "Holds the secret of the Mountains"


class ValleyBiome(Item):
    def __init__(self):
        super().__init__(i.VALLEY, img=INV + "valley.png", name="Valley Biome")

    def get_description(self, data):
        return "Reveals the mysteries of the Valley"


class SmallWorld(Item):
    def __init__(self):
        super().__init__(i.SMALL_WORLD, img=INV + "small_world.png", name="Small World")

    def get_description(self, data):
        return "Holds the power to create a small world"


class MedWorld(Item):
    def __init__(self):
        super().__init__(i.MED_WORLD, img=INV + "med_world.png", name="Medium World")

    def get_description(self, data):
        return "Holds the power to create a medium-sized world"


class LargeWorld(Item):
    def __init__(self):
        super().__init__(i.LARGE_WORLD, img=INV + "large_world.png", name="Large World")

    def get_description(self, data):
        return "Holds the power to bring a large world into existence"


class BonusStructure(Item):
    def __init__(self):
        super().__init__(i.BONUS_STRUCTURE, img=INV + "bonus_structure.png", name="Bonus Structure")

    def get_description(self, data):
        return "With this item, new worlds can hold one more structure"


# Ore items
class IronOre(Item):
    def __init__(self):
        super().__init__(i.IRON_ORE, img=INV + "iron_ore.png", name="Iron Ore")


class GoldOre(Item):
    def __init__(self):
        super().__init__(i.GOLD_ORE, img=INV + "gold_ore.png", name="Gold Ore")


class Pyrite(Item):
    def __init__(self):
        super().__init__(i.PYRITE, img=INV + "pyrite.png", name="Pyrite Chunk")

    def get_description(self, data):
        return "Oooh, shiny!"


class Sphalerite(Item):
    def __init__(self):
        super().__init__(i.SPHALERITE, img=INV + "sphalerite.png", name="Sphalerite Crystal")

    def get_description(self, data):
        return "Sphaler-what?"


class Obsidian(Item):
    def __init__(self):
        super().__init__(i.OBSIDIAN, img=INV + "obsidian.png", name="Obsidian Shard")

    def get_description(self, data):
        return "Obtained from the nether regions of the world"


# Weapons/Tools
class TestSword(Weapon):
    def __init__(self):
        super().__init__(i.BASIC_SWORD, damage=7, damage_type=MELEE,
                         img=INV + "basic_sword.png", name="Basic Sword")

    def on_left_click(self):
        game_vars.shoot_projectile(self.P1(game_vars.player.rect.center, game_vars.global_mouse_pos()))

    def get_description(self, data):
        return "Your basic sword\nIt has so much potential"

    class P1(Projectile):
        def __init__(self, pos, target):
            super().__init__(pos, target, w=.5, img=INV + "snow_ball.png", speed=6)
            self.hurts_mobs = True


class TestPickaxe(Weapon):
    def __init__(self):
        super().__init__(i.BASIC_PICKAXE, damage=3, damage_type=MELEE,
                         img=INV + "basic_pickaxe.png", name="Basic Pickaxe")
        self.auto_use = True
        self.breaks_blocks = True

    def get_description(self, data):
        return "Your basic pickaxe\nIt has so much potential"


# Blocks
class Dirt(Block):
    def __init__(self):
        super().__init__(i.DIRT, t.DIRT, name="Dirt", img=INV + "dirt.png")


class Stone(Block):
    def __init__(self):
        super().__init__(i.STONE, t.STONE, name="Stone", img=INV + "stone.png")


class Snow(Block):
    def __init__(self):
        super().__init__(i.SNOW, t.SNOW, name="Snow", img=INV + "snow.png")


class Wood(Block):
    def __init__(self):
        super().__init__(i.WOOD, t.WOOD, name="Wood", img=INV + "wood_item.png")


class Leaves(Block):
    def __init__(self):
        super().__init__(i.LEAVES, t.LEAVES, name="Leaves", img=INV + "leaves.png")


class ShinyStone1(Block):
    def __init__(self):
        super().__init__(i.SHINY_STONE_1, t.SHINY_STONE_1, name="Shiny Stone: Tier 1",
                         img=INV + "shiny_stone_1.png")

    def get_description(self, data):
        return "You can kind of see something shiny inside"


class ShinyStone2(Block):
    def __init__(self):
        super().__init__(i.SHINY_STONE_2, t.SHINY_STONE_2, name="Shiny Stone: Tier 2",
                         img=INV + "shiny_stone_2.png")

    def get_description(self, data):
        return "Ooh, this rock is pretty"


class ShinyStone3(Block):
    def __init__(self):
        super().__init__(i.SHINY_STONE_3, t.SHINY_STONE_3, name="Shiny Stone: Tier 3",
                         img=INV + "shiny_stone_3.png")

    def get_description(self, data):
        return "The glow of untold riches within tempts your greed"


class DragonEgg(Block):
    def __init__(self):
        super().__init__(i.DRAGON_EGG, t.DRAGON_EGG, name="Dragon Egg", img=INV + "dragon_egg.png")

    def get_description(self, data):
        return "There's definitely something alive in here"


class WorkTable(Block):
    def __init__(self):
        super().__init__(i.WORK_TABLE, t.WORK_TABLE, name="Work Table", img=INV + "work_table.png")

    def get_description(self, data):
        return "Now you can make pretty furniture!"


class DimensionHopper(Block):
    def __init__(self):
        super().__init__(i.DIMENSION_HOPPER, t.DIMENSION_HOPPER, name="Dimension Hopper",
                         img=INV + "dimension_hopper.png")

    def get_description(self, data):
        return "A mysterious portal that calls to your adventurous spirit"


class Chest(Block):
    def __init__(self):
        super().__init__(i.CHEST, t.CHEST, name="Chest", img=INV + "chest.png")

    def get_description(self, data):
        return "Challenge idea: this block is only unlocked after beating the final boss"


class WorldBuilder(Block):
    def __init__(self):
        super().__init__(i.WORLD_BUILDER, t.WORLD_BUILDER, name="World Builder",
                         img=INV + "world_builder/world_builder_0.png")

    def get_description(self, data):
        return "Channels the energy of biomes to create entire worlds\n" + \
               "Legend says that the presence of certain biome combinations will allow rare creatures to spawn"


class Crusher(Block):
    def __init__(self):
        super().__init__(i.CRUSHER, t.CRUSHER, name="Crusher", img=INV + "crusher/crusher_0.png")

    def get_description(self, data):
        return "This machine looks powerful enough to crush those shiny stones that you found"
