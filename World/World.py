# Created on 21 December 2019

from os.path import isfile
from sys import byteorder
from numpy import full, int16
import math
import pygame as pg
from pygame.locals import *
from Objects.tile_ids import AIR
from Tools import constants as c
from Tools import objects as o
from UI.Operations import CompleteTask, percent
from World.WorldGenerator import WorldGenerator


class World:
    def __init__(self, universe, name):
        # Visual variables
        self.dim = [0, 0]
        self.surface = None
        self.map = None
        self.minimap_zoom = 2
        self.map_zoom = 1
        self.map_off = [0, 0]
        # World data
        self.blocks = None
        self.spawn = [0, 0]
        self.spawners = {}
        self.animations = {}
        self.block_data = {}
        # File variables
        self.universe = universe
        self.name = name
        self.current_byte = 0
        # World generator
        self.generator = WorldGenerator(self)

    @property
    def file(self):
        return "saves/universes/" + self.universe + "/" + self.name + ".wld"

    # Load world
    def load_part(self, progress):
        from Tools.objects import tiles
        if isfile(self.file):
            # Open file
            with open(self.file, "rb") as file:
                data = file.read()
                # If it's the first time, read dimensions
                if progress == 0:
                    # Reset world data
                    self.spawners.clear()
                    self.block_data.clear()
                    self.animations.clear()
                    self.dim = [int.from_bytes(data[:2], byteorder), int.from_bytes(data[2:4], byteorder)]
                    self.spawn = (int.from_bytes(data[4:6], byteorder), int.from_bytes(data[6:8], byteorder))
                    self.blocks = full((self.dim[1], self.dim[0]), AIR, dtype=int16)
                    self.current_byte = 8
                # Get current height and data for that row
                current_y = int(progress * self.dim[1])
                data = data[self.current_byte:]
                # Write data to array
                num_rows = math.ceil(self.dim[1] / 100)
                for y in range(current_y, min(current_y + num_rows, self.dim[1])):
                    for x in range(self.dim[0]):
                        # Extract tile id
                        val = int.from_bytes(data[:2], byteorder)
                        data = data[2:]
                        self.current_byte += 2
                        if val != AIR:
                            tile = tiles[val]
                            # Save multiblock parts
                            for dy in range(tile.dim[1]):
                                for dx in range(tile.dim[0]):
                                    self.blocks[y + dy][x + dx] = -(dx * 100 + dy)
                            self.blocks[y][x] = val
                            # Save it if it is a spawner
                            if tile.spawner:
                                c.update_dict(x, y, val, self.spawners)
                            if tile.animation:
                                anim = tile.get_animation()
                                if anim is not None:
                                    c.update_dict(x, y, tile.get_animation(), self.animations)
                            # Check if we should be loading extra data
                            num_bytes = tile.data_bytes
                            if num_bytes > 0:
                                c.update_dict(x, y, data[:num_bytes], self.block_data)
                                data = data[num_bytes:]
                                self.current_byte += num_bytes
                return (y + 1) / self.dim[1]

    # Save world
    def save_part(self, progress, num_rows):
        from Tools.objects import tiles
        if self.blocks is not None:
            code = "wb+" if progress == 0 else "ab+"
            with open(self.file, code) as file:
                # If this is the first call, save world dimensions and spawn
                if progress == 0:
                    file.write(self.dim[0].to_bytes(2, byteorder))
                    file.write(self.dim[1].to_bytes(2, byteorder))
                    file.write(self.spawn[0].to_bytes(2, byteorder))
                    file.write(self.spawn[1].to_bytes(2, byteorder))
                # Save the requested rows
                y = int(progress * self.dim[1])
                for dy, row in enumerate(self.blocks[y: min(y + num_rows, self.dim[1])]):
                    for x, val in enumerate(row):
                        # Save the tile id
                        val = int(val)
                        if val < 0 or val == AIR:
                            file.write(AIR.to_bytes(2, byteorder))
                            continue
                        file.write(val.to_bytes(2, byteorder))
                        # Write any extra data
                        num_extra = tiles[val].data_bytes
                        if num_extra > 0:
                            # We have to write the correct number of bytes no matter what
                            # Bad block data is better than bad world data
                            bytes_ = c.get_from_dict(x, y + dy, self.block_data)
                            # Create a new bytearray
                            if bytes_ is None:
                                bytes_ = bytearray(num_extra)
                            else:
                                length = len(bytes_)
                                # Cut off extra bytes
                                if length > num_extra:
                                    bytes_ = bytes_[:num_extra]
                                # Add extra bytes
                                elif length < num_extra:
                                    bytes_ += (0).to_bytes(num_extra - length, byteorder)
                            file.write(bytes_)
                return (y + num_rows) / self.dim[1]
        return 1

    # Multiblocks whose topleft is off screen won't update
    # Go through all x/y and check if x+w is on screen (same for y)
    def update_anim(self, rect):
        from Tools.constants import BLOCK_W
        ymin, ymax = int(rect.top / BLOCK_W), int(rect.bottom / BLOCK_W)
        for x in range(rect.left // BLOCK_W, (rect.right // BLOCK_W) + 1):
            if x in self.animations.keys():
                for y in self.animations[x].keys():
                    if ymin <= y <= ymax:
                        anim = self.animations[x][y]
                        img = anim.get_frame(o.dt)
                        if img is not None:
                            self.surface.blit(img, (x * BLOCK_W, y * BLOCK_W))

    def get_view_rect(self, player_pos):
        dim = pg.display.get_surface().get_size()
        rect = Rect(0, 0, dim[0], dim[1])
        rect.center = player_pos
        for i in (0, 1):
            if rect.topleft[i] < 0:
                rect.topleft[i] = 0
            else:
                ub = self.dim[i] * c.BLOCK_W - dim[i]
                if rect.topleft[i] > ub:
                    rect.topleft[i] = ub
        return rect

    def draw_blocks(self):
        # Calculate pixel dimensions
        dim = (c.BLOCK_W * self.blocks.shape[1], c.BLOCK_W * self.blocks.shape[0])
        self.surface = pg.Surface(dim, SRCALPHA)
        self.map = pg.Surface(self.dim)
        self.map.fill((64, 64, 255))
        one_percent_h = math.ceil(self.dim[1] / 100)

        def draw_row(progress):
            y = int(progress * self.dim[1])
            for y in range(y, min(y + one_percent_h, self.dim[1])):
                for x, val in enumerate(self.blocks[y]):
                    if val != AIR and val >= 0:
                        self.surface.blit(o.tiles[val].image, (x * c.BLOCK_W, y * c.BLOCK_W))
                        tile = o.tiles[val]
                        pg.draw.rect(self.map, tile.map_color, (x, y, *tile.dim))
            return (y + 1) / self.dim[1]

        self.surface.fill(SRCALPHA)
        CompleteTask(draw_row, [], percent, ["Drawing World"]).run_now()

    def destroy_block(self, x, y):
        x, y = self.get_topleft(x, y)
        tile = o.tiles[self.blocks[y][x]]
        # Destroy all parts
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[AIR] * w] * h
        # Redraw block
        block_rect = Rect(x * c.BLOCK_W, y * c.BLOCK_W, c.BLOCK_W * w, c.BLOCK_W * h)
        self.surface.fill(SRCALPHA, block_rect)
        pg.draw.rect(self.map, (64, 64, 255), (x, y, *tile.dim))
        # Update data
        if tile.spawner:
            c.remove_from_dict(x, y, self.spawners)
        if tile.animation:
            c.remove_from_dict(x, y, self.animations)

    def place_block(self, x, y, block):
        tile = o.tiles[block]
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[-(x * 100 + y) for x in range(w)] for y in range(h)]
        self.blocks[y][x] = block
        self.surface.blit(o.tiles[block].image, (x * c.BLOCK_W, y * c.BLOCK_W))
        pg.draw.rect(self.map, tile.map_color, (x, y, *tile.dim))
        if tile.spawner:
            c.update_dict(x, y, block, self.spawners)
        if tile.animation:
            anim = tile.get_animation()
            if anim is not None:
                c.update_dict(x, y, anim, self.animations)

    def get_topleft(self, x, y):
        if 0 <= x < self.dim[0] and 0 <= y < self.dim[1]:
            idx = self.blocks[y][x]
            if idx < 0:
                idx *= -1
                x -= idx // 100
                y -= idx % 100
            return x, y

    def contains_only(self, x, y, dx, dy, tile):
        # If the chunk is outside the world, return false
        if not 0 <= x < self.dim[0] - dx or not 0 <= y < self.dim[1] - dy:
            return False
        for y1 in range(y, y + dy):
            for x1 in range(x, x + dx):
                if self.blocks[y1][x1] != tile:
                    return False
        return True

    def contains(self, x, y, dx, dy, tile):
        # lb must be >= 0, If ub < 0 then d is now <= 0
        if x < 0:
            dx += x
            x = 0
        if y < 0:
            dy += y
            y = 0
        # ub must be < world size, if lb > world size then d is now <= 0
        if x + dx > self.dim[0]:
            dx = self.dim[0] - x
        if y + dy > self.dim[1]:
            dy = self.dim[1] - y
        if not (dx <= 0 or dy <= 0):
            for y1 in range(y, y + dy):
                for x1 in range(x, x + dx):
                    if self.blocks[y1][x1] == tile:
                        return True
        return False

    def adjacent(self, x, y, w, h, tile, only):
        if only:
            if not 1 <= x < self.dim[0] - w + 1 or not 1 <= y < self.dim[1] - h + 1:
                return False
        else:
            # lb must be >= 0, If ub < 0 then d is now <= 0
            if x < 1:
                w += x - 1
                x = 1
            if y < 1:
                h += y - 1
                y = 1
            # ub must be < world size, if lb > world size then d is now <= 0
            if x + w > self.dim[0] - 1:
                w = self.dim[0] - x - 1
            if y + h > self.dim[1] - 1:
                h = self.dim[1] - y - 1
            if w < 0 or h < 0:
                return False
        # Iterate through relevant data
        data = self.blocks[y:y + h, (x - 1, x + w + 1)].flatten() + self.blocks[(y - 1, y + h + 1), x:x + w].flatten()
        for val in data:
            equal = val == tile
            if only and not equal:
                return False
            elif not only and equal:
                return True
        return only

    def get_map(self, dim):
        dim = [min(dim[i], self.dim[i] * self.map_zoom) for i in (0, 1)]
        # Get map width in terms of blocks
        block_dim = (dim[0] / self.map_zoom, dim[1] / self.map_zoom)
        half_dim = (block_dim[0] / 2, block_dim[1] / 2)
        # Calculate top and left of our minimap
        for i in range(2):
            if self.map_off[i] < half_dim[i]:
                self.map_off[i] = half_dim[i]
            elif self.map_off[i] > self.dim[i] - half_dim[i]:
                self.map_off[i] = self.dim[i] - half_dim[i]
        left, top = self.map_off[0] - half_dim[0], self.map_off[1] - half_dim[1]
        # Get the blocks that will be in our map
        b_left, b_top = int(left), int(top)
        b_right, b_bot = math.ceil(left + block_dim[0]), math.ceil(top + block_dim[1])
        b_dim = (b_right - b_left, b_bot - b_top)
        # Draw them onto a surface
        s1 = pg.Surface(b_dim)
        s1.blit(self.map, (0, 0), area=((b_left, b_top), b_dim))
        s1 = pg.transform.scale(s1, (int(b_dim[0] * self.map_zoom), int(b_dim[1] * self.map_zoom)))
        # Cut off the edges
        off_x, off_y = int((left - b_left) * self.map_zoom), int((top - b_top) * self.map_zoom)
        s2 = pg.Surface(dim)
        s2.blit(s1, (0, 0), area=((off_x, off_y), dim))
        return s2

    def get_minimap(self, center):
        from Tools.constants import MAP_W
        # Get map width in terms of blocks
        block_w = MAP_W / self.minimap_zoom
        half_w = block_w / 2
        # Calculate top and left of our minimap
        left, top = [min(max(center[i] - half_w, 0), self.dim[i] - block_w) for i in (0, 1)]
        # Get the blocks that will be in our map
        b_left, b_top = int(left), int(top)
        b_right, b_bot = math.ceil(left + block_w), math.ceil(top + block_w)
        b_dim = (b_right - b_left, b_bot - b_top)
        # Draw them onto a surface
        s1 = pg.Surface(b_dim)
        s1.blit(self.map, (0, 0), area=((b_left, b_top), b_dim))
        s1 = pg.transform.scale(s1, (int(b_dim[0] * self.minimap_zoom), int(b_dim[1] * self.minimap_zoom)))
        # Cut off the edges
        off_x, off_y = int((left - b_left) * self.minimap_zoom), int((top - b_top) * self.minimap_zoom)
        s2 = pg.Surface((MAP_W, MAP_W))
        s2.blit(s1, (0, 0), area=(off_x, off_y, MAP_W, MAP_W))
        return s2

    def move_map(self, keys):
        if keys[K_a]:
            self.map_off[0] -= o.dt / 10
        elif keys[K_d]:
            self.map_off[0] += o.dt / 10
        elif keys[K_w]:
            self.map_off[1] -= o.dt / 10
        elif keys[K_s]:
            self.map_off[1] += o.dt / 10
