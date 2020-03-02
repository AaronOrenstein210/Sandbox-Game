# Created on 4 December 2019

from sys import byteorder
from random import choice
from pygame.locals import *
from Objects.TileTypes import *
from Objects.DroppedItem import DroppedItem
from Objects import INV
from NPCs import Mobs as mobs
from Player.ActiveUI import ActiveUI
from Player.Inventory import Inventory
from Tools import constants as c, item_ids as i, tile_ids as t
from Tools import game_vars
from World import WorldGenerator
from World.World import World


# Normal Tiles
class Air(Tile):
    def __init__(self):
        super().__init__(t.AIR)


class Dirt(Tile):
    def __init__(self):
        super().__init__(t.DIRT, hardness=1, img=INV + "dirt.png")
        self.add_drop(i.DIRT, 1)
        self.map_color = (150, 75, 0)


class Stone(Tile):
    def __init__(self):
        super().__init__(t.STONE, hardness=2, img=INV + "stone.png")
        self.add_drop(i.STONE, 1)
        self.map_color = (200, 200, 200)


class Snow(Tile):
    def __init__(self):
        super().__init__(t.SNOW, hardness=1, img=INV + "snow.png")
        self.add_drop(i.SNOW_BALL, 2, 5)
        self.map_color = (255, 255, 255)


class Wood(Tile):
    def __init__(self):
        super().__init__(t.WOOD, hardness=1, img=INV + "wood_tile.png")
        self.add_drop(i.WOOD, 1)
        self.map_color = (100, 50, 0)


class Leaves(Tile):
    def __init__(self):
        super().__init__(t.LEAVES, hardness=0, img=INV + "leaves.png")
        self.add_drop(i.LEAVES, 1)
        self.map_color = (0, 150, 0)


class Boulder1(Tile):
    def __init__(self):
        super().__init__(t.BOULDER1, hardness=0, img=INV + "boulder_1.png")
        self.add_drop(i.STONE, 0, max_amnt=1)
        self.map_color = (100, 100, 64)


class Boulder2(Tile):
    def __init__(self):
        super().__init__(t.BOULDER2, hardness=0, img=INV + "boulder_2.png", dim=(2, 1))
        self.map_color = (100, 100, 64)
        self.add_drop(i.STONE, 0, max_amnt=2)


class Boulder3(Tile):
    def __init__(self):
        super().__init__(t.BOULDER3, hardness=0, img=INV + "boulder_3.png", dim=(3, 2))
        self.map_color = (100, 100, 64)
        self.add_drop(i.STONE, 1, max_amnt=3)


class ShinyStone1(Tile):
    def __init__(self):
        super().__init__(t.SHINY_STONE_1, hardness=1, img=INV + "shiny_stone_1.png")
        self.add_drop(i.SHINY_STONE_1, 1)
        self.map_color = (175, 175, 175)


class ShinyStone2(Tile):
    def __init__(self):
        super().__init__(t.SHINY_STONE_2, hardness=1, img=INV + "shiny_stone_2.png")
        self.add_drop(i.SHINY_STONE_2, 1)
        self.map_color = (150, 150, 150)


class ShinyStone3(Tile):
    def __init__(self):
        super().__init__(t.SHINY_STONE_3, hardness=1, img=INV + "shiny_stone_3.png")
        self.add_drop(i.SHINY_STONE_3, 1)
        self.map_color = (125, 125, 125)


class DragonEgg(Tile):
    def __init__(self):
        super().__init__(t.DRAGON_EGG, hardness=3, img=INV + "dragon_egg.png")
        self.add_drop(i.DRAGON_EGG, 1)
        self.map_color = (64, 200, 0)

    def on_break(self, pos):
        game_vars.spawn_entity(mobs.Dragon(),
                               [p + randint(10, 20) * BLOCK_W * c.random_sign() for p in game_vars.player_pos()])
        return False


# End


# Crafting Stations
class WorkTable(CraftingStation):
    def __init__(self):
        super().__init__(t.WORK_TABLE, dim=(2, 1), img=INV + "work_table.png")
        self.on_surface = True
        self.map_color = (54, 78, 154)
        self.add_drop(i.WORK_TABLE, 1)

    def get_recipes(self):
        return [[[i.SNOW, 1], [i.SNOW_BALL, 4]],
                [[i.FOREST, 1], [i.DIRT, 50], [i.CAT, 1]],
                [[i.MOUNTAIN, 1], [i.STONE, 10], [i.SNOW, 15]],
                [[i.VALLEY, 1], [i.STONE, 50], [i.ZOMBIE, 1]],
                [[i.BASIC_SWORD, 1], [i.WOOD, 10], [i.STONE, 20]],
                [[i.CRUSHER, 1], [i.STONE, 15], [i.SHINY_STONE_1, 10]],
                [[i.CHEST, 1], [i.WOOD, 15], [i.STONE, 5]],
                [[i.WORLD_BUILDER, 1], [i.STONE, 25], [i.OBSIDIAN, 5]],
                [[i.SNOW_BALL, 1]]]


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


# End


# Tiles that do stuff
class DimensionHopper(FunctionalTile):
    def __init__(self):
        super().__init__(t.DIMENSION_HOPPER, 0, hardness=2, img=INV + "dimension_hopper.png")
        self.scroller = None
        self.add_drop(i.DIMENSION_HOPPER, 1)
        self.map_color = (0, 0, 0)

    def activate(self, pos):
        game_vars.set_active_ui(self.UI(pos))

    class UI(ActiveUI):
        def __init__(self, pos):
            from os import listdir
            from Tools.VerticalScroller import VerticalScroller

            dim = (c.MIN_W // 2, c.MIN_H * 3 // 4)

            ActiveUI.__init__(self, pg.Surface(dim), pg.Rect((0, 0), dim), pos=pos)
            self.on_resize()
            self.scroller = VerticalScroller(self.rect.size, background=(0, 200, 128))

            font = c.get_scaled_font(self.rect.w, int(self.rect.h / 8), "_" * 25, "Times New Roman")
            for file in listdir("saves/universes/" + game_vars.world.universe):
                if file.endswith(".wld"):
                    name = file[:-4]
                    text = font.render(name, 1, (255, 255, 255))
                    self.scroller.add_item(text, name)

            self.ui.blit(self.scroller.surface, (0, 0))
            pg.draw.rect(self.ui, (0, 0, 0), self.ui.get_rect(), 2)

        def process_events(self, events, mouse, keys):
            for e in events:
                if e.type == BUTTON_WHEELUP or e.type == BUTTON_WHEELDOWN:
                    self.scroller.do_scroll(e.type == BUTTON_WHEELUP)
                    self.ui.blit(self.scroller.surface, (0, self.scroller.scroll))
                    pg.draw.rect(self.ui, (0, 0, 0), self.ui.get_rect(), 2)
                elif e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                    pos = pg.mouse.get_pos()
                    if self.rect.collidepoint(*pos):
                        mouse[BUTTON_LEFT - 1] = False
                        pos = (pos[0] - self.rect.x, pos[1] - self.rect.y)
                        world = self.scroller.click(pos)
                        if world != "":
                            game_vars.change_world(world)
                            game_vars.set_active_ui(None)
                    else:
                        continue
                elif e.type == KEYUP and e.key == K_ESCAPE:
                    keys[K_ESCAPE] = False
                    game_vars.set_active_ui(None)
                else:
                    continue

        def on_resize(self):
            self.rect.center = pg.display.get_surface().get_rect().center


class WorldBuilder(FunctionalTile):
    INV_SPOTS = 6

    def __init__(self):
        super().__init__(t.WORLD_BUILDER, 4 * self.INV_SPOTS, img=INV + "world_builder/")
        self.on_surface = True
        self.add_drop(i.WORLD_BUILDER, 1)
        self.map_color = (0, 0, 0)

    def activate(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            game_vars.set_active_ui(self.UI(pos, data))

    def on_place(self, pos):
        from Player.Inventory import new_inventory
        game_vars.write_block_data(pos, new_inventory((1, self.INV_SPOTS)))

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

    class UI(ActiveUI):
        BIOME, STRUCTURE, SIZE = range(3)
        INV_ORDER = [BIOME, STRUCTURE, SIZE]

        def __init__(self, pos, data):
            self.name = ""
            self.cursor = False
            # Load inventories
            invs = {self.BIOME: Inventory((2, 2), max_stack=1, items_list=game_vars.biomes.keys()),
                    self.STRUCTURE: Inventory((1, 1), max_stack=4, items_list=[i.BONUS_STRUCTURE]),
                    self.SIZE: Inventory((1, 1), max_stack=1, items_list=WorldGenerator.WORLD_DIMS.keys())}
            for idx in self.INV_ORDER:
                # Load data
                num_bytes = invs[idx].num_bytes
                invs[idx].load(data[:num_bytes])
                data = data[num_bytes:]
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
                inv = invs[idx]
                inv.rect.y, inv.rect.centerx = y, inv_w // 2
                surfaces.append([inv.surface, inv.rect])
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
            super().__init__(s, s.get_rect(), pos=pos, invs=invs)
            self.on_resize()

            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()

        @property
        def data(self):
            data = bytearray()
            for idx in self.INV_ORDER:
                data += self.invs[idx].write()
            return data

        def process_events(self, events, mouse, keys):
            temp = self.cursor
            self.cursor = (pg.time.get_ticks() // 400) % 2 == 0
            if temp != self.cursor:
                self.draw_name()
            pos = pg.mouse.get_pos()
            if self.rect.collidepoint(*pos) and game_vars.player.use_time <= 0:
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                # Clicked create
                if self.create_rect.collidepoint(*pos):
                    if not self.invs["Biome"].is_empty() and not self.invs["Size"].is_empty() and self.name != "":
                        for e in events:
                            if e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                                events.remove(e)
                                new = World(game_vars.world.universe, self.name)
                                items = self.invs["Biome"].inv_items.flatten().tolist()
                                items += [self.invs["Size"].inv_items[0][0]]
                                items += [i.BONUS_STRUCTURE] * self.invs["Structure"].inv_amnts[0][0]
                                WorldGenerator.generate_world(new, modifiers=items)
                                del new
                                from Player.Inventory import new_inventory
                                game_vars.write_block_data(self.block_pos, new_inventory((1, WorldBuilder.INV_SPOTS)))
                                game_vars.set_active_ui(None)
                # Clicked inventories
                else:
                    for inv in self.invs.values():
                        if inv.rect.collidepoint(*pos):
                            pos = [pos[0] - inv.rect.x, pos[1] - inv.rect.y]
                            if mouse[BUTTON_LEFT - 1]:
                                inv.left_click(pos)
                            elif mouse[BUTTON_RIGHT - 1]:
                                inv.right_click(pos)
                            self.ui.fill((0, 0, 0), inv.rect)
                            self.ui.blit(inv.surface, inv.rect)
                            game_vars.write_block_data(self.block_pos, self.data)
                            break
            if keys[K_ESCAPE]:
                game_vars.set_active_ui(None)
                keys[K_ESCAPE] = False
            for e in events:
                if e.type == KEYDOWN:
                    if e.key == K_BACKSPACE:
                        self.name = self.name[:-1]
                    elif e.key == K_SPACE:
                        self.name += " "
                    elif len(pg.key.name(e.key)) == 1:
                        self.name += e.unicode
                    else:
                        continue
                    self.draw_name()

        def draw_name(self):
            font = c.get_scaled_font(*self.name_rect.size, self.name + "|")
            text = font.render(self.name + ("|" if self.cursor else ""), 1, (255, 255, 255))
            text_rect = text.get_rect(center=self.name_rect.center)
            self.ui.fill((0, 0, 0), self.name_rect)
            self.ui.blit(text, text_rect)

        def on_resize(self):
            self.rect.center = pg.display.get_surface().get_rect().center


class Chest(FunctionalTile):
    INV_DIM = (10, 5)

    def __init__(self):
        super().__init__(t.CHEST, 4 * self.INV_DIM[0] * self.INV_DIM[1], hardness=1, img=INV + "chest.png",
                         dim=(2, 2))
        self.on_surface = True
        self.add_drop(i.CHEST, 1)
        self.map_color = (200, 200, 0)

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
            game_vars.set_active_ui(self.UI(pos, data))

    class UI(ActiveUI):
        def __init__(self, pos, data):
            inventory = Inventory(Chest.INV_DIM)
            ActiveUI.__init__(self, inventory.surface, inventory.rect.move(0, inventory.rect.h),
                              pos=pos, invs={0: inventory})
            self.invs[0].load(data)

            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()

        def process_events(self, events, mouse, keys):
            pos = pg.mouse.get_pos()
            if self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                if game_vars.player.use_time <= 0:
                    if mouse[BUTTON_LEFT - 1]:
                        self.invs[0].left_click(pos)
                    elif mouse[BUTTON_RIGHT - 1]:
                        self.invs[0].right_click(pos)
                    game_vars.write_block_data(self.block_pos, self.invs[0].write())
            if keys[K_ESCAPE]:
                game_vars.set_active_ui(None)
                keys[K_ESCAPE] = False


class Crusher(FunctionalTile):
    def __init__(self):
        super().__init__(t.CRUSHER, 4, img=INV + "crusher/", dim=(2, 2))
        self.on_surface = True
        self.add_drop(i.CRUSHER, 1)
        self.map_color = (64, 64, 64)

    def on_place(self, pos):
        game_vars.write_block_data(pos, bytearray(4))

    def on_break(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            amnt = int.from_bytes(data[:2], byteorder)
            if amnt != 0:
                # Drop contents
                from random import choice
                item = int.from_bytes(data[2:4], byteorder)
                game_vars.player.drop_item(DroppedItem(item, amnt), choice([True, False]),
                                           [pos[0] * BLOCK_W, pos[1] * BLOCK_W])
        game_vars.write_block_data(pos, None)
        return True

    def activate(self, pos):
        data = game_vars.get_block_data(pos)
        if data is not None:
            game_vars.set_active_ui(self.UI(pos, data, 9))
            if not game_vars.player.inventory.open:
                game_vars.player.inventory.toggle()

    class UI(ActiveUI):
        ITEMS = [i.SHINY_STONE_1, i.SHINY_STONE_2, i.SHINY_STONE_3]

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
            inventory = Inventory((1, 1), items_list=self.ITEMS, max_stack=9)
            inventory.rect = pg.Rect((w - c.INV_W) // 2, 0, c.INV_W, c.INV_W)
            inventory.load(data)
            s.blit(inventory.surface, inventory.rect)

            ActiveUI.__init__(self, s, s.get_rect(), pos=pos, invs={0: inventory})

            self.on_resize()

        def on_resize(self):
            self.rect.center = pg.display.get_surface().get_rect().center

        def process_events(self, events, mouse, keys):
            pos = pg.mouse.get_pos()
            if self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                for e in events:
                    if e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT and \
                            self.text_rect.collidepoint(*pos) and self.invs[0].inv_amnts[0][0] != 0:
                        from Objects import CRUSH_DROPS
                        items = {}
                        item = self.invs[0].inv_items[0][0]
                        # Go through each item and get a random drop
                        while self.invs[0].inv_amnts[0][0] > 0:
                            idx, amnt = CRUSH_DROPS[item](randint(1, 100))
                            if idx in items.keys():
                                items[idx] += amnt
                            else:
                                items[idx] = amnt
                            self.invs[0].inv_amnts[0][0] -= 1
                        # Drop the results
                        block_pos = [self.block_pos[0] * BLOCK_W, self.block_pos[1] * BLOCK_W]
                        for idx, amnt in zip(items.keys(), items.values()):
                            max_stack = game_vars.items[idx].max_stack
                            # Make sure we don't drop more than max stack
                            while amnt > 0:
                                transfer = min(max_stack, amnt)
                                item_obj = DroppedItem(idx, transfer)
                                game_vars.player.drop_item(item_obj, choice([True, False]), block_pos)
                                amnt -= transfer
                        game_vars.write_block_data(self.block_pos, self.invs[0].write())
                        self.invs[0].update_item(0, 0)

                if game_vars.player.use_time <= 0 and self.invs[0].rect.collidepoint(*pos):
                    pos = [pos[0] - self.invs[0].rect.x, pos[1] - self.invs[0].rect.y]
                    if mouse[BUTTON_LEFT - 1]:
                        self.invs[0].left_click(pos)
                    elif mouse[BUTTON_RIGHT - 1]:
                        self.invs[0].right_click(pos)
                    game_vars.write_block_data(self.block_pos, self.invs[0].write())

                self.ui.fill((0, 0, 0), self.invs[0].rect)
                self.ui.blit(self.invs[0].surface, self.invs[0].rect)

            if keys[K_ESCAPE]:
                game_vars.write_block_data(self.block_pos, self.invs[0].write())
                game_vars.set_active_ui(None)
