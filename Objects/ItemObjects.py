# Created on 3 December 2019

from pygame.locals import *
from Objects import INV
from Objects.ItemTypes import *
from Objects.UpgradeObjects import head, chest, legs, feet
from Tools.constants import *
from Tools import game_vars, item_ids as i, tile_ids as t
from NPCs.Entity import Projectile
from NPCs import Mobs


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
            self.max_bounces = 3


class DragonClaw(Item):
    def __init__(self):
        super().__init__(i.DRAGON_CLAW, img=INV + "dragon_claw.png", name="Dragon Claw")
        self.consumable = True

    def on_left_click(self):
        game_vars.spawn_entity(Mobs.MainBoss(),
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
        data = game_vars.player_inventory().get_current_item().data
        if data:
            pos = [int.from_bytes(data[2 * j:2 * (j + 1)], byteorder) * BLOCK_W for j in range(2)]
            game_vars.player.set_pos(pos)

    def on_right_click(self):
        pos = game_vars.player_topleft(True)
        data = int(pos[0]).to_bytes(2, byteorder)
        data += int(pos[1]).to_bytes(2, byteorder)
        game_vars.player_inventory().get_current_item().data = data

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


class DesertBiome(Item):
    def __init__(self):
        super().__init__(i.DESERT, img=INV + "desert.png", name="Desert Biome")

    def get_description(self, data):
        return "Pulsates with the power of the Desert"


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


class IronBar(Item):
    def __init__(self):
        super().__init__(i.IRON_BAR, img=INV + "iron_bar.png", name="Iron Bar")


class GoldOre(Item):
    def __init__(self):
        super().__init__(i.GOLD_ORE, img=INV + "gold_ore.png", name="Gold Ore")


class GoldBar(Item):
    def __init__(self):
        super().__init__(i.GOLD_BAR, img=INV + "gold_bar.png", name="Gold Bar")


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


class Geode(Item):
    def __init__(self):
        super().__init__(i.GEODE, img=INV + "geode.png", name="Geode")

    def get_description(self, data):
        return "So many pretty colors, maybe we should try crushing it"


class Jade(Item):
    def __init__(self):
        super().__init__(i.JADE, img=INV + "jade.png", name="Jade")
        self.magic_value = 1


class Pearl(Item):
    def __init__(self):
        super().__init__(i.PEARL, img=INV + "pearl.png", name="Pearl")
        self.magic_value = 1


class Amethyst(Item):
    def __init__(self):
        super().__init__(i.AMETHYST, img=INV + "amethyst.png", name="Amethyst")
        self.magic_value = 2


class Sapphire(Item):
    def __init__(self):
        super().__init__(i.SAPPHIRE, img=INV + "sapphire.png", name="Sapphire")
        self.magic_value = 3


class Opal(Item):
    def __init__(self):
        super().__init__(i.OPAL, img=INV + "opal.png", name="Opal")
        self.magic_value = 3


class MagicWand(Item):
    def __init__(self):
        super().__init__(i.MAGIC_WAND, img=INV + "magic_wand.png", name="Magic Wand")
        self.right_click = True

    def on_left_click(self):
        pos = game_vars.get_topleft(*game_vars.global_mouse_pos(blocks=True))
        item_id = game_vars.get_block_at(*pos)
        if item_id == t.PORTAL:
            data = game_vars.get_block_data(pos)
            if data:
                # TODO: ingame message system
                print("Magic Stored:", int.from_bytes(data, byteorder))

    def on_right_click(self):
        item = game_vars.player_inventory().get_current_item()
        if item.item_id != i.MAGIC_WAND:
            return
        entities = game_vars.handler.entities
        # Check if we clicked on a mage
        pos = game_vars.global_mouse_pos(blocks=False)
        for key, entity in entities.items():
            if isinstance(entity, Mobs.Mage) and entity.rect.collidepoint(pos):
                print("Selected mage")
                item.data = key.to_bytes(2, byteorder)
                entity.target = (-1, -1)
                return
        # Get the clicked on tile
        pos = game_vars.get_topleft(*game_vars.global_mouse_pos(blocks=True))
        tile_id = game_vars.get_block_at(*pos)
        # Check if we clicked on a pedestal
        if item.data and tile_id == t.PEDESTAL:
            key = int.from_bytes(item.data[:2], byteorder)
            if isinstance(entities.get(key), Mobs.Mage):
                print("Bound mage")
                entities[key].set_target(pos)
                entities[key].set_pos(pos[0] * BLOCK_W, (pos[1] - entities[key].dim[1]) * BLOCK_W)
            item.data = None
        # Check if we clicked on a portal
        elif tile_id == t.PORTAL:
            game_vars.tiles[t.PORTAL].summon(pos)

    def get_description(self, data):
        return "Portals: Left click to display current magic amount\n" + \
               "         Right click to summon a mage, consuming magic\n" + \
               "Mages: Right click on a mage to select\n" + \
               "Right click again on a pedestal to assign that mage to the pedestal"


# Other Items


class MagicBall(MagicContainer):
    def __init__(self):
        super().__init__(i.MAGIC_BALL, capacity=100, img=INV + "magic_ball.png", name="Magic Ball")


class ReinforcedMagicBall(MagicContainer):
    def __init__(self):
        super().__init__(i.REINFORCED_MAGIC_BALL, capacity=500, img=INV + "reinforced_magic_ball.png",
                         name="Reinforced Magic Ball")


class ShinyMagicBall(MagicContainer):
    def __init__(self):
        super().__init__(i.SHINY_MAGIC_BALL, capacity=2500, img=INV + "shiny_magic_ball.png", name="Shiny Magic Ball")


class GiantMagicBall(MagicContainer):
    def __init__(self):
        super().__init__(i.GIANT_MAGIC_BALL, capacity=10000, img=INV + "giant_magic_ball.png", name="Giant Magic Ball")


# Blocks
class Dirt(Placeable):
    def __init__(self):
        super().__init__(i.DIRT, t.DIRT, name="Dirt", img=INV + "dirt.png")


class Stone(Placeable):
    def __init__(self):
        super().__init__(i.STONE, t.STONE, name="Stone", img=INV + "stone.png")


class Snow(Placeable):
    def __init__(self):
        super().__init__(i.SNOW, t.SNOW, name="Snow", img=INV + "snow.png")


class Wood(Placeable):
    def __init__(self):
        super().__init__(i.WOOD, t.WOOD, name="Wood", img=INV + "wood_item.png")


class Leaves(Placeable):
    def __init__(self):
        super().__init__(i.LEAVES, t.LEAVES, name="Leaves", img=INV + "leaves.png")


class Sand(Placeable):
    def __init__(self):
        super().__init__(i.SAND, t.SAND, name="Sand", img=INV + "sand.png")


class Glass(Placeable):
    def __init__(self):
        super().__init__(i.GLASS, t.GLASS, name="Glass", img=INV + "glass.png")


class ShinyStone1(Placeable):
    def __init__(self):
        super().__init__(i.SHINY_STONE_1, t.SHINY_STONE_1, name="Shiny Stone: Tier 1",
                         img=INV + "shiny_stone_1.png")

    def get_description(self, data):
        return "You can kind of see something shiny inside"


class ShinyStone2(Placeable):
    def __init__(self):
        super().__init__(i.SHINY_STONE_2, t.SHINY_STONE_2, name="Shiny Stone: Tier 2",
                         img=INV + "shiny_stone_2.png")

    def get_description(self, data):
        return "Ooh, this rock is pretty"


class ShinyStone3(Placeable):
    def __init__(self):
        super().__init__(i.SHINY_STONE_3, t.SHINY_STONE_3, name="Shiny Stone: Tier 3",
                         img=INV + "shiny_stone_3.png")

    def get_description(self, data):
        return "The glow of untold riches within tempts your greed"


class DragonEgg(Placeable):
    def __init__(self):
        super().__init__(i.DRAGON_EGG, t.DRAGON_EGG, name="Dragon Egg", img=INV + "dragon_egg.png")

    def get_description(self, data):
        return "There's definitely something alive in here"


class WorkTable(Placeable):
    def __init__(self):
        super().__init__(i.WORK_TABLE, t.WORK_TABLE, name="Work Table", img=INV + "work_table.png")

    def get_description(self, data):
        return "Now you can make pretty furniture!"


class Forge(Placeable):
    def __init__(self):
        super().__init__(i.FORGE, t.FORGE, img=INV + "forge/forge_0.png")

    def get_description(self, data):
        return "I should really make a sweaty debuff for players near a forge"


class DimensionHopper(Placeable):
    def __init__(self):
        super().__init__(i.DIMENSION_HOPPER, t.DIMENSION_HOPPER, name="Dimension Hopper",
                         img=INV + "dimension_hopper.png")

    def get_description(self, data):
        return "A mysterious portal that calls to your adventurous spirit"


class Chest(Placeable):
    def __init__(self):
        super().__init__(i.CHEST, t.CHEST, name="Chest", img=INV + "chest.png")

    def get_description(self, data):
        return "Challenge idea: this block is only unlocked after beating the final boss"


class WorldBuilder(Placeable):
    def __init__(self):
        super().__init__(i.WORLD_BUILDER, t.WORLD_BUILDER, name="World Builder",
                         img=INV + "world_builder/world_builder_0.png")

    def get_description(self, data):
        return "Channels the energy of biomes to create entire worlds\n" + \
               "Legend says that the presence of certain biome combinations will allow rare creatures to spawn"


class Crusher(Placeable):
    def __init__(self):
        super().__init__(i.CRUSHER, t.CRUSHER, name="Crusher", img=INV + "crusher/crusher_0.png")

    def get_description(self, data):
        return "This machine looks powerful enough to crush those shiny stones that you found"


class UpgradeStation(Placeable):
    def __init__(self):
        super().__init__(i.UPGRADE_STATION, t.UPGRADE_STATION, name="Upgrade Station", img=INV + "upgrade_station.png")


class Pedestal(Placeable):
    def __init__(self):
        super().__init__(i.PEDESTAL, t.PEDESTAL, name="Pedestal", img=INV + "pedestal.png")

    def get_description(self, data):
        return "Place a magic ball on a pedestal to begin channeling magic into it"


# Weapons/Tools
class TestSword(Weapon):
    def __init__(self):
        super().__init__(i.BASIC_SWORD, head, stats=Stats(WEAPON_STATS, damage=7, use_time=.5),
                         img=INV + "basic_sword.png", name="Basic Sword")

    def on_left_click(self):
        game_vars.shoot_projectile(self.P1(game_vars.player.rect.center, game_vars.global_mouse_pos()))

    def get_description(self, data):
        return "Your basic sword\nIt has so much potential"

    class P1(Projectile):
        def __init__(self, pos, target):
            super().__init__(pos, target, w=.5, img=INV + "snow_ball.png", speed=10)
            self.hurts_mobs = True


class TestPickaxe(Tool):
    def __init__(self):
        super().__init__(i.BASIC_PICKAXE, head, img=INV + "basic_pickaxe.png", name="Basic Pickaxe",
                         stats=Stats(TOOL_STATS, damage=3, use_time=.3, power=10))
        self.auto_use = True
        self.breaks_blocks = True

    def get_description(self, data):
        return "Your basic pickaxe\nIt has so much potential"


# Armor
class Helmet(Armor):
    def __init__(self):
        super().__init__(i.HELMET, head, img=INV + "helmet.png", name="Helmet")
        self.max_stack = 1

    def get_description(self, data):
        return "A handy helmet to protect your head from falling meteors"


class Chestplate(Armor):
    def __init__(self):
        super().__init__(i.CHESTPLATE, chest, img=INV + "chestplate.png", name="Chestplate")
        self.max_stack = 1

    def get_description(self, data):
        return "A thick chestplate to protect you during snowball fights"


class Leggings(Armor):
    def __init__(self):
        super().__init__(i.LEGGINGS, legs, img=INV + "leggings.png", name="Leggings")
        self.max_stack = 1

    def get_description(self, data):
        return "These are purely decorative, to be worn only as a fashion statement"


class Boots(Armor):
    def __init__(self):
        super().__init__(i.BOOTS, feet, img=INV + "boots.png", name="Boots")
        self.max_stack = 1

    def get_description(self, data):
        return "Their extra wide soles make jumping in rain puddles a blast!"
