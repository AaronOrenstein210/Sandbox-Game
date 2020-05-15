# Created on 4 December 2019

from sys import byteorder
from random import choice, uniform
from pygame.locals import *
import Objects
from Objects.TileTypes import *
from Objects.DroppedItem import DroppedItem
from Objects import ItemTypes
from Objects.Animation import Animation
from Objects import INV, PROJ
from NPCs import Mobs as mobs
from Player.ActiveUI import ActiveUI
from Player.Inventory import Inventory
from Tools import constants as c, item_ids as i, tile_ids as t
from Tools import game_vars
from World import WorldGenerator
from World.World import World
from World.Selector import WorldSelector


# Normal Tiles
class Air(LightTile):
    def __init__(self):
        super().__init__(t.AIR, radius=2.5)
        self.barrier = False
        self.map_color = (64, 64, 255)
        self.image.fill(SRCALPHA)


class Dirt(Tile):
    def __init__(self):
        super().__init__(t.DIRT, img=INV + "dirt.png")
        self.add_drop(i.DIRT, 1)
        self.map_color = (150, 75, 0)
        self.hp = 2


class Stone(Tile):
    def __init__(self):
        super().__init__(t.STONE, img=INV + "stone.png")
        self.add_drop(i.STONE, 1)
        self.map_color = (200, 200, 200)
        self.hardness = 1


class Snow(LightTile):
    def __init__(self):
        super().__init__(t.SNOW, img=INV + "snow.png")
        self.add_drop(i.SNOW_BALL, 2, 5)
        self.map_color = (255, 255, 255)


class Wood(Tile):
    def __init__(self):
        super().__init__(t.WOOD, img=INV + "wood_tile.png")
        self.add_drop(i.WOOD, 1)
        self.map_color = (100, 50, 0)


class Leaves(Tile):
    def __init__(self):
        super().__init__(t.LEAVES, img=INV + "leaves.png")
        self.add_drop(i.LEAVES, 1)
        self.map_color = (0, 150, 0)


class Sand(Tile):
    def __init__(self):
        super().__init__(t.SAND, img=INV + "sand.png")
        self.add_drop(i.SAND, 1)
        self.map_color = (255, 224, 140)


class Glass(Tile):
    def __init__(self):
        super().__init__(t.GLASS, img=INV + "glass.png")
        self.map_color = (200, 200, 200)


class Boulder1(Tile):
    def __init__(self):
        super().__init__(t.BOULDER1, img=INV + "boulder_1.png")
        self.add_drop(i.STONE, 0, max_amnt=1)
        self.map_color = (100, 100, 64)
        self.hardness = 1


class Boulder2(Tile):
    def __init__(self):
        super().__init__(t.BOULDER2, img=INV + "boulder_2.png", dim=(2, 1))
        self.map_color = (100, 100, 64)
        self.add_drop(i.STONE, 0, max_amnt=2)
        self.hardness = 1


class Boulder3(Tile):
    def __init__(self):
        super().__init__(t.BOULDER3, img=INV + "boulder_3.png", dim=(3, 2))
        self.map_color = (100, 100, 64)
        self.add_drop(i.STONE, 1, max_amnt=3)
        self.hardness = 1


class ShinyStone1(Tile):
    def __init__(self):
        super().__init__(t.SHINY_STONE_1, img=INV + "shiny_stone_1.png")
        self.add_drop(i.SHINY_STONE_1, 1)
        self.map_color = (175, 175, 175)
        self.hardness = 1


class ShinyStone2(Tile):
    def __init__(self):
        super().__init__(t.SHINY_STONE_2, img=INV + "shiny_stone_2.png")
        self.add_drop(i.SHINY_STONE_2, 1)
        self.map_color = (150, 150, 150)
        self.hardness = 2


class ShinyStone3(Tile):
    def __init__(self):
        super().__init__(t.SHINY_STONE_3, img=INV + "shiny_stone_3.png")
        self.add_drop(i.SHINY_STONE_3, 1)
        self.map_color = (125, 125, 125)
        self.hardness = 3


class Geode(Tile):
    def __init__(self):
        super().__init__(t.GEODE, img=INV + "geode_rock.png")
        self.add_drop(i.GEODE, 1)
        self.hardness = 2


class DragonEgg(Tile):
    def __init__(self):
        super().__init__(t.DRAGON_EGG, img=INV + "dragon_egg.png")
        self.add_drop(i.DRAGON_EGG, 1)
        self.map_color = (64, 200, 0)
        self.hardness = 2

    def on_break(self, pos):
        game_vars.spawn_entity(mobs.Dragon(),
                               [p + randint(10, 20) * BLOCK_W * c.random_sign() for p in game_vars.player_pos()])
        return False


class Portal(Tile):
    def __init__(self):
        super().__init__(t.PORTAL, dim=[2, 3])
        self.barrier = False
        self.updates = self.has_data = True
        self.hardness = -1
        self.map_color = (150, 0, 150)
        self.set_animation(Animation(INV + "portal/", [d * BLOCK_W for d in self.dim], .15))

    def summon(self, pos):
        data = game_vars.get_block_data(pos)
        if data:
            magic = int.from_bytes(data[:8], byteorder)
            # Must have at least 5 magic
            if magic < 5:
                return
            # Every X5 for magic increases max level by 1
            max_level = math.log(magic, 5)
            chance = max(max_level % 1, .5)
            max_level = int(max_level)
            # Find chances for current level and up to two levels below
            if max_level == 1:
                chances = {1: 1}
            elif max_level == 2:
                chances = {2: chance, 1: 1 - chance}
            else:
                chances = {max_level: chance, max_level - 1: (1 - chance) * 2 / 3,
                           max_level - 2: (1 - chance) / 3}
            # Choose a random level
            num = uniform(0, 1)
            for lvl, chance in chances.items():
                if num > chance:
                    num -= chance
                else:
                    # Summon mage
                    # element = choice(list(ItemTypes.MagicContainer.ELEMENT_NAMES.keys()))
                    game_vars.spawn_entity(mobs.Mage(ItemTypes.MagicContainer.FIRE, lvl), [p * BLOCK_W for p in pos])
                    break
            magic = int(magic / 2)
            game_vars.write_block_data(pos, magic.to_bytes(8, byteorder))

    def on_place(self, pos):
        game_vars.write_block_data(pos, bytearray(8))

    def tick(self, x, y, dt):
        magic = 0
        rect = pg.Rect(x * BLOCK_W, y * BLOCK_W, self.dim[0] * BLOCK_W, self.dim[1] * BLOCK_W)
        items = game_vars.handler.items
        for item in items:
            if item.item.magic_value > 0 and item.rect.colliderect(rect):
                magic += item.item.magic_value * item.info.amnt
                items.remove(item)
        if magic > 0:
            data = game_vars.get_block_data((x, y))
            if data:
                current_magic = int.from_bytes(data[:8], byteorder)
                game_vars.write_block_data((x, y), (current_magic + magic).to_bytes(8, byteorder))


# Crafting Stations
class WorkTable(CraftingStation):
    def __init__(self):
        super().__init__(t.WORK_TABLE, dim=(2, 1), img=INV + "work_table.png")
        self.on_surface = True
        self.map_color = (54, 78, 154)
        self.add_drop(i.WORK_TABLE, 1)
        self.hardness = 1

    def get_recipes(self):
        return [[[i.SNOW, 1], [i.SNOW_BALL, 4]],
                [[i.FOREST, 1], [i.DIRT, 50], [i.CAT, 1]],
                [[i.MOUNTAIN, 1], [i.STONE, 10], [i.SNOW, 15]],
                [[i.VALLEY, 1], [i.STONE, 50], [i.ZOMBIE, 1]],
                [[i.DESERT, 1], [i.SAND, 50], [i.GLASS, 15]],
                [[i.BASIC_SWORD, 1], [i.WOOD, 10], [i.STONE, 20]],
                [[i.CRUSHER, 1], [i.STONE, 15], [i.SHINY_STONE_1, 10]],
                [[i.CHEST, 1], [i.WOOD, 15], [i.STONE, 5]],
                [[i.WORLD_BUILDER, 1], [i.STONE, 25], [i.OBSIDIAN, 5]],
                [[i.SNOW_BALL, 1]],
                [[i.MAGIC_BALL, 1], [i.GLASS, 10]],
                [[i.REINFORCED_MAGIC_BALL, 1], [i.MAGIC_BALL, 2], [i.IRON_BAR, 5]],
                [[i.SHINY_MAGIC_BALL, 1], [i.REINFORCED_MAGIC_BALL, 2], [i.GOLD_BAR, 10]],
                [[i.GIANT_MAGIC_BALL, 1], [i.SHINY_MAGIC_BALL, 2], [i.OBSIDIAN, 5]],
                # TODO: Groups of items (e.g. any gem)
                [[i.MAGIC_WAND, 1], [i.WOOD, 5], [i.OPAL, 2]]]


class Forge(CraftingStation):
    def __init__(self):
        super().__init__(t.FORGE, dim=(1, 2))
        self.on_surface = True
        self.map_color = (99, 99, 99)
        self.add_drop(i.FORGE, 1)
        self.hardness = 1
        self.set_animation(Animation(INV + "forge/", [d * BLOCK_W for d in self.dim], .25))

    def get_recipes(self):
        return [[[i.IRON_BAR, 1], [i.IRON_ORE, 2]],
                [[i.GOLD_BAR, 1], [i.GOLD_ORE, 2]],
                [[i.GLASS, 1], [i.SAND, 1]]]


# Spawners
class CatSpawner(SpawnTile):
    def __init__(self):
        super().__init__(t.CAT, mobs.Cat(), item_id=i.CAT)
        self.add_drop(i.CAT, 1)


class ZombieSpawner(SpawnTile):
    def __init__(self):
        super().__init__(t.ZOMBIE, mobs.Zombie(), item_id=i.ZOMBIE)
        self.add_drop(i.ZOMBIE, 1)


class DoomBunnySpawner(SpawnTile):
    def __init__(self):
        super().__init__(t.DOOM_BUNNY, mobs.DoomBunny(), item_id=i.DOOM_BUNNY)
        self.add_drop(i.DOOM_BUNNY, 1)


class HelicopterSpawner(SpawnTile):
    def __init__(self):
        super().__init__(t.HELICOPTER, mobs.Helicopter(), item_id=i.HELICOPTER)
        self.add_drop(i.HELICOPTER, 1)
        self.map_color = (0, 0, 80)


class BirdieSpawner(SpawnTile):
    def __init__(self):
        super().__init__(t.BIRDIE, mobs.Birdie(), item_id=i.BIRDIE)
        self.add_drop(i.BIRDIE, 1)
        self.map_color = (0, 0, 80)


# Tiles that do stuff
class DimensionHopper(FunctionalTile):
    def __init__(self):
        super().__init__(t.DIMENSION_HOPPER, img=INV + "dimension_hopper.png")
        self.barrier = True
        self.scroller = None
        self.add_drop(i.DIMENSION_HOPPER, 1)
        self.map_color = (0, 0, 0)
        self.hardness = 2

    def activate(self, pos):
        game_vars.player.set_active_ui(self.UI(pos))
        return True

    class UI(ActiveUI):
        def __init__(self, pos):
            self.selector = WorldSelector(game_vars.universe())

            ActiveUI.__init__(self, None, None, pos=pos)

            self.on_resize()

        def process_events(self, events, mouse, keys):
            if self.selector.handle_events(events):
                game_vars.player.set_active_ui(None)

        def on_resize(self):
            r = pg.Rect(0, 0, c.MIN_W // 2, c.MIN_H * 3 // 4)
            r.center = c.screen_center
            self.selector.resize(rect=r)
            self.ui, self.rect = self.selector.get_surface(), self.selector.get_rect()


class WorldBuilder(FunctionalTile):
    INV_SPOTS = 6

    def __init__(self):
        super().__init__(t.WORLD_BUILDER)
        self.on_surface = True
        self.add_drop(i.WORLD_BUILDER, 1)
        self.map_color = (0, 0, 0)
        self.hardness = 1
        self.set_animation(Animation(INV + "world_builder/", [d * BLOCK_W for d in self.dim], .25))

    def activate(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            game_vars.player.set_active_ui(self.UI(pos, data))
            return True
        return False

    def on_place(self, pos):
        from Player.Inventory import new_inventory
        game_vars.write_block_data(pos, new_inventory((1, self.INV_SPOTS)))

    def on_break(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            # Check if we have any items
            for byte in data:
                if byte != 0:
                    return False
            # If not, remove our data
            c.remove_from_dict(*pos, game_vars.world.block_data)
        return True

    class UI(ActiveUI):
        BIOME, STRUCTURE, SIZE = range(3)
        INV_ORDER = [BIOME, STRUCTURE, SIZE]

        def __init__(self, pos, data):
            self.name = c.WorldFile(game_vars.universe())
            self.cursor = False
            # Load inventories
            self.invs = {self.BIOME: Inventory((2, 2), max_stack=1, whitelist=game_vars.biomes.keys()),
                         self.STRUCTURE: Inventory((1, 1), max_stack=4, whitelist=[i.BONUS_STRUCTURE]),
                         self.SIZE: Inventory((1, 1), max_stack=1, whitelist=WorldGenerator.WORLD_DIMS.keys())}
            for idx in self.INV_ORDER:
                data = self.invs[idx].load(data)
            # Set text height
            text_h = c.INV_W // 2
            # Text
            text = {self.BIOME: "Biome Cards",
                    self.STRUCTURE: "Bonus Structure",
                    self.SIZE: "Size Card"}
            # Get font and inventory section width
            longest = c.get_widest_string(text.values())
            font = c.get_scaled_font(-1, text_h, longest)
            inv_w = font.size(longest)[0]
            # Get all surfaces to draw
            surfaces = []
            y = 0
            for idx in self.INV_ORDER:
                text_s = font.render(text[idx], 1, (255, 255, 255))
                text_rect = text_s.get_rect(centerx=inv_w // 2, centery=y + text_h // 2)
                surfaces.append([text_s, text_rect])
                y += text_h
                inv = self.invs[idx]
                inv.rect.y, inv.rect.centerx = y, inv_w // 2
                y += inv.rect.h
            # Draw world name text
            text_h = y // 7
            font = c.get_scaled_font(inv_w, text_h, "World Name:")
            text = font.render("World Name:", 1, (255, 255, 255))
            surfaces.append([text, text.get_rect(center=(inv_w * 3 // 2, text_h * 3 // 2))])
            # Draw create button text
            font = c.get_scaled_font(inv_w, text_h * 2, "Create!")
            text = font.render("Create!", 1, (0, 200, 0))
            self.create_rect = text.get_rect(center=(inv_w * 3 // 2, text_h * 5))
            surfaces.append([text, self.create_rect])
            # Used to enter world name
            self.name_rect = pg.Rect(inv_w, text_h * 2, inv_w, text_h)
            # Draw surface
            s = pg.Surface((inv_w * 2, y))
            for surface, rect in surfaces:
                s.blit(surface, rect)
            super().__init__(s, s.get_rect(), pos=pos)
            self.rect.center = c.screen_center

            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()

        @property
        def data(self):
            data = bytearray()
            for idx in self.INV_ORDER:
                data += self.invs[idx].write()
            return data

        def get_inventories(self):
            return list(self.invs.values())

        def tick(self):
            temp = self.cursor
            self.cursor = (pg.time.get_ticks() // 400) % 2 == 0
            if temp != self.cursor:
                self.draw_name()

        def draw_name(self):
            font = c.get_scaled_font(*self.name_rect.size, self.name.name + "|")
            text = font.render(self.name.name + ("|" if self.cursor else ""), 1, (255, 255, 255))
            text_rect = text.get_rect(center=self.name_rect.center)
            self.ui.fill((0, 0, 0), self.name_rect)
            self.ui.blit(text, text_rect)

        def on_inv_pickup(self):
            game_vars.write_block_data(self.block_pos, self.data)

        def process_events(self, events, mouse, keys):
            if self.click_inventories(mouse):
                game_vars.write_block_data(self.block_pos, self.data)
            else:
                pos = pg.mouse.get_pos()
                if self.rect.collidepoint(*pos) and game_vars.player.use_time <= 0:
                    pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                    # Clicked create
                    if self.create_rect.collidepoint(*pos):
                        if not self.invs[self.BIOME].empty and not self.invs[
                            self.SIZE].empty and self.name.valid:
                            for e in events:
                                if e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                                    events.remove(e)
                                    new = World(self.name)
                                    new.can_delete = True
                                    items = [j.item_id for row in self.invs[self.BIOME].inv_items for j in row if
                                             j.is_item]
                                    items += [self.invs[self.SIZE].inv_items[0][0].item_id]
                                    items += [i.BONUS_STRUCTURE] * self.invs[self.STRUCTURE].inv_items[0][0].amnt
                                    WorldGenerator.generate_world(new, modifiers=items)
                                    del new
                                    from Player.Inventory import new_inventory
                                    game_vars.write_block_data(self.block_pos,
                                                               new_inventory((1, WorldBuilder.INV_SPOTS)))
                                    game_vars.player.set_active_ui(None)
                for e in events:
                    if e.type == KEYDOWN:
                        self.name.type_char(e)
                        self.draw_name()


class Chest(FunctionalTile):
    INV_DIM = (10, 5)

    def __init__(self):
        super().__init__(t.CHEST, img=INV + "chest.png", dim=(2, 2))
        self.on_surface = self.barrier = True
        self.add_drop(i.CHEST, 1)
        self.map_color = (200, 200, 0)
        self.hardness = 1

    def on_place(self, pos):
        from Player.Inventory import new_inventory
        game_vars.write_block_data(pos, new_inventory(self.INV_DIM))

    def on_break(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            # Check if we have any i
            for byte in data:
                if byte != 0:
                    return False
            # If not, remove our data
            c.remove_from_dict(*pos, game_vars.world.block_data)
        return True

    def activate(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            game_vars.player.set_active_ui(self.UI(pos, data))
            return True
        return False

    class UI(ActiveUI):
        def __init__(self, pos, data):
            self.inv = Inventory(Chest.INV_DIM)
            ActiveUI.__init__(self, None, self.inv.rect.move(0, self.inv.rect.h),
                              pos=pos)
            self.can_drag = False
            self.inv.load(data)

            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()

        def get_inventories(self):
            return [self.inv]

        def on_inv_pickup(self):
            game_vars.write_block_data(self.block_pos, self.inv.write())

        def process_events(self, events, mouse, keys):
            if self.click_inventories(mouse):
                game_vars.write_block_data(self.block_pos, self.inv.write())


class Crusher(FunctionalTile):
    def __init__(self):
        super().__init__(t.CRUSHER, dim=(2, 2))
        self.on_surface = True
        self.add_drop(i.CRUSHER, 1)
        self.map_color = (64, 64, 64)
        self.hardness = 1
        self.set_animation(Animation(INV + "crusher/", [d * BLOCK_W for d in self.dim], .25))

    def on_place(self, pos):
        game_vars.write_block_data(pos, bytearray(4))

    def on_break(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            item = int.from_bytes(data[:2], byteorder)
            if item in game_vars.items.keys():
                # Drop contents
                from random import choice
                amnt = int.from_bytes(data[2:4], byteorder)
                if amnt > 0:
                    game_vars.drop_item(DroppedItem(ItemInfo(item, amnt)), choice([True, False]),
                                        [pos[0] * BLOCK_W, pos[1] * BLOCK_W])
        game_vars.write_block_data(pos, None)
        return True

    def activate(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            game_vars.player.set_active_ui(self.UI(pos, data, 9))
            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()
            return True
        return False

    class UI(ActiveUI):
        def __init__(self, pos, data, max_stack):
            self.max_stack = max_stack
            # Generate text
            font = c.get_scaled_font(-1, c.INV_IMG_W, "Crush!", "Times New Roman")
            text = font.render("Crush!", 1, (255, 255, 255))
            self.text_rect = text.get_rect(centery=c.INV_W * 3 // 2)
            w = max(self.text_rect.w, c.INV_W)
            self.text_rect.centerx = w // 2
            # Draw surface
            s = pg.Surface((w, c.INV_W * 2))
            s.blit(text, self.text_rect)
            # This is where we will take/add items
            self.inv = Inventory((1, 1), whitelist=Objects.CRUSH_DROPS.keys(), max_stack=9)
            self.inv.rect = pg.Rect((w - c.INV_W) // 2, 0, c.INV_W, c.INV_W)
            self.inv.load(data)

            ActiveUI.__init__(self, s, s.get_rect(), pos=pos)

            self.rect.center = c.screen_center

        def get_inventories(self):
            return [self.inv]

        def save(self):
            game_vars.write_block_data(self.block_pos, self.inv.write())

        def on_inv_pickup(self):
            self.save()

        def process_events(self, events, mouse, keys):
            if self.click_inventories(mouse):
                self.save()
            else:
                pos = pg.mouse.get_pos()
                if self.rect.collidepoint(*pos):
                    pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                    for e in events:
                        item = self.inv.get_item(0, 0)
                        if e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT and \
                                self.text_rect.collidepoint(*pos) and item.is_item:
                            items = {}
                            item = self.inv.inv_items[0][0]
                            # Go through each item and get a random drop
                            while item.is_item:
                                idx = Objects.CRUSH_DROPS[item].random()
                                if idx in items.keys():
                                    items[idx] += 1
                                else:
                                    items[idx] = 1
                                item.amnt -= 1
                            # Drop the results
                            block_pos = [self.block_pos[0] * BLOCK_W, self.block_pos[1] * BLOCK_W]
                            for idx, amnt in zip(items.keys(), items.values()):
                                max_stack = game_vars.items[idx].max_stack
                                # Make sure we don't drop more than max stack
                                while amnt > 0:
                                    transfer = min(max_stack, amnt)
                                    game_vars.drop_item(DroppedItem(ItemInfo(idx, transfer)), choice([True, False]),
                                                        block_pos)
                                    amnt -= transfer
                            self.save()


class UpgradeStation(FunctionalTile):
    def __init__(self):
        super().__init__(t.UPGRADE_STATION, img=INV + "upgrade_station.png", dim=(1, 2))
        self.on_surface = True
        self.add_drop(i.UPGRADE_STATION, 1)
        self.map_color = (200, 0, 200)
        self.hardness = 0
        self.set_animation(self.Anim(self.image))

    def get_block_img(self, pos):
        data = game_vars.get_block_data(pos)
        if data and len(data) >= 2:
            item, amnt = ItemTypes.load_id_amnt(data[:4])
            if item in game_vars.items.keys():
                return game_vars.animations[self.anim_idx].get_frame(img=game_vars.items[item].inv_img)
        return game_vars.animations[self.anim_idx].get_frame()

    def on_place(self, pos):
        game_vars.write_block_data(pos, bytearray(4))

    def on_break(self, pos):
        data = game_vars.get_block_data(pos)
        if data:
            inv = Inventory((1, 1))
            inv.load(data)
            item = inv.get_item(0, 0)
            if item.is_item:
                game_vars.drop_item(DroppedItem(item), c.random_sign(), [p * BLOCK_W for p in pos])
        game_vars.write_block_data(pos, None)
        return True

    def activate(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            game_vars.player.set_active_ui(self.UI(pos, data))
            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()
            return True
        return False

    class UI(ActiveUI):
        def __init__(self, pos, data):
            rect = pg.Rect(0, 0, c.MIN_W // 2, c.MIN_H // 2)
            rect.center = c.screen_center
            super().__init__(pg.Surface(rect.size), rect, pos=pos)

            # Set up inventory for item
            whitelist = [item_id for item_id, item in game_vars.items.items() if isinstance(item, ItemTypes.Upgradable)]
            self.inv = Inventory((1, 1), whitelist=whitelist, max_stack=1)
            self.inv.rect.move_ip((self.rect.w - c.INV_W) // 2, c.INV_W // 2)
            self.inv.load(data)
            # Set up upgrade section with offsets, rect, and surface
            self.dragging = False
            self.off_x = self.off_y = 0
            self.max_x = self.max_y = 0
            y = self.inv.rect.bottom
            self.tree_r = pg.Rect(0, y, self.rect.w, self.rect.h - y)
            self.upgrade_tree = self.tree_s = None
            # Load the data
            self.load_tree()

        def get_inventories(self):
            return [self.inv]

        def draw(self):
            super().draw()
            # Check for hovering over upgrade tree
            if self.upgrade_tree:
                pos = pg.mouse.get_pos()
                if self.rect.collidepoint(*pos):
                    pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                    if self.tree_r.collidepoint(*pos):
                        pos = [pos[0] - self.tree_r.x + self.off_x, pos[1] - self.tree_r.y + self.off_y]
                        self.upgrade_tree.check_hover(pos)

        def save(self):
            item = self.inv.get_item(0, 0)
            if not self.upgrade_tree or not item.is_item:
                item.data = None
            else:
                item.data = self.upgrade_tree.write()
            game_vars.write_block_data(self.block_pos, self.inv.write())

        def draw_tree(self):
            self.ui.fill((0, 0, 0), self.tree_r)
            if self.tree_s:
                self.ui.blit(self.tree_s, self.tree_r, area=((self.off_x, self.off_y), self.tree_r.size))

        def load_tree(self):
            item = self.inv.get_item(0, 0)
            if item.data and item.is_item:
                # Draw upgrade tree and get surface dimensions
                self.upgrade_tree = game_vars.items[item.item_id].upgrade_tree.new_tree()
                self.upgrade_tree.load(item.data)
                self.tree_s = self.upgrade_tree.get_surface()
                s_dim = self.tree_s.get_size()
                # Readjust rectangle
                y = self.inv.rect.bottom
                self.tree_r = pg.Rect(0, y, min(self.rect.w, s_dim[0]), min(self.rect.h - y, s_dim[1]))
                self.tree_r.centerx = self.rect.w // 2
                # Update max scroll and current scroll
                self.max_x = max(0, s_dim[0] - self.tree_r.w)
                self.off_x = self.max_x // 2
                self.max_y = max(0, s_dim[1] - self.tree_r.h)
                self.off_y = 0
            else:
                self.tree_s = None
            # Draw upgrade tree to ui surface
            self.draw_tree()

        def on_inv_pickup(self):
            self.load_tree()
            self.save()

        def process_events(self, events, mouse, keys):
            # Get current item data to check if we changed the item
            prev_data = self.inv.inv_items[0][0].data
            # Drag upgrade screen
            if self.dragging:
                if not mouse[BUTTON_LEFT - 1]:
                    self.dragging = False
                else:
                    self.off_x -= game_vars.d_mouse[0]
                    self.off_x = min(max(0, self.off_x), self.max_x)
                    self.off_y -= game_vars.d_mouse[1]
                    self.off_y = min(max(0, self.off_y), self.max_y)
                    self.draw_tree()
            # Check inventories
            elif self.click_inventories(mouse):
                # If we changed the item data, draw upgrade tree
                if prev_data != self.inv.inv_items[0][0].data:
                    self.load_tree()
                self.save()
            # Handle other events
            else:
                pos = pg.mouse.get_pos()
                if self.rect.collidepoint(*pos):
                    pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                    # Process events
                    for e in events:
                        # Start dragging only if the player is holding nothing
                        if e.type == MOUSEBUTTONDOWN and e.button == BUTTON_LEFT:
                            if self.tree_r.collidepoint(
                                    *pos) and not game_vars.player_inventory().get_held_item().is_item:
                                self.dragging = True
                        # Click the upgrade tree
                        elif e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                            if self.tree_r.collidepoint(*pos) and self.upgrade_tree:
                                pos = [pos[0] - self.tree_r.x + self.off_x, pos[1] - self.tree_r.y + self.off_y]
                                if self.upgrade_tree.click(pos):
                                    self.tree_s = self.upgrade_tree.get_surface()
                                    self.draw_tree()
                                self.save()

    class Anim(Animation):
        def __init__(self, img):
            super().__init__("", [0, 0])
            dim = img.get_size()
            # Set background image
            self.background = img
            # Set up default floating item
            img_w = min(dim[0], dim[1] // 2)
            self.def_img = c.load_image(PROJ + "fire_ball.png", img_w, img_w)
            # Calculate float bounds
            self.min_y, self.max_y = dim[1] // 4, dim[1] // 2
            self.x, self.y = dim[0] // 2, self.max_y
            self.going_up = True

        def update(self, dt):
            dy = (self.max_y - self.min_y) * dt / .75
            if self.going_up:
                self.y -= dy
                if self.y <= self.min_y:
                    self.y = self.min_y
                    self.going_up = False
            else:
                self.y += dy
                if self.y >= self.max_y:
                    self.y = self.max_y
                    self.going_up = True

        def get_frame(self, img=None):
            if not img:
                img = self.def_img
            else:
                w, h = self.def_img.get_size()
                img = c.scale_to_fit(img, w=w, h=h)
            result = self.background.copy()
            result.blit(img, img.get_rect(center=(self.x, self.y)))
            return result


class Pedestal(Tile):
    def __init__(self):
        super().__init__(t.PEDESTAL, img=INV + "pedestal.png")
        self.clickable = self.has_data = self.on_surface = self.img_updates = True
        self.barrier = False
        self.add_drop(i.PEDESTAL, 1)

    # Returns space left in current magic ball, 0 if no item or invalid block
    def get_space(self, x, y):
        tile_id = game_vars.get_block_at(x, y)
        if tile_id == t.PEDESTAL:
            data = game_vars.get_block_data((x, y))
            if data and len(data) > 2:
                item = game_vars.items[int.from_bytes(data[:2], byteorder)]
                if isinstance(item, ItemTypes.MagicContainer):
                    current_amnt = int.from_bytes(data[3:item.int_bytes + 3], byteorder)
                    return item.capacity - current_amnt
        return 0

    def add_magic(self, x, y, amnt):
        data = game_vars.get_block_data((x, y))
        if data and len(data) > 2:
            item = game_vars.items[int.from_bytes(data[:2], byteorder)]
            if isinstance(item, ItemTypes.MagicContainer):
                current_amnt = int.from_bytes(data[3:item.int_bytes + 3], byteorder)
                transfer = min(item.capacity - current_amnt, amnt)
                amnt -= transfer
                new_data = data[:3] + (current_amnt + transfer).to_bytes(item.int_bytes, byteorder)
                game_vars.write_block_data((x, y), new_data)

    def get_block_img(self, pos):
        data = game_vars.get_block_data(pos)
        if data and len(data) > 2:
            item = game_vars.items[int.from_bytes(data[:2], byteorder)]
            if isinstance(item, ItemTypes.MagicContainer):
                final_img = self.image.copy()
                # Draw magic ball
                img_w = BLOCK_W * 3 // 4
                img = c.scale_to_fit(item.image, img_w, img_w)
                img_rect = img.get_rect(center=(BLOCK_W // 2, img_w // 2))
                final_img.blit(img, img_rect)
                element = int.from_bytes(data[2:3], byteorder)
                current_amnt = int.from_bytes(data[3:], byteorder)
                px_h = int(current_amnt * img_w / item.capacity)
                px_arr = pg.surfarray.pixels2d(final_img)
                for y in range(img_rect.bottom - px_h, img_rect.bottom):
                    first = False
                    for x in range(img_rect.left, img_rect.right):
                        if first:
                            if px_arr[x][y] == 0xff000000:
                                break
                            else:
                                px_arr[x][y] = 0xff0000ff
                        else:
                            if px_arr[x][y] == 0xff000000:
                                first = True
                del px_arr
                return final_img
        return self.image

    def on_break(self, pos):
        data = game_vars.get_block_data(pos)
        # There is an item in the pedestal
        if data:
            item = ItemInfo(int.from_bytes(data[:2], byteorder), 1, data=data[2:])
            game_vars.drop_item(DroppedItem(item), c.random_sign(),
                                [p * BLOCK_W + d * BLOCK_W // 2 for p, d in zip(pos, self.dim)])
            game_vars.write_block_data(pos, None)
        return True

    def activate(self, pos):
        item = game_vars.player_inventory().get_current_item()
        data = game_vars.get_block_data(pos)
        # There is an item in the pedestal
        if data and (not item.is_item or item.item_id != i.MAGIC_WAND):
            item = ItemInfo(int.from_bytes(data[:2], byteorder), 1, data=data[2:])
            game_vars.drop_item(DroppedItem(item), c.random_sign(),
                                [p * BLOCK_W + d * BLOCK_W // 2 for p, d in zip(pos, self.dim)])
            game_vars.write_block_data(pos, None)
            game_vars.player.use_time = .3
            return True
        # There is no item in the pedestal, Make sure we clicked with a magic container item
        elif item.is_item and isinstance(game_vars.items[item.item_id], ItemTypes.MagicContainer):
            game_vars.write_block_data(pos, item.item_id.to_bytes(2, byteorder) + item.data)
            item.amnt -= 1
            game_vars.player.use_time = .3
            return True
        return False
