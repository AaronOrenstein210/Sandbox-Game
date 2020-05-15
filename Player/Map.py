# Created on 23 February 2020
# Defines the map class for drawing and zooming a map

import math
import pygame as pg
from Tools import game_vars


class Map:
    def __init__(self, source):
        # Source surface
        self.source = source
        # Map zoom
        self.zoom = 1
        # Pixel position from the source surface of the map center
        self.center = [0, 0]

    def set_center(self, pos):
        self.center = list(pos)

    def draw_map(self, rect):
        src_dim = self.source.get_size()
        dim = rect.size

        dim = [min(dim[i], src_dim[i] * self.zoom) for i in (0, 1)]
        # Get map width in terms of blocks
        block_dim = (dim[0] / self.zoom, dim[1] / self.zoom)
        half_dim = (block_dim[0] / 2, block_dim[1] / 2)
        # Calculate top and left of our minimap
        for i in range(2):
            if self.center[i] < half_dim[i]:
                self.center[i] = half_dim[i]
            elif self.center[i] > src_dim[i] - half_dim[i]:
                self.center[i] = src_dim[i] - half_dim[i]
        left, top = self.center[0] - half_dim[0], self.center[1] - half_dim[1]
        # Get the blocks that will be in our map
        b_left, b_top = int(left), int(top)
        b_right, b_bot = math.ceil(left + block_dim[0]), math.ceil(top + block_dim[1])
        b_dim = (b_right - b_left, b_bot - b_top)
        # Draw them onto a surface
        s = pg.Surface(b_dim)
        s.blit(self.source, (0, 0), area=((b_left, b_top), b_dim))
        s = pg.transform.scale(s, (int(b_dim[0] * self.zoom), int(b_dim[1] * self.zoom)))
        # Cut off the edges
        off_x, off_y = int((left - b_left) * self.zoom), int((top - b_top) * self.zoom)
        map_rect = pg.Rect((b_left, b_top), b_dim)
        self.draw_sprite(s, map_rect, game_vars.player.sprite, game_vars.player_pos(in_blocks=True))
        for entity in [e for e in game_vars.handler.entities.values() if e.sprite]:
            self.draw_sprite(s, map_rect, entity.sprite, entity.get_block_pos())
        pg.display.get_surface().blit(s, (rect.centerx - dim[0] // 2, rect.centery - dim[1] // 2),
                                      area=((off_x, off_y), dim))

    def draw_sprite(self, surface, map_rect, sprite, pos):
        if map_rect.collidepoint(*pos):
            pos[0] = int((pos[0] - map_rect.x) * self.zoom)
            pos[1] = int((pos[1] - map_rect.y) * self.zoom)
            sprite_rect = sprite.get_rect(center=pos)
            surface.blit(sprite, sprite_rect)
