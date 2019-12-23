# Created on 21 December 2019

from os.path import isfile
from sys import byteorder
from numpy import full, int16
import math
import pygame as pg
from pygame.locals import *
from Objects.tile_ids import AIR
from Tools.constants import update_dict, get_from_dict, remove_from_dict, \
    BLOCK_W, MAP_W
from Tools import objects as o
from UI.Operations import CompleteTask
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
    def load_part(self, progress, num_rows):
        from Tools.objects import tiles
        if isfile(self.file):
            # Open file
            with open(self.file, "rb") as file:
                data = file.read()
                # If it's the first time, read dimensions
                if progress == 0:
                    self.dim = [int.from_bytes(data[:2], byteorder), int.from_bytes(data[2:4], byteorder)]
                    self.spawn = (int.from_bytes(data[4:6], byteorder), int.from_bytes(data[6:8], byteorder))
                    self.blocks = full((self.dim[1], self.dim[0]), AIR, dtype=int16)
                    self.current_byte = 8
                # Get current height and data for that row
                current_y = int(progress * self.dim[1])
                data = data[self.current_byte:]
                # Write data to array
                for y in range(current_y, min(current_y + num_rows, self.dim[1])):
                    for x in range(self.dim[0]):
                        # Extract tile id
                        val = int.from_bytes(data[:2], byteorder)
                        data = data[2:]
                        self.current_byte += 2
                        if val != AIR:
                            self.blocks[y][x] = val
                            # Save it if it is a spawner
                            if tiles[val].spawner:
                                update_dict(x, y, val, self.spawners)
                            # Check if we should be loading extra data
                            num_bytes = tiles[val].data_bytes
                            if num_bytes > 0:
                                update_dict(x, y, data[:num_bytes], self.block_data)
                                data = data[num_bytes:]
                                self.current_byte += num_bytes
                return float((y + 1) / self.dim[1])

    # Save world
    def save_part(self, progress, num_rows):
        from Tools.objects import tiles
        if self.blocks is not None:
            code = "wb+" if progress == 0 else "ab+"
            with open(self.file, code) as file:
                # If this is the first call, save world dimensions ad spawn
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
                        file.write(val.to_bytes(2, byteorder))
                        # Write any extra data
                        num_extra = tiles[val].data_bytes
                        if num_extra > 0:
                            # We have to write the correct number of bytes no matter what
                            # Bad block data is better than bad world data
                            bytes_ = get_from_dict(x, y + dy, self.block_data)
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

    def get_view_rect(self, player_pos):
        dim = pg.display.get_surface().get_size()
        rect = Rect(0, 0, dim[0], dim[1])
        rect.center = player_pos
        for i in (0, 1):
            if rect.topleft[i] < 0:
                rect.topleft[i] = 0
            else:
                ub = self.dim[i] * BLOCK_W - dim[i]
                if rect.topleft[i] > ub:
                    rect.topleft[i] = ub
        return rect

    def draw_blocks(self):
        # Calculate pixel dimensions
        dim = (BLOCK_W * self.blocks.shape[1], BLOCK_W * self.blocks.shape[0])
        self.surface = pg.Surface(dim, SRCALPHA)
        self.map = pg.Surface(self.dim)
        self.map.fill((64, 64, 255))

        def draw_row(progress):
            y = int(progress * self.dim[1])
            for x, val in enumerate(self.blocks[y]):
                if val != AIR:
                    self.surface.blit(o.tiles[val].image, (x * BLOCK_W, y * BLOCK_W))
                    self.map.set_at((x, y), o.tiles[val].map_color)
            return (y + 1) / self.dim[1]

        self.surface.fill(SRCALPHA)
        CompleteTask(draw_row, draw_args=("Drawing World",)).run_now()

    def destroy_block(self, pos):
        # Get block coords and break the block if it is not air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if self.blocks[y][x] != AIR:
            old = self.blocks[y][x]
            self.blocks[y][x] = AIR
            block_rect = Rect(int(pos[0] / BLOCK_W) * BLOCK_W, int(pos[1] / BLOCK_W) * BLOCK_W,
                              BLOCK_W, BLOCK_W)
            self.surface.fill(SRCALPHA, block_rect)
            self.map.set_at((x, y), (64, 64, 255))
            if o.tiles[old].spawner:
                remove_from_dict(x, y, self.spawners)
            return old
        return AIR

    def place_block(self, pos, block):
        # Get block coords and place the block if it is currently air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if self.blocks[y][x] == AIR and len(self.get_adjacent(x, y)) > 0:
            self.blocks[y][x] = block
            self.surface.blit(o.tiles[block].image, (x * BLOCK_W, y * BLOCK_W))
            self.map.set_at((x, y), o.tiles[block].map_color)
            if o.tiles[block].spawner:
                update_dict(x, y, block, self.spawners)
            return True
        return False

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

    def get_adjacent(self, x, y):
        # Get adjacent o.blocks
        adj_blocks = []
        for x1, y1 in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 < x1 < self.dim[0] and 0 < y1 < self.dim[1] and self.blocks[y1][x1] != AIR:
                adj_blocks.append(self.blocks[y1][x1])
        return adj_blocks
