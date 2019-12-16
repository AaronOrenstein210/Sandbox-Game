# Created on 4 December 2019

from sys import byteorder
import pygame as pg
from pygame.locals import *
from Objects.TileTypes import *
from Objects import item_ids as items, tile_ids as tiles
from NPCs import Mobs as mobs
from Player.ActiveUI import ActiveUI
from Tools import constants as c
from Tools import objects as o


class Air(Tile):
    def __init__(self):
        Tile.__init__(self, tiles.AIR)


class Dirt(Tile):
    def __init__(self):
        Tile.__init__(self, tiles.DIRT, hardness=1, img=INV + "dirt.png")
        self.add_drop(items.DIRT, 1)
        self.map_color = (150, 75, 0)


class Stone(Tile):
    def __init__(self):
        Tile.__init__(self, tiles.STONE, hardness=2, img=INV + "stone.png")
        self.add_drop(items.STONE, 1)
        self.map_color = (200, 200, 200)


class Snow(Tile):
    def __init__(self):
        Tile.__init__(self, tiles.SNOW, hardness=1, img=INV + "snow.png")
        self.add_drop(items.SNOW, 1)
        self.map_color = (255, 255, 255)


class CatSpawner(SpawnTile):
    def __init__(self):
        SpawnTile.__init__(self, tiles.CAT, mobs.Cat)
        self.add_drop(items.CAT, 1)


class ZombieSpawner(SpawnTile):
    def __init__(self):
        SpawnTile.__init__(self, tiles.ZOMBIE, mobs.Zombie)
        self.add_drop(items.ZOMBIE, 1)


class DimensionHopper(Tile):
    def __init__(self):
        Tile.__init__(self, tiles.DIMENSION_HOPPER, hardness=2, img=INV + "dimension_hopper.png")
        self.has_ui = True
        self.clickable = True
        self.scroller = None
        self.add_drop(items.DIMENSION_HOPPER, 1)
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
            for file in listdir("saves/universes/" + o.universe_name):
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


class Chest(Tile):
    def __init__(self):
        Tile.__init__(self, tiles.CHEST, hardness=1, img=INV + "chest.png")
        self.has_ui = True
        self.clickable = True
        self.data_bytes = 200
        self.add_drop(items.CHEST, 1)
        self.map_color = (200, 200, 0)

    def on_place(self, pos):
        from Player.Inventory import new_inventory
        c.update_dict(*pos, new_inventory((5, 10)), o.block_data)

    def on_break(self, pos):
        data = c.get_from_dict(*pos, o.block_data)
        if data is not None:
            # Check if we have any items
            while len(data) > 0:
                if int.from_bytes(data[:2], byteorder) > 0:
                    return False
                data = data[4:]
            # If not, remove our data
            c.remove_from_dict(*pos, o.block_data)
        return True

    def activate(self, pos):
        data = c.get_from_dict(*pos, o.block_data)
        if data is not None:
            o.player.active_ui = self.UI(pos, data)

    class UI(ActiveUI):
        def __init__(self, pos, data):
            from Player.Inventory import Inventory
            self.inventory = Inventory()
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
                    c.update_dict(*self.block_pos, self.inventory.write(), o.block_data)
            if keys[K_ESCAPE]:
                o.player.active_ui = None
                keys[K_ESCAPE] = False
