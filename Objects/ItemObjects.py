# Created on 3 December 2019

from pygame.locals import *
from Objects import INV
from Objects.ItemTypes import *
from Tools.constants import *
from Tools import objects as o, item_ids as i, tile_ids as t
from NPCs.Mobs import Dragon


# Don't create items that place blocks here, see the tile class
# for implementing blocks

# Useable Items
class SnowBall(Item):
    def __init__(self):
        super().__init__(i.SNOW_BALL, img=INV + "snow_ball.png", name="Snow Ball")
        self.max_stack = 99

    def get_description(self):
        return "Fun to throw!"


class DragonClaw(Item):
    def __init__(self):
        super().__init__(i.DRAGON_CLAW, img=INV + "dragon_claw.png", name="Dragon Claw")
        self.consumable = True

    def on_left_click(self):
        d = Dragon()
        d.set_pos(o.player.pos[0] + randint(15, 30) * BLOCK_W * random_sign(),
                  o.player.pos[1] + randint(15, 30) * BLOCK_W * random_sign())
        o.player.handler.entities.append(d)

    def get_description(self):
        return "A claw, torn from a defeated dragon\nIt holds many magical properties"


class Dematerializer(Item):
    def __init__(self):
        super().__init__(i.DEMATERIALIZER, img=INV + "dematerializer.png",
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

    def get_description(self):
        return "Teleports the user back to spawn"


class TimeWarp(Item):
    def __init__(self):
        super().__init__(i.TIME_WARP, img=INV + "time_warp.png", name="Time Warp")
        self.right_click = True

    def on_tick(self):
        mouse = pg.mouse.get_pressed()
        if mouse[BUTTON_LEFT - 1]:
            o.world_time = (o.world_time + (40 * o.dt)) % MS_PER_DAY
        elif mouse[BUTTON_RIGHT - 1]:
            o.world_time = (o.world_time - (60 * o.dt)) % MS_PER_DAY
        else:
            o.player.use_time = 0

    def get_description(self):
        return "Left click to move time forwards, right click to move time backwards"


# Biome Items
class ForestBiome(Item):
    def __init__(self):
        super().__init__(i.FOREST, img=INV + "forest.png", name="Forest Biome")

    def get_description(self):
        return "Contains the essence of the Forest"


class MountainBiome(Item):
    def __init__(self):
        super().__init__(i.MOUNTAIN, img=INV + "mountain.png", name="Mountain Biome")

    def get_description(self):
        return "Holds the secret of the Mountains"


class ValleyBiome(Item):
    def __init__(self):
        super().__init__(i.VALLEY, img=INV + "valley.png", name="Valley Biome")

    def get_description(self):
        return "Reveals the mysteries of the Valley"


class SmallWorld(Item):
    def __init__(self):
        super().__init__(i.SMALL_WORLD, img=INV + "small_world.png", name="Small World")

    def get_description(self):
        return "Holds the power to create a small world"


class MedWorld(Item):
    def __init__(self):
        super().__init__(i.MED_WORLD, img=INV + "med_world.png", name="Medium World")

    def get_description(self):
        return "Holds the power to create a medium-sized world"


class LargeWorld(Item):
    def __init__(self):
        super().__init__(i.LARGE_WORLD, img=INV + "large_world.png", name="Large World")

    def get_description(self):
        return "Holds the power to bring a large world into existence"


class BonusStructure(Item):
    def __init__(self):
        super().__init__(i.BONUS_STRUCTURE, img=INV + "bonus_structure.png", name="Bonus Structure")

    def get_description(self):
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

    def get_description(self):
        return "Oooh, shiny!"


class Sphalerite(Item):
    def __init__(self):
        super().__init__(i.SPHALERITE, img=INV + "sphalerite.png", name="Sphalerite Crystal")

    def get_description(self):
        return "Sphaler-what?"


class Obsidian(Item):
    def __init__(self):
        super().__init__(i.OBSIDIAN, img=INV + "obsidian.png", name="Obsidian Shard")

    def get_description(self):
        return "Obtained from the nether regions of the world"


# Weapons/Tools
class TestSword(Weapon):
    def __init__(self):
        super().__init__(i.BASIC_SWORD, damage=7, damage_type=MELEE,
                         img=INV + "basic_sword.png", name="Basic Sword")

    def get_description(self):
        return "Your basic sword\nIt has so much potential"


class TestPickaxe(Weapon):
    def __init__(self):
        super().__init__(i.BASIC_PICKAXE, damage=3, damage_type=MELEE,
                         img=INV + "basic_pickaxe.png", name="Basic Pickaxe")
        self.auto_use = True
        self.breaks_blocks = True

    def get_description(self):
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

    def get_description(self):
        return "You can kind of see something shiny inside"


class ShinyStone2(Block):
    def __init__(self):
        super().__init__(i.SHINY_STONE_2, t.SHINY_STONE_2, name="Shiny Stone: Tier 2",
                         img=INV + "shiny_stone_2.png")

    def get_description(self):
        return "Ooh, this rock is pretty"


class ShinyStone3(Block):
    def __init__(self):
        super().__init__(i.SHINY_STONE_3, t.SHINY_STONE_3, name="Shiny Stone: Tier 3",
                         img=INV + "shiny_stone_3.png")

    def get_description(self):
        return "The glow of untold riches within tempts your greed"


class DragonEgg(Block):
    def __init__(self):
        super().__init__(i.DRAGON_EGG, t.DRAGON_EGG, name="Dragon Egg", img=INV + "dragon_egg.png")

    def get_description(self):
        return "There's definitely something alive in here"


class WorkTable(Block):
    def __init__(self):
        super().__init__(i.WORK_TABLE, t.WORK_TABLE, name="Work Table", img=INV + "work_table.png")

    def get_description(self):
        return "Now you can make pretty furniture!"


class DimensionHopper(Block):
    def __init__(self):
        super().__init__(i.DIMENSION_HOPPER, t.DIMENSION_HOPPER, name="Dimension Hopper",
                         img=INV + "dimension_hopper.png")

    def get_description(self):
        return "A mysterious portal that calls to your adventurous spirit"


class Chest(Block):
    def __init__(self):
        super().__init__(i.CHEST, t.CHEST, name="Chest", img=INV + "chest.png")

    def get_description(self):
        return "Challenge idea: this block is only unlocked after beating the final boss"


class WorldBuilder(Block):
    def __init__(self):
        super().__init__(i.WORLD_BUILDER, t.WORLD_BUILDER, name="World Builder",
                         img=INV + "world_builder/world_builder_0.png")

    def get_description(self):
        return "Channels the energy of biomes to create entire worlds\n" + \
               "Legend says that the presence of certain biome combinations will allow rare creatures to spawn"


class Crusher(Block):
    def __init__(self):
        super().__init__(i.CRUSHER, t.CRUSHER, name="Crusher", img=INV + "crusher/crusher_0.png")

    def get_description(self):
        return "This machine looks powerful enough to crush those shiny stones that you found"
