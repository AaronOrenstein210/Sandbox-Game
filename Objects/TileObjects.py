# Created on 4 December 2019

import pygame as pg
from pygame.locals import *
from Objects.TileTypes import *
from Objects.Animation import Animation
from Objects import item_ids as i, tile_ids as t
from NPCs import Mobs as mobs
from Player.ActiveUI import ActiveUI
from Tools import constants as c
from Tools import objects as o
from World import WorldGenerator as wg
from World.World import World
from UI.Operations import TextInput


class Air(Tile):
    def __init__(self):
        Tile.__init__(self, t.AIR)


class Dirt(Tile):
    def __init__(self):
        Tile.__init__(self, t.DIRT, hardness=1, img=INV + "dirt.png")
        self.add_drop(i.DIRT, 1)
        self.map_color = (150, 75, 0)


class Stone(Tile):
    def __init__(self):
        Tile.__init__(self, t.STONE, hardness=2, img=INV + "stone.png")
        self.add_drop(i.STONE, 1)
        self.map_color = (200, 200, 200)


class Snow(Tile):
    def __init__(self):
        Tile.__init__(self, t.SNOW, hardness=1, img=INV + "snow.png")
        self.add_drop(i.SNOW_BALL, 2, 5)
        self.map_color = (255, 255, 255)


class WorkTable(CraftingStation):
    def __init__(self):
        CraftingStation.__init__(self, t.WORK_TABLE, dim=(2, 1), img=INV + "work_table.png")
        self.on_surface = True
        self.map_color = (54, 78, 154)
        self.add_drop(i.WORK_TABLE, 1)

    def get_recipes(self):
        return [[[i.SNOW, 1], [i.SNOW_BALL, 4]],
                [[i.FOREST, 1], [i.DIRT, 50], [i.CAT, 1]],
                [[i.MOUNTAIN, 1], [i.STONE, 10], [i.SNOW, 15]],
                [[i.VALLEY, 1], [i.STONE, 50], [i.ZOMBIE, 1]]]


class CatSpawner(SpawnTile):
    def __init__(self):
        SpawnTile.__init__(self, t.CAT, mobs.Cat)
        self.add_drop(i.CAT, 1)


class ZombieSpawner(SpawnTile):
    def __init__(self):
        SpawnTile.__init__(self, t.ZOMBIE, mobs.Zombie)
        self.add_drop(i.ZOMBIE, 1)


class DoomBunnySpawner(SpawnTile):
    def __init__(self):
        SpawnTile.__init__(self, t.DOOM_BUNNY, mobs.DoomBunny)
        self.add_drop(i.DOOM_BUNNY, 1)


class DimensionHopper(Tile):
    def __init__(self):
        Tile.__init__(self, t.DIMENSION_HOPPER, hardness=2, img=INV + "dimension_hopper.png")
        self.has_ui = True
        self.clickable = True
        self.scroller = None
        self.add_drop(i.DIMENSION_HOPPER, 1)
        self.map_color = (0, 0, 0)

    def activate(self, pos):
        o.player.active_ui = self.UI(pos)

    class UI(ActiveUI):
        def __init__(self, pos):
            from os import listdir
            from Tools.VerticalScroller import VerticalScroller

            dim = (c.MIN_W // 2, c.MIN_H * 3 // 4)

            ActiveUI.__init__(self, pg.Surface(dim), pg.Rect((0, 0), dim), pos=pos)
            self.on_resize()
            self.scroller = VerticalScroller(self.rect.size, background=(0, 200, 128))

            font = c.get_scaled_font(self.rect.w, int(self.rect.h / 8), "_" * 25, "Times New Roman")
            for file in listdir("saves/universes/" + o.world.universe):
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
                            o.change_world(world)
                            o.player.active_ui = None
                    else:
                        continue
                elif e.type == KEYUP and e.key == K_ESCAPE:
                    keys[K_ESCAPE] = False
                    o.player.active_ui = None
                else:
                    continue

        def on_resize(self):
            self.rect.center = pg.display.get_surface().get_rect().center


class WorldBuilder(Tile):
    INV_DIM = (4, 2)

    def __init__(self):
        Tile.__init__(self, t.WORLD_BUILDER, img=INV + "world_builder_0.png")
        self.animation = True
        self.has_ui = True
        self.clickable = True
        self.on_surface = True
        self.data_bytes = 4 * self.INV_DIM[0] * self.INV_DIM[1]
        self.add_drop(i.WORLD_BUILDER, 1)
        self.map_color = (0, 0, 0)

    def get_animation(self):
        return Animation([INV + "world_builder_{}.png".format(i) for i in range(6)],
                         [BLOCK_W, BLOCK_W], delay=250)

    def activate(self, pos):
        data = c.get_from_dict(*pos, o.world.block_data)
        if data is not None:
            o.player.active_ui = self.UI(pos, data)

    def on_place(self, pos):
        from Player.Inventory import new_inventory
        c.update_dict(*pos, new_inventory(self.INV_DIM), o.world.block_data)

    def on_break(self, pos):
        data = c.get_from_dict(*pos, o.world.block_data)
        if data is not None:
            # Check if we have any i
            for byte in data:
                if byte != 0:
                    return False
            # If not, remove our data
            c.remove_from_dict(*pos, o.world.block_data)
        return True

    class UI(ActiveUI):
        biomes = {i.FOREST: wg.FOREST,
                  i.MOUNTAIN: wg.MOUNTAIN,
                  i.VALLEY: wg.VALLEY}

        def __init__(self, pos, data):
            from Player.Inventory import Inventory
            self.text_input = None
            self.inventory = Inventory(WorldBuilder.INV_DIM)
            self.inventory.load(data)
            inv_dim = self.inventory.surface.get_size()
            self.inv_w = inv_dim[0]
            # Draw create text
            font = c.get_scaled_font(-1, inv_dim[1] // 2, "Create!", "Times New Roman")
            text = font.render("Create!", -1, (255, 255, 255))
            text_rect = text.get_rect(centery=inv_dim[1] // 2, left=inv_dim[0])
            # Create surface
            s = pg.Surface((inv_dim[0] + text_rect.w, inv_dim[1]))
            s.blit(self.inventory.surface, (0, 0))
            s.blit(text, text_rect)
            ActiveUI.__init__(self, s, s.get_rect(), pos=pos)
            self.on_resize()

            if not o.player.inventory.open:
                o.player.inventory.toggle()

        def process_events(self, events, mouse, keys):
            pos = pg.mouse.get_pos()
            if self.text_input is not None:
                world_name = self.text_input.check_events(events)
                if world_name is not None:
                    if world_name != "":
                        new = World(o.world.universe, world_name)
                        biomes = []
                        for y, row in enumerate(self.inventory.inv_items):
                            for x, item in enumerate(row):
                                if item in self.biomes.keys():
                                    biomes += [self.biomes[item]] * self.inventory.inv_amnts[y][x]
                        new.generator.generate((1000, 500), biomes)
                        del new
                        from Player.Inventory import new_inventory
                        c.update_dict(*self.block_pos, new_inventory(WorldBuilder.INV_DIM), o.world.block_data)
                    o.player.active_ui = None
            elif self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                if pos[0] > self.inv_w:
                    for e in events:
                        if e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                            events.remove(e)
                            self.text_input = TextInput("Input World Name", char_limit=10)
                            self.ui = self.text_input.surface
                            self.rect = self.ui.get_rect()
                            self.on_resize()
                elif o.player.use_time <= 0:
                    p_item = o.player.inventory.selected_item
                    if p_item == -1 or p_item in self.biomes.keys():
                        if mouse[BUTTON_LEFT - 1]:
                            o.player.use_time = self.inventory.left_click(pos)
                        elif mouse[BUTTON_RIGHT - 1]:
                            o.player.use_time = self.inventory.right_click(pos)
                        c.update_dict(*self.block_pos, self.inventory.write(), o.world.block_data)
                        self.ui.fill((0, 0, 0), self.inventory.rect)
                        self.ui.blit(self.inventory.surface, (0, 0))
            if keys[K_ESCAPE]:
                o.player.active_ui = None
                keys[K_ESCAPE] = False

        def on_resize(self):
            self.rect.center = pg.display.get_surface().get_rect().center


class Chest(Tile):
    INV_DIM = (10, 5)

    def __init__(self):
        Tile.__init__(self, t.CHEST, hardness=1, img=INV + "chest.png", dim=(2, 2))
        self.has_ui = True
        self.clickable = True
        self.on_surface = True
        self.data_bytes = 4 * self.INV_DIM[0] * self.INV_DIM[1]
        self.add_drop(i.CHEST, 1)
        self.map_color = (200, 200, 0)

    def on_place(self, pos):
        from Player.Inventory import new_inventory
        c.update_dict(*pos, new_inventory(self.INV_DIM), o.world.block_data)

    def on_break(self, pos):
        data = c.get_from_dict(*pos, o.world.block_data)
        if data is not None:
            # Check if we have any i
            for byte in data:
                if byte != 0:
                    return False
            # If not, remove our data
            c.remove_from_dict(*pos, o.world.block_data)
        return True

    def activate(self, pos):
        data = c.get_from_dict(*pos, o.world.block_data)
        if data is not None:
            o.player.active_ui = self.UI(pos, data)

    class UI(ActiveUI):
        def __init__(self, pos, data):
            from Player.Inventory import Inventory
            self.inventory = Inventory(Chest.INV_DIM)
            ActiveUI.__init__(self, self.inventory.surface,
                              self.inventory.rect.move(0, self.inventory.rect.h), pos=pos)
            self.inventory.load(data)

            if not o.player.inventory.open:
                o.player.inventory.toggle()

        def process_events(self, events, mouse, keys):
            pos = pg.mouse.get_pos()
            if self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                if o.player.use_time <= 0:
                    if mouse[BUTTON_LEFT - 1]:
                        o.player.use_time = self.inventory.left_click(pos)
                    elif mouse[BUTTON_RIGHT - 1]:
                        o.player.use_time = self.inventory.right_click(pos)
                    c.update_dict(*self.block_pos, self.inventory.write(), o.world.block_data)
            if keys[K_ESCAPE]:
                o.player.active_ui = None
                keys[K_ESCAPE] = False
