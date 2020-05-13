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
        self.blocks = self.surface = None
        # Special blocks whose positions need to be stored
        self.updates = []
        self.animations = []
        self.lights = []

        if blocks is not None:
            self.load(blocks)

    def load(self, blocks):
        self.blocks = blocks[self.y:self.y + CHUNK_W, self.x:self.x + CHUNK_W]
        self.surface = pg.Surface((CHUNK_W * BLOCK_W, CHUNK_W * BLOCK_W))
        for y, row in enumerate(self.blocks):
            for x, val in enumerate(row):
                if val > 0:
                    tile = game_vars.tiles[val]
                    # TODO: Air light
                    self.surface.blit(tile.image, (x * BLOCK_W, y * BLOCK_W))
                    if tile.updates:
                        self.updates.append((x, y))
                    if tile.anim_idx != -1:
                        self.animations.append((x, y))
                    if tile.emits_light:
                        self.lights.append((x, y))
                # TODO: multiblock updates
        # TODO: Block light

    def unload(self):
        del self.blocks, self.surface
        self.updates.clear()
        self.animations.clear()
        self.lights.clear()

    # Called when a block in the chunk is changed
    def block_change(self, x, y):
        coords = (x - self.x, y - self.y)
        tile = game_vars.tiles[game_vars.get_block_at(x, y)]
        if coords in self.updates and not tile.updates:
            self.updates.remove(coords)
        elif tile.updates:
            self.updates.append(coords)
        if coords in self.animations and tile.anim_idx == -1:
            self.animations.remove(coords)
        elif tile.anim_idx != -1:
            self.animations.append(coords)
        if coords in self.lights and not tile.emits_light:
            self.lights.remove(coords)
        elif tile.emits_light:
            self.lights.append(coords)
        rect = pg.Rect(coords[0] * BLOCK_W, coords[1] * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
        self.surface.fill(SRCALPHA, rect)
        self.surface.blit(tile.image, rect)

    def tick(self, dt):
        from Tools.constants import BLOCK_W
        # TODO: Multiblocks whose topleft is off screen won't update
        # Go through all x/y and check if x+w is on screen (same for y)
        for (x, y) in self.animations:
            img = game_vars.tiles[self.blocks[y][x]].get_block_img(game_vars.get_block_data((self.x + x, self.y + y)))
            img_rect = img.get_rect(topleft=(x * BLOCK_W, y * BLOCK_W))
            pg.draw.rect(self.surface, SRCALPHA, img_rect)
            self.surface.blit(img, img_rect)

        # Do block ticks
        for (x, y) in self.updates:
            game_vars.tiles[self.blocks[y][x]].tick(x + self.x, y + self.y, dt, game_vars.get_block_data((x, y)))


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
        right = int(min(self.world.dim[0], pos[0] + CHUNK_W * 3 // 2) / CHUNK_W)
        top = int(max(0, pos[1] - CHUNK_W * 3 // 2) / CHUNK_W)
        bot = int(min(self.world.dim[1], pos[1] + CHUNK_W * 3 // 2) / CHUNK_W)
        self.chunks = [[Chunk(x * CHUNK_W, y * CHUNK_W) for x in range(left, right + 1)] for y in range(top, bot + 1)]
        self.print()

    def load_all(self):
        for row in self.chunks:
            for chunk in row:
                chunk.unload()
                chunk.load(self.world.blocks)

    def block_change(self, x, y):
        rect = self.get_rect()
        if rect.left <= x < rect.right and rect.top <= y < rect.bottom:
            x_, y_ = int((x - rect.x) / CHUNK_W), int((y - rect.y) / CHUNK_W)
            self.chunks[y_][x_].block_change(x, y)

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
            elif dx[i] <= CHUNK_W * 3 // 2 and (rect.x >= 0 if i == 0 else rect.right <= self.world.dim[0] - CHUNK_W):
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
            elif dy[i] <= CHUNK_W * 3 // 2 and (rect.y >= 0 if i == 0 else rect.bottom <= self.world.dim[1] - CHUNK_W):
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
        right = min(len(self.chunks[0]), int((rect.right - chunk_rect.x) / CHUNK_W_PX))
        top = max(0, int((rect.top - chunk_rect.y) / CHUNK_W_PX))
        bot = min(len(self.chunks), int((rect.bottom - chunk_rect.y) / CHUNK_W_PX))
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
        print()
        for row in self.chunks:
            for chunk in row:
                print("({}, {})".format(chunk.x, chunk.y), end=" ")
            print()
