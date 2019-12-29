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
        self.surface = None
        self.map = None
        self.minimap_zoom = 2
        self.map_zoom = 1
        self.map_off = [0, 0]
        # World data
        self.dim = [0, 0]
        self.num_blocks = 0
        self.blocks = None
        self.spawn = [0, 0]
        self.spawners = {}
        self.animations = {}
        self.block_data = {}
        self.crafters = {}
        # File variables
        self.universe = universe
        self.name = name
        self.current_byte = 0
        # World generator
        self.generator = WorldGenerator(self)

    @property
    def file(self):
        return "saves/universes/" + self.universe + "/" + self.name + ".wld"

    def new_world(self, dim):
        self.dim = dim
        self.num_blocks = dim[0] * dim[1]
        self.blocks = full((dim[1], dim[0]), AIR, dtype=int16)

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
                    self.num_blocks = self.dim[0] * self.dim[1]
                    self.spawn = (int.from_bytes(data[4:6], byteorder), int.from_bytes(data[6:8], byteorder))
                    self.blocks = full((self.dim[1], self.dim[0]), AIR, dtype=int16)
                    self.current_byte = 8
                data = data[self.current_byte:]
                # Get current row and column and the blocks left to load
                current_block = int(progress * self.num_blocks)
                col, row = current_block % self.dim[0], current_block // self.dim[0]
                blocks_left = math.ceil(self.num_blocks / 100)
                # Write data to array
                while blocks_left > 0:
                    # Extract tile id and number of tiles
                    val = int.from_bytes(data[:2], byteorder)
                    num = int.from_bytes(data[2:4], byteorder)
                    data = data[4:]
                    self.current_byte += 4
                    # Tile defaults to air if it doesn't exist
                    if val not in tiles.keys():
                        val = AIR
                    # Make sure we don't go over the row
                    if col + num > self.dim[0]:
                        num = self.dim[0] - col
                    if val != AIR:
                        tile = tiles[val]
                        # If the block has a width > 1, there is automatically only one block in this strip
                        if tile.dim[0] != 1:
                            # Save multiblock parts
                            for dr in range(tile.dim[1]):
                                for dc in range(tile.dim[0]):
                                    self.blocks[row + dr][col + dc] = -(dr * 100 + dc)
                        self.blocks[row][col:col + num] = [val] * num
                        # Check if we should be loading extra data
                        num_bytes = tile.data_bytes
                        has_bytes = num_bytes > 0
                        # Loop through every block
                        for col1 in range(col, col + num):
                            # Add the block to applicable lists
                            self.add_block(col1, row, val)
                            # Load extra data if the block has any
                            if has_bytes:
                                c.update_dict(col1, row, data[:num_bytes], self.block_data)
                                data = data[num_bytes:]
                                self.current_byte += num_bytes
                    # Update our column and blocks left
                    blocks_left -= num
                    col += num
                    # Check if we made it to the next row
                    if col >= self.dim[0]:
                        col %= self.dim[0]
                        row += 1
                        # Check if we hit the end of the map
                        if row >= self.dim[1]:
                            return 1
                return (row * self.dim[0] + col) / self.num_blocks
        return

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
                # Get current block along with rows and columns to save
                block_num = int(progress * self.num_blocks)
                col, row = block_num % self.dim[0], block_num // self.dim[0]
                blocks_left = int(num_rows * self.dim[0])
                while blocks_left > 0:
                    # Save the tile id
                    val = int(self.blocks[row][col])
                    col1 = col + 1
                    # Keep going until we hit a new tile or the end of the row
                    # This ignores blocks_left so we can store the entire strip of this block type
                    while col1 < self.dim[0]:
                        val1 = self.blocks[row][col1]
                        if val != val1 and (val > 0 or val1 > 0):
                            break
                        col1 += 1
                    num_byte = (col1 - col).to_bytes(2, byteorder)
                    # Need to skip checking bytes in case val < 0
                    if val < 0 or val == AIR:
                        file.write(AIR.to_bytes(2, byteorder))
                        file.write(num_byte)
                    else:
                        # Write data
                        file.write(val.to_bytes(2, byteorder))
                        file.write(num_byte)
                        # Write any extra data
                        num_extra = tiles[val].data_bytes
                        if num_extra > 0:
                            # Write it for each block
                            for x in range(col, col1):
                                # We have to write the correct number of bytes no matter what
                                # Bad block data is better than bad world data
                                bytes_ = c.get_from_dict(x, row, self.block_data)
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
                    # Now that we are done, update our column and blocks left
                    blocks_left -= col1 - col
                    col = col1
                    # Check if we made it to the next row
                    if col >= self.dim[0]:
                        col %= self.dim[0]
                        row += 1
                        # Check if we hit the end of the map
                        if row >= self.dim[1]:
                            return 1
                return (row * self.dim[0] + col) / self.num_blocks
        return 1

    # Update dictionaries
    def add_block(self, x, y, idx):
        tile = o.tiles[idx]
        if tile.spawner:
            c.update_dict(x, y, idx, self.spawners)
        if tile.crafting:
            c.update_dict(x, y, idx, self.crafters)
        if tile.animation:
            anim = tile.get_animation()
            if anim is not None:
                c.update_dict(x, y, anim, self.animations)

    def remove_block(self, x, y, idx):
        tile = o.tiles[idx]
        if tile.spawner:
            c.remove_from_dict(x, y, self.spawners)
        if tile.crafting:
            c.remove_from_dict(x, y, self.crafters)
        if tile.animation:
            c.remove_from_dict(x, y, self.animations)

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
        topleft = list(rect.topleft)
        for i in (0, 1):
            if topleft[i] < 0:
                topleft[i] = 0
            else:
                ub = self.dim[i] * c.BLOCK_W - dim[i]
                if topleft[i] > ub:
                    topleft[i] = ub
        rect.topleft = topleft
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
        if not CompleteTask(draw_row, [], percent, ["Drawing World"]).run_now():
            pg.quit()
            exit(0)

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
        self.remove_block(x, y, tile.idx)

    def place_block(self, x, y, block):
        tile = o.tiles[block]
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[-(x * 100 + y) for x in range(w)] for y in range(h)]
        self.blocks[y][x] = block
        self.surface.blit(o.tiles[block].image, (x * c.BLOCK_W, y * c.BLOCK_W))
        pg.draw.rect(self.map, tile.map_color, (x, y, *tile.dim))
        # Update data
        self.add_block(x, y, block)

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
        left, top, right, bot = True, True, True, True
        # lb must be >= 0, If ub < 0 then d is now <= 0
        if x < 1:
            w += x - 1
            x = 1
            left = False
        if y < 1:
            h += y - 1
            y = 1
            top = False
        # ub must be < world size, if lb > world size then d is now <= 0
        if x + w > self.dim[0] - 1:
            w = self.dim[0] - x - 1
            right = False
        if y + h > self.dim[1] - 1:
            h = self.dim[1] - y - 1
            bot = False
        if not (left or right) or not (top or bot):
            return False
        # Iterate through relevant data
        x_points = ([x - 1] if left else []) + ([x + w] if right else [])
        y_points = ([y - 1] if top else []) + ([y + h] if bot else [])
        data = self.blocks[y:y + h + 1, x_points].flatten() + self.blocks[y_points, x:x + w + 1].flatten()
        for val in data:
            equal = val == tile
            if only and not equal:
                return False
            elif not only and equal:
                return True
        return only

    def get_map(self, dim, sprites=None):
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
        if sprites is not None:
            rect = pg.Rect(b_left * self.map_zoom + off_x, b_top * self.map_zoom + off_y, *dim)
            draw_sprites(s2, rect, self.map_zoom, sprites)
        return s2

    def get_minimap(self, center, sprites=None):
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
        if sprites is not None:
            rect = pg.Rect(b_left * self.minimap_zoom + off_x, b_top * self.minimap_zoom + off_y, MAP_W, MAP_W)
            draw_sprites(s2, rect, self.minimap_zoom, sprites)
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


def draw_sprites(surface, rect, zoom, sprites):
    for key in sprites.keys():
        pos = [int(p * zoom) for p in key]
        if rect.collidepoint(*pos):
            pos[0] -= rect.x
            pos[1] -= rect.y
            img = sprites[key]
            img_rect = img.get_rect(center=pos)
            surface.blit(img, img_rect)
