# Created on 21 December 2019

from sys import byteorder
from numpy import full, int16
import math
import pygame as pg
from pygame.locals import *
from Tools.tile_ids import AIR
from Tools import constants as c
from Tools import game_vars
from UI.Operations import CompleteTask, percent


class World:
    def __init__(self, universe, name):
        # Visual variables
        self.surface = None
        self.map = None
        # World data
        self.dim = [0, 0]
        self.num_blocks = 0
        self.blocks = None
        self.spawn = [0, 0]
        self.world_time = c.MS_PER_DAY * .4
        # Special blocks, whose positions need to be stored
        self.spawners = {}
        self.animations = {}
        self.block_data = {}
        self.crafters = {}
        # File variables
        self.universe = universe
        self.name = name
        self.f_obj = open(self.file, 'r')
        self.f_obj.close()

    @property
    def surface_h(self):
        return self.dim[1] // 2

    @property
    def underground(self):
        return self.dim[1] * 2 // 3

    @property
    def file(self):
        return "saves/universes/" + self.universe + "/" + self.name + ".wld"

    @property
    def sky_color(self):
        return 0, 0, 255 * (1 - pow((self.world_time - c.NOON) / c.NOON, 2))

    def tick(self):
        self.world_time = (self.world_time + game_vars.dt) % c.MS_PER_DAY

    def new_world(self, dim):
        self.dim = dim
        self.num_blocks = dim[0] * dim[1]
        self.blocks = full((dim[1], dim[0]), AIR, dtype=int16)

    # Load world
    def load_part(self, progress):
        # If we are just opening the file, get world info
        if self.f_obj.closed or not self.f_obj.readable():
            self.f_obj.close()
            self.f_obj = open(self.file, 'rb+')
            # Reset world data
            self.spawners.clear()
            self.block_data.clear()
            self.animations.clear()
            # Load world info
            self.dim = [int.from_bytes(self.f_obj.read(2), byteorder) for i in range(2)]
            self.num_blocks = self.dim[0] * self.dim[1]
            self.spawn = [int.from_bytes(self.f_obj.read(2), byteorder) for i in range(2)]
            self.blocks = full((self.dim[1], self.dim[0]), AIR, dtype=int16)
        # Get current row and column and the blocks left to load
        current_block = int(progress * self.num_blocks)
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
                # Otherwise, it is either a single block, or a vertical multiblock
                else:
                    # Save single block
                    self.blocks[row][col:col + num] = [val] * num
                    # Save vertical multiblock
                    for i in range(1, tile.dim[1]):
                        self.blocks[row + i][col + num] = [-i] * num
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
        return (row * self.dim[0] + col) / self.num_blocks

    # Save world
    def save_part(self, progress, num_rows):
        # If there is no data, just end the process
        if self.blocks is None:
            return 1
        # If we are just opening the file, save world info
        if self.f_obj.closed or not self.f_obj.writable():
            self.f_obj.close()
            self.f_obj = open(self.file, 'wb+')
            self.f_obj.write(self.dim[0].to_bytes(2, byteorder))
            self.f_obj.write(self.dim[1].to_bytes(2, byteorder))
            self.f_obj.write(self.spawn[0].to_bytes(2, byteorder))
            self.f_obj.write(self.spawn[1].to_bytes(2, byteorder))
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

    # Update block
    def place_block(self, x, y, block):
        tile = game_vars.tiles[block]
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[-(x * 100 + y) for x in range(w)] for y in range(h)]
        self.blocks[y][x] = block
        self.surface.blit(game_vars.tiles[block].image, (x * c.BLOCK_W, y * c.BLOCK_W))
        pg.draw.rect(self.map, tile.map_color, (x, y, *tile.dim))
        # Update data
        self.add_block(x, y, block)

    def destroy_block(self, x, y):
        x, y = game_vars.get_topleft(x, y)
        tile = game_vars.tiles[self.blocks[y][x]]
        # Destroy all parts
        w, h = tile.dim
        self.blocks[y:y + h, x:x + w] = [[AIR] * w] * h
        # Redraw block
        block_rect = Rect(x * c.BLOCK_W, y * c.BLOCK_W, c.BLOCK_W * w, c.BLOCK_W * h)
        self.surface.fill(SRCALPHA, block_rect)
        pg.draw.rect(self.map, (64, 64, 255), (x, y, *tile.dim))
        # Update data
        self.remove_block(x, y, tile.idx)

    # Update dictionaries
    def add_block(self, x, y, idx):
        tile = game_vars.tiles[idx]
        if tile.spawner:
            c.update_dict(x, y, idx, self.spawners)
        if tile.crafting:
            c.update_dict(x, y, idx, self.crafters)
        if tile.anim_idx != -1:
            c.update_dict(x, y, tile.anim_idx, self.animations)

    def remove_block(self, x, y, idx):
        tile = game_vars.tiles[idx]
        if tile.spawner:
            c.remove_from_dict(x, y, self.spawners)
        if tile.crafting:
            c.remove_from_dict(x, y, self.crafters)
        if tile.anim_idx != -1:
            c.remove_from_dict(x, y, self.animations)

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

    # Draws blocks
    def draw_blocks(self, rect):
        # Update every animation
        for a in game_vars.animations:
            a.update()
        from Tools.constants import BLOCK_W
        xmin, xmax = rect.left // BLOCK_W, rect.right // BLOCK_W
        ymin, ymax = rect.top // BLOCK_W, rect.bottom // BLOCK_W
        # Multiblocks whose topleft is off screen won't update
        # Go through all x/y and check if x+w is on screen (same for y)
        for x in self.animations.keys():
            if xmin <= x <= xmax:
                for y in self.animations[x].keys():
                    if ymin <= y <= ymax:
                        anim = game_vars.animations[self.animations[x][y]]
                        img = anim.get_frame()
                        img_rect = img.get_rect(topleft=(x * BLOCK_W, y * BLOCK_W))
                        pg.draw.rect(self.surface, SRCALPHA, img_rect)
                        self.surface.blit(anim.get_frame(), img_rect)

        # Draw sky and blocks
        d = pg.display.get_surface()
        d.blit(self.surface, (0, 0), area=rect)

    # TODO: Chunks
    # Draws the entire world
    def draw_world(self):
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
                        self.surface.blit(game_vars.tiles[val].image, (x * c.BLOCK_W, y * c.BLOCK_W))
                        tile = game_vars.tiles[val]
                        pg.draw.rect(self.map, tile.map_color, (x, y, *tile.dim))
            return (y + 1) / self.dim[1]

        self.surface.fill(SRCALPHA)
        if not CompleteTask(draw_row, [], percent, ["Drawing World"]).run_now():
            pg.quit()
            exit(0)
