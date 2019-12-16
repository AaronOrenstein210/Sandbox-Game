# Created on 21 October 2019
# Handles the UI of the game

import math
import pygame as pg
from pygame.locals import *
from Tools.constants import BLOCK_W, update_dict, remove_from_dict, MAP_W
from Objects.tile_ids import AIR
from UI.Operations import CompleteTask
from Tools import objects as o


class GameDriver:
    def __init__(self):
        # Calculate pixel dimensions
        self.dim = (0, 0)
        self.blocks_surface = None
        # Map and Minimap
        self.map = None
        self.minimap_zoom = 2
        self.map_zoom = 1
        self.map_off = [0, 0]

    def get_view_rect(self, player_pos):
        dim = pg.display.get_surface().get_size()
        rect = Rect(0, 0, dim[0], dim[1])
        rect.center = player_pos
        rect.x = max(min(rect.x, self.dim[0] - dim[0]), 0)
        rect.y = max(min(rect.y, self.dim[1] - dim[1]), 0)
        return rect

    def draw_blocks(self):
        # Calculate pixel dimensions
        self.dim = (BLOCK_W * o.blocks.shape[1], BLOCK_W * o.blocks.shape[0])
        self.blocks_surface = pg.Surface(self.dim, SRCALPHA)
        self.map = pg.Surface((o.blocks.shape[1], o.blocks.shape[0]))
        self.map.fill((64, 64, 255))

        def draw_row(progress, surface):
            y = int(progress * o.blocks.shape[0])
            for x, val in enumerate(o.blocks[y]):
                if val != AIR:
                    surface.blit(o.tiles[val].image, (x * BLOCK_W, y * BLOCK_W))
                    self.map.set_at((x, y), o.tiles[val].map_color)
            return (y + 1) / o.blocks.shape[0]

        self.blocks_surface.fill(SRCALPHA)
        CompleteTask(draw_row, task_args=[self.blocks_surface], draw_args=("Drawing World",)).run_now()

    def destroy_block(self, pos):
        # Get block coords and break the block if it is not air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if o.blocks[y][x] != AIR:
            old = o.blocks[y][x]
            o.blocks[y][x] = AIR
            block_rect = Rect(int(pos[0] / BLOCK_W) * BLOCK_W, int(pos[1] / BLOCK_W) * BLOCK_W,
                              BLOCK_W, BLOCK_W)
            self.blocks_surface.fill(SRCALPHA, block_rect)
            self.map.set_at((x, y), (64, 64, 255))
            if o.tiles[old].spawner:
                remove_from_dict(x, y, o.spawners)
            return old
        return AIR

    def place_block(self, pos, block):
        # Get block coords and place the block if it is currently air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if o.blocks[y][x] == AIR and len(get_adjacent(x, y)) > 0:
            o.blocks[y][x] = block
            self.blocks_surface.blit(o.tiles[block].image, (x * BLOCK_W, y * BLOCK_W))
            self.map.set_at((x, y), o.tiles[block].map_color)
            if o.tiles[block].spawner:
                update_dict(x, y, block, o.spawners)
            return True
        return False

    def get_map(self, dim):
        # Get world dim
        world_dim = list(o.blocks.shape)
        world_dim.reverse()
        dim = [min(dim[i], world_dim[i] * self.map_zoom) for i in (0, 1)]
        # Get map width in terms of blocks
        block_dim = (dim[0] / self.map_zoom, dim[1] / self.map_zoom)
        half_dim = (block_dim[0] / 2, block_dim[1] / 2)
        # Calculate top and left of our minimap
        for i in range(2):
            if self.map_off[i] < half_dim[i]:
                self.map_off[i] = half_dim[i]
            elif self.map_off[i] > world_dim[i] - half_dim[i]:
                self.map_off[i] = world_dim[i] - half_dim[i]
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
        # Get world dim
        world_dim = list(o.blocks.shape)
        world_dim.reverse()
        # Get map width in terms of blocks
        block_w = MAP_W / self.minimap_zoom
        half_w = block_w / 2
        # Calculate top and left of our minimap
        left, top = [min(max(center[i] - half_w, 0), world_dim[i] - block_w) for i in (0, 1)]
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
            self.map_off[0] -= 1
        elif keys[K_d]:
            self.map_off[0] += 1
        elif keys[K_w]:
            self.map_off[1] -= 1
        elif keys[K_s]:
            self.map_off[1] += 1


def get_adjacent(x, y):
    # Get adjacent o.blocks
    adj_blocks = []
    for x1, y1 in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 < x1 < o.blocks.shape[1] and 0 < y1 < o.blocks.shape[0] and \
                o.blocks[y1][x1] != AIR:
            adj_blocks.append(o.blocks[y1][x1])
    return adj_blocks
