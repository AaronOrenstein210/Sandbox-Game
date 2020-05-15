# Created on 12 May 2020
# Defines classes for chunks

import pygame as pg
from pygame.locals import SRCALPHA
from Tools import game_vars
from Tools.constants import BLOCK_W

CHUNK_W = 50
CHUNK_W_PX = CHUNK_W * BLOCK_W


class Chunk:
    def __init__(self, left, top, blocks=None):
        self.x, self.y = left, top
        self.surface = None
        # Special blocks whose positions need to be stored
        # Stored as (x,y):tile_id pairs
        self.updates = {}
        self.img_updates = {}
        self.lights = {}

        if blocks is not None:
            self.load(blocks)

    # TODO: Do a tick based on last recorded time
    def load(self, blocks):
        self.surface = pg.Surface((CHUNK_W_PX, CHUNK_W_PX), SRCALPHA)
        for y in range(self.y, min(self.y + CHUNK_W, blocks.shape[0])):
            for x in range(self.x, min(self.x + CHUNK_W, blocks.shape[1])):
                val = blocks[y][x]
                # negative ID signifies a multiblock
                if val < 0:
                    # Find topleft of multiblock using global coords
                    x_, y_ = game_vars.get_topleft(x, y)
                    val = blocks[y_][x_]
                    # Make x and y relative to the chunk's topleft corner
                    x_ -= self.x
                    y_ -= self.y
                else:
                    # Make x and y relative to the chunk's topleft corner
                    x_ = x - self.x
                    y_ = y - self.y
                if val > 0:
                    tile = game_vars.tiles[val]
                    # TODO: Air light
                    self.surface.blit(tile.image, (x_ * BLOCK_W, y_ * BLOCK_W))
                    if tile.updates:
                        self.updates[(x_, y_)] = val
                    if tile.img_updates:
                        self.img_updates[(x_, y_)] = val
                    if tile.emits_light:
                        self.lights[(x_, y_)] = val
        # TODO: Block light
        pg.draw.rect(self.surface, (0, 0, 0), (0, 0, CHUNK_W_PX, CHUNK_W_PX), 2)

    def unload(self):
        del self.surface
        self.updates.clear()
        self.img_updates.clear()
        self.lights.clear()

    # Called when a block in the chunk is changed
    def block_change(self, x, y, tile_id, place):
        coords = (x - self.x, y - self.y)
        tile = game_vars.tiles[tile_id]
        if tile.updates:
            if place:
                self.updates[coords] = tile_id
            else:
                self.updates.pop(coords)
        if tile.img_updates:
            if place:
                self.img_updates[coords] = tile_id
            else:
                self.img_updates.pop(coords)
        if tile.emits_light:
            if place:
                self.lights[coords] = tile_id
            else:
                self.lights.pop(coords)

        rect = pg.Rect(coords[0] * BLOCK_W, coords[1] * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
        pg.draw.rect(self.surface, SRCALPHA, rect)
        if place:
            self.surface.blit(tile.image, rect)

    def tick(self, dt):
        from Tools.constants import BLOCK_W
        # Go through all img_updates and redraw
        for (x, y), tile_id in self.img_updates.items():
            img = game_vars.tiles[tile_id].get_block_img((self.x + x, self.y + y))
            img_rect = img.get_rect(topleft=(x * BLOCK_W, y * BLOCK_W))
            pg.draw.rect(self.surface, SRCALPHA, img_rect)
            self.surface.blit(img, img_rect)

        # Do block ticks
        for (x, y), tile_id in self.updates.items():
            game_vars.tiles[tile_id].tick(x + self.x, y + self.y, dt)


# TODO: When leaving world, load all chunks to update them one more time
class ChunkManager:
    def __init__(self, world):
        self.world = world
        self.chunks = []

    def get_rect(self):
        return pg.Rect(self.chunks[0][0].x, self.chunks[0][0].y, CHUNK_W * len(self.chunks[0]),
                       CHUNK_W * len(self.chunks))

    def setup(self):
        pos = self.world.spawn
        left = int(max(0, pos[0] - CHUNK_W * 3 // 2) / CHUNK_W)
        right = int(min(self.world.dim[0] - 1, pos[0] + CHUNK_W * 3 // 2) / CHUNK_W)
        top = int(max(0, pos[1] - CHUNK_W * 3 // 2) / CHUNK_W)
        bot = int(min(self.world.dim[1] - 1, pos[1] + CHUNK_W * 3 // 2) / CHUNK_W)
        self.chunks = [[Chunk(x * CHUNK_W, y * CHUNK_W) for x in range(left, right + 1)] for y in range(top, bot + 1)]

    def load_all(self):
        for row in self.chunks:
            for chunk in row:
                chunk.unload()
                chunk.load(self.world.blocks)

    def block_change(self, x, y, tile_id, place):
        rect = self.get_rect()
        tile = game_vars.tiles[tile_id]
        tile_rect = pg.Rect(x, y, tile.dim[0] - 1, tile.dim[1] - 1)
        if rect.colliderect(tile_rect):
            left, top = int((tile_rect.x - rect.x) / CHUNK_W), int((tile_rect.y - rect.y) / CHUNK_W)
            right, bot = int((tile_rect.right - rect.x) / CHUNK_W), int((tile_rect.bottom - rect.y) / CHUNK_W)
            for y_ in range(top, bot + 1):
                for x_ in range(left, right + 1):
                    self.chunks[y_][x_].block_change(x, y, tile_id, place)

    def tick(self, dt):
        # Check chunk loading/unloading
        pos = game_vars.player_pos(in_blocks=True)
        rect = self.get_rect()
        dx = [pos[0] - rect.x, rect.right - pos[0]]
        dy = [pos[1] - rect.top, rect.bottom - pos[1]]
        for i in range(2):
            # X chunks
            if dx[i] >= CHUNK_W * 3:
                for row in self.chunks:
                    row[-i].unload()
                    del row[-i]
            elif dx[i] <= CHUNK_W * 3 // 2 and (
                    rect.x >= CHUNK_W if i == 0 else rect.right <= self.world.dim[0] - CHUNK_W):
                x = self.chunks[0][-i].x + (-CHUNK_W if i == 0 else CHUNK_W)
                for row in self.chunks:
                    new = Chunk(x, row[0].y, blocks=self.world.blocks)
                    if i == 0:
                        row.insert(0, new)
                    else:
                        row.append(new)

            # Y chunks
            if dy[i] >= CHUNK_W * 3:
                for chunk in self.chunks[-i]:
                    chunk.unload()
                del self.chunks[-i]
            elif dy[i] <= CHUNK_W * 3 // 2 and (
                    rect.y >= CHUNK_W if i == 0 else rect.bottom <= self.world.dim[1] - CHUNK_W):
                y = self.chunks[0][-i].y + (-CHUNK_W if i == 0 else CHUNK_W)
                new_row = [Chunk(c.x, y, blocks=self.world.blocks) for c in self.chunks[0]]
                if i == 0:
                    self.chunks.insert(0, new_row)
                else:
                    self.chunks.append(new_row)

        # Update chunks
        for row in self.chunks:
            for chunk in row:
                chunk.tick(dt)

    def draw(self, rect):
        chunk_rect = self.get_rect()
        chunk_rect = pg.Rect(chunk_rect.x * BLOCK_W, chunk_rect.y * BLOCK_W, chunk_rect.w * BLOCK_W,
                             chunk_rect.h * BLOCK_W)
        # In chunks
        left = max(0, int((rect.x - chunk_rect.x) / CHUNK_W_PX))
        right = min(len(self.chunks[0]) - 1, int((rect.right - chunk_rect.x) / CHUNK_W_PX))
        top = max(0, int((rect.top - chunk_rect.y) / CHUNK_W_PX))
        bot = min(len(self.chunks) - 1, int((rect.bottom - chunk_rect.y) / CHUNK_W_PX))
        d = pg.display.get_surface()
        screen_x = 0
        for i, x in enumerate(range(left, right + 1)):
            chunk_x = x * CHUNK_W_PX + chunk_rect.x
            off_x = max(0, rect.x - chunk_x)
            w = min(CHUNK_W_PX, rect.right - chunk_x) - off_x
            screen_y = 0
            for j, y in enumerate(range(top, bot + 1)):
                chunk_y = y * CHUNK_W_PX + chunk_rect.y
                off_y = max(0, rect.y - chunk_y)
                h = min(CHUNK_W_PX, rect.bottom - chunk_y) - off_y
                d.blit(self.chunks[y][x].surface, (screen_x, screen_y),
                       area=pg.Rect(off_x, off_y, w, h))
                screen_y += h
            screen_x += w

    def print(self):
        print("Chunks:")
        for row in self.chunks:
            for chunk in row:
                print("({}, {})".format(chunk.x, chunk.y), end=" ")
            print()
