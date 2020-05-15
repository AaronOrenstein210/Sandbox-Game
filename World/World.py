# Created on 21 December 2019

from sys import byteorder
import numpy as np
import math
import pygame as pg
from pygame.locals import *
from Tools.tile_ids import AIR
from Tools import constants as c
from Tools import game_vars
from NPCs.Mobs import Mage, load_mage
from World.Chunk import ChunkManager

# World types
WORLD, IDLE = range(2)


class World:
    def __init__(self, world_file):
        # Visual variables
        self.map = None
        self.light = None
        # World type
        self.type = WORLD  # 1 bytes
        # Can we delete the world
        self.can_delete = False  # 1 bytes
        # World time
        self.time = c.SEC_PER_DAY * .4  # 2 bytes
        # World spawn location
        self.spawn = [0, 0]  # 4 bytes
        # World dimensions and number of blocks
        self.dim = [0, 0]  # 4 bytes
        self.num_blocks = 0
        # 2D array of world blocks
        self.blocks = None
        # Special blocks whose positions need to be stored
        self.block_data = {}
        self.spawners = {}
        self.crafters = {}
        # File variables
        self.file = world_file
        self.f_obj = open(self.file.full_file, 'ab+')
        self.f_obj.close()
        # Auto save variables
        self.next_save = 30
        self.save_progress = 0

        self.manager = ChunkManager(self)

    @property
    def surface_h(self):
        return self.dim[1] // 2

    @property
    def underground(self):
        return self.dim[1] * 2 // 3

    @property
    def sky_color(self):
        return 0, 0, 255 * (1 - pow((self.time - c.NOON) / c.NOON, 2))

    def tick(self, dt):
        self.time = (self.time + dt) % c.SEC_PER_DAY
        # Run auto save
        self.next_save -= game_vars.dt
        if self.next_save <= 0:
            self.save_progress = self.save_world(self.save_progress)
            if self.save_progress >= 1:
                self.save_progress = 0
                self.next_save = 30
                game_vars.player.write()
        # Update minimap
        pos = game_vars.player_pos(True)
        left, top = max(int(pos[0] - 10), 0), max(int(pos[1] - 10), 0)
        # Go through every row, column pair where the color is black
        section = pg.surfarray.pixels2d(self.map)[left:math.ceil(pos[0] + 10), top:math.ceil(pos[1] + 10)]
        for x, y in zip(*np.where(section == 0)):
            map_color = game_vars.tiles[game_vars.get_block_at(left + x, top + y)].map_color
            section[x][y] = self.map.map_rgb(map_color)
        del section

        self.manager.tick(dt)

    def new_world(self, dim):
        self.dim = list(dim)
        self.num_blocks = dim[0] * dim[1]
        self.blocks = np.full((dim[1], dim[0]), AIR, dtype=np.int16)
        self.map = pg.Surface(dim)

    # Load world information
    # @param close_file: should we close the file when done
    def load_info(self, close_file):
        # Open the file
        self.f_obj.close()
        self.f_obj = open(self.file.full_file, 'rb')
        # Load file data
        self.can_delete = bool.from_bytes(self.f_obj.read(1), byteorder)
        self.type = int.from_bytes(self.f_obj.read(1), byteorder)
        self.time = int.from_bytes(self.f_obj.read(2), byteorder)
        self.dim = [int.from_bytes(self.f_obj.read(2), byteorder) for i in range(2)]
        self.spawn = [int.from_bytes(self.f_obj.read(2), byteorder) for i in range(2)]
        # Calculate number of blocks
        self.num_blocks = self.dim[0] * self.dim[1]
        # Check if we should close the file
        if close_file:
            self.f_obj.close()

    # Loads world blocks
    def load_blocks(self, progress):
        # Get current row and column and the blocks left to load
        current_block = int(progress * self.num_blocks + .5 / self.num_blocks)
        col, row = current_block % self.dim[0], current_block // self.dim[0]
        blocks_left = math.ceil(self.num_blocks / 100)
        # Write data to array
        while blocks_left > 0:
            # Extract tile id and number of tiles
            val = int.from_bytes(self.f_obj.read(2), byteorder)
            num = int.from_bytes(self.f_obj.read(2), byteorder)
            # Tile defaults to air if it doesn't exist
            if val not in game_vars.tiles.keys():
                val = AIR
            # Make sure we don't go over the row
            if col + num > self.dim[0]:
                num = self.dim[0] - col
            if val != AIR:
                tile = game_vars.tiles[val]
                # If the block has a width > 1, there is automatically only one block in this strip
                if tile.dim[0] != 1:
                    # Save multiblock parts
                    for dr in range(tile.dim[1]):
                        for dc in range(tile.dim[0]):
                            self.blocks[row + dr][col + dc] = -(dc * 100 + dr)
                    self.blocks[row][col] = val
                # Otherwise, it is either a single block or a vertical multiblock
                else:
                    # Load single block (top left)
                    self.blocks[row][col:col + num] = [val] * num
                    # Load vertical multiblock
                    for i in range(1, tile.dim[1]):
                        self.blocks[row + i, col:col + num] = [-i] * num
                # Loop through every block
                for col1 in range(col, col + num):
                    # Add the block to applicable lists
                    self.add_block(col1, row, val)
                    # Load extra data if the block has any
                    if tile.has_data:
                        amnt = int.from_bytes(self.f_obj.read(2), byteorder)
                        c.update_dict(col1, row, self.f_obj.read(amnt), self.block_data)
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
        # If we are done, close the file
        return (row * self.dim[0] + col) / self.num_blocks

    # Draws the entire world and map
    def draw_world(self, progress):
        if progress == 0:
            # Calculate pixel dimensions
            self.map = pg.Surface(self.dim)
            self.map.fill(game_vars.tiles[AIR].map_color)
            self.light = pg.Surface(self.dim, SRCALPHA)
        map_arr = pg.surfarray.pixels2d(self.map)
        one_percent_h = math.ceil(self.dim[1] / 100)
        light_arr = pg.surfarray.pixels_alpha(self.light)
        # Load world
        y = int(progress * self.dim[1] + .5 / self.dim[1])
        for y in range(y, min(y + one_percent_h, self.dim[1])):
            # Get initial section
            explored = bool.from_bytes(self.f_obj.read(1), byteorder)
            length = int.from_bytes(self.f_obj.read(2), byteorder)
            if not explored:
                map_arr[:length, y] = [0] * length
            # Loop through row
            for x, val in enumerate(self.blocks[y]):
                if val != AIR:
                    light_arr[x][y] = 255
                    if val >= 0:
                        if explored:
                            tile = game_vars.tiles[val]
                            color_int = self.map.map_rgb(tile.map_color)
                            map_arr[x:x + tile.dim[0], y:y + tile.dim[1]] = [[color_int] * tile.dim[1]] * tile.dim[0]
                length -= 1
                # If we finished this map section, get next section length and flip explored
                if length == 0 and x < self.dim[0] - 1:
                    explored = not explored
                    length = int.from_bytes(self.f_obj.read(2), byteorder)
                    if not explored:
                        map_arr[x + 1:x + length + 1, y] = [0] * length
        return (y + 1) / self.dim[1]

    # Load world
    def load_world(self, progress):
        if progress == 0:
            # Reset world data
            self.block_data.clear()
            self.spawners.clear()
            # Load world info, automatically opens the file
            self.load_info(False)
            self.blocks = np.full((self.dim[1], self.dim[0]), AIR, dtype=np.int16)
        progress *= 2
        if progress < 1:
            return self.load_blocks(progress) / 2
        else:
            result = self.draw_world(progress - 1) / 2 + .5
            if result == 1:
                self.f_obj.close()
                self.manager.setup()
                self.manager.load_all()
            return result

    # Saves world information
    def save_info(self):
        # Open the file in write mode
        self.f_obj.close()
        self.f_obj = open(self.file.full_file, 'wb')
        # Write data
        self.f_obj.write(self.can_delete.to_bytes(1, byteorder))
        self.f_obj.write(self.type.to_bytes(1, byteorder))
        self.f_obj.write(int(self.time).to_bytes(2, byteorder))
        for val in self.dim + self.spawn:
            self.f_obj.write(val.to_bytes(2, byteorder))

    # Save world blocks
    def save_blocks(self, progress, num_rows):
        # If there is no data, just end the process
        if self.blocks is None:
            return 1
        # Get current block along with rows and columns to save
        block_num = int(progress * self.num_blocks + .5 / self.num_blocks)
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
                self.f_obj.write(AIR.to_bytes(2, byteorder))
                self.f_obj.write(num_byte)
            else:
                # Write data
                self.f_obj.write(val.to_bytes(2, byteorder))
                self.f_obj.write(num_byte)
                # Write any extra data
                if game_vars.tiles[val].has_data:
                    # Write it for each block
                    for x in range(col, col1):
                        # We have to write the correct number of bytes no matter what
                        # Bad block data is better than bad world data
                        bytes_ = c.get_from_dict(x, row, self.block_data)
                        # Create a new bytearray
                        if bytes_ is None:
                            self.f_obj.write(bytearray(2))
                        else:
                            self.f_obj.write(len(bytes_).to_bytes(2, byteorder))
                            self.f_obj.write(bytes_)
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

    # Saves map data
    def save_map(self, progress):
        if not self.map:
            return 1
        # Get current row
        row = int(progress * self.dim[1] + .5 / self.dim[1])
        arr = pg.surfarray.array2d(self.map)[:, row]
        # Figure out which sections have been explored
        self.f_obj.write(bool(arr[0] != 0).to_bytes(1, byteorder))
        result = [i + 1 for i, (v1, v2) in enumerate(zip(arr[:-1], arr[1:])) if (v1 == 0) != (v2 == 0)]
        for v1, v2 in zip([0] + result, result + [len(arr)]):
            self.f_obj.write((v2 - v1).to_bytes(2, byteorder))
        return (row + 1) / self.dim[1]

    # Save world
    def save_world(self, progress):
        if progress == 0:
            # Save world information, automatically opens the file
            self.save_info()
        progress *= 2
        if progress < 1:
            return self.save_blocks(progress, 1) / 2
        else:
            result = self.save_map(progress - 1) / 2 + .5
            if result == 1:
                self.f_obj.close()
            return result

    # Update block
    def place_block(self, x, y, block):
        tile = game_vars.tiles[block]
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[-(x * 100 + y) for x in range(w)] for y in range(h)]
        self.blocks[y][x] = block
        pg.draw.rect(self.map, tile.map_color, (x, y, *tile.dim))
        light_arr = pg.surfarray.pixels_alpha(self.light)
        light_arr[x:x + tile.dim[0], y:y + tile.dim[1]] = [[255] * tile.dim[1]] * tile.dim[0]
        # Update data
        self.add_block(x, y, block)
        self.manager.block_change(x, y, block, True)

    def destroy_block(self, x, y):
        x, y = game_vars.get_topleft(x, y)
        tile_id = self.blocks[y][x]
        tile = game_vars.tiles[tile_id]
        # Destroy all parts
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[AIR] * w] * h
        # Redraw block
        pg.draw.rect(self.map, (64, 64, 255), (x, y, *tile.dim))
        light_arr = pg.surfarray.pixels_alpha(self.light)
        light_arr[x:x + tile.dim[0], y:y + tile.dim[1]] = [[0] * tile.dim[1]] * tile.dim[0]
        # Update data
        self.remove_block(x, y, tile.idx)
        self.manager.block_change(x, y, tile_id, False)

    # Update dictionaries
    def add_block(self, x, y, idx):
        tile = game_vars.tiles[idx]
        if tile.crafting:
            c.update_dict(x, y, idx, self.crafters)
        if tile.spawner:
            c.update_dict(x, y, idx, self.spawners)

    def remove_block(self, x, y, idx):
        tile = game_vars.tiles[idx]
        if tile.crafting:
            c.remove_from_dict(x, y, self.crafters)
        if tile.spawner:
            c.remove_from_dict(x, y, self.spawners)

    def get_screen_rect(self, player_pos):
        dim = pg.display.get_surface().get_size()
        rect = Rect((0, 0), dim)
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

    # Draws light
    def draw_light(self, rect):
        # Draw light surface
        left, top = int(rect.x / c.BLOCK_W), int(rect.y / c.BLOCK_W)
        right, bot = math.ceil(rect.right / c.BLOCK_W), math.ceil(rect.bottom / c.BLOCK_W)
        off_x, off_y = rect.x % c.BLOCK_W, rect.y % c.BLOCK_W
        b_dim = (right - left, bot - top)
        light = pg.Surface(b_dim, SRCALPHA)
        light.blit(self.light, (0, 0), area=((left, top), b_dim))
        light.fill((0, 0, 0, 255 - self.sky_color[-1]), special_flags=BLEND_RGBA_ADD)
        light = pg.transform.scale(light, (b_dim[0] * c.BLOCK_W, b_dim[1] * c.BLOCK_W))
        air_light = game_vars.tiles[AIR].light_s.copy()
        air_light.fill((0, 0, 0, 255 - self.sky_color[-1]), special_flags=BLEND_RGBA_SUB)
        radius = int(air_light.get_size()[0] / c.BLOCK_W / 2)
        r = pg.Rect(0, 0, c.BLOCK_W, c.BLOCK_W)
        y_lb, y_ub = max(top - radius, 0), min(bot + radius, self.dim[1])
        x_lb, x_ub = max(left - radius, 0), min(right + radius, self.dim[0])
        for y, x in zip(*np.where(self.blocks[y_lb:y_ub, x_lb:x_ub] == AIR)):
            # Global position of the air block
            x_, y_ = x + x_lb, y + y_lb
            if (self.blocks[y_ - 1:y_ + 2, x_ - 1:x_ + 2] != AIR).any():
                # Bounds to iterate around the air block
                y_lb1, y_ub1 = max([y_ - radius, top, 0]), min([y_ + radius + 1, bot, self.dim[1]])
                x_lb1, x_ub1 = max([x_ - radius, left, 0]), min([x_ + radius + 1, right, self.dim[0]])
                for y1, x1 in zip(*np.where(self.blocks[y_lb1:y_ub1, x_lb1:x_ub1] != AIR)):
                    # Global position of this block
                    x1_, y1_ = x1 + x_lb1, y1 + y_lb1
                    light.blit(air_light, ((x1_ - left) * c.BLOCK_W, (y1_ - top) * c.BLOCK_W),
                               area=r.move((x1_ - x_ + radius) * c.BLOCK_W, (y1_ - y_ + radius) * c.BLOCK_W),
                               special_flags=BLEND_RGBA_SUB)
        for x in self.lights.keys():
            for y in self.lights[x].keys():
                light_s = game_vars.tiles[self.lights[x][y]].light_s
                r = light_s.get_rect(center=(int((x + .5) * c.BLOCK_W), int((y + .5) * c.BLOCK_W)))
                if rect.colliderect(r):
                    light.blit(light_s, (r.x - (left * c.BLOCK_W), r.y - (top * c.BLOCK_W)),
                               special_flags=BLEND_RGBA_SUB)
        pg.display.get_surface().blit(light, (0, 0), area=((off_x, off_y), rect.size))


class IdleWorld(World):
    def __init__(self, worldfile):
        super().__init__(worldfile)
        self.type = IDLE

    # Draws the entire world and map
    def draw_world(self, progress):
        if progress == 0:
            # Calculate pixel dimensions
            dim = (c.BLOCK_W * self.blocks.shape[1], c.BLOCK_W * self.blocks.shape[0])
            self.surface = pg.Surface(dim, SRCALPHA)
            self.map = pg.Surface(self.dim)
            self.map.fill(game_vars.tiles[AIR].map_color)
            self.light = pg.Surface(self.dim, SRCALPHA)
        map_arr = pg.surfarray.pixels2d(self.map)
        one_percent_h = math.ceil(self.dim[1] / 100)
        light_arr = pg.surfarray.pixels_alpha(self.light)
        # Load world
        y = int(progress * self.dim[1] + .5 / self.dim[1])
        for y in range(y, min(y + one_percent_h, self.dim[1])):
            # Loop through row
            for x, val in enumerate(self.blocks[y]):
                if val != AIR:
                    light_arr[x][y] = 255
                    if val >= 0:
                        self.surface.blit(game_vars.tiles[val].image, (x * c.BLOCK_W, y * c.BLOCK_W))
                        tile = game_vars.tiles[val]
                        color_int = self.map.map_rgb(tile.map_color)
                        map_arr[x:x + tile.dim[0], y:y + tile.dim[1]] = [[color_int] * tile.dim[1]] * tile.dim[
                            0]
        return (y + 1) / self.dim[1]

    def load_info(self, close_file):
        super().load_info(False)
        num_mages = int.from_bytes(self.f_obj.read(1), byteorder)
        spawn = [p * c.BLOCK_W for p in self.spawn]
        for i in range(num_mages):
            num_bytes = int.from_bytes(self.f_obj.read(1), byteorder)
            mage = load_mage(self.f_obj.read(num_bytes))
            game_vars.spawn_entity(mage, pos=mage.pos if mage.bound else spawn)

        if close_file:
            self.f_obj.close()

    # Save world
    def save_world(self, progress):
        if progress == 0:
            # Save world information, automatically opens the file
            self.save_info()
        progress = self.save_blocks(progress, 1)
        if progress == 1:
            self.f_obj.close()
        return progress

    # Save all mage entities
    def save_info(self):
        super().save_info()
        mages = [e for e in game_vars.handler.entities.values() if isinstance(e, Mage)]
        self.f_obj.write(len(mages).to_bytes(1, byteorder))
        for mage in mages:
            self.f_obj.write(mage.write())
