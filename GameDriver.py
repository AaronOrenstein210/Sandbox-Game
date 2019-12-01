# Created on 21 October 2019
# Handles the UI of the game

from pygame import Surface
from pygame.display import get_surface
from pygame.locals import *
from Tools.constants import BLOCK_W, AIR_ID
import World as W
from Tools.lists import items
from Tools.UIOperations import complete_task


class GameDriver:
    def __init__(self):
        # Calculate pixel dimensions
        self.dim = (0, 0)
        self.blocks_surface = None

    def get_view_rect(self, player_pos):
        dim = get_surface().get_size()
        rect = Rect(0, 0, dim[0], dim[1])
        rect.center = player_pos
        rect.x = max(min(rect.x, self.dim[0] - dim[0]), 0)
        rect.y = max(min(rect.y, self.dim[1] - dim[1]), 0)
        return rect

    def draw_blocks(self):
        # Calculate pixel dimensions
        self.dim = (BLOCK_W * W.blocks.shape[1], BLOCK_W * W.blocks.shape[0])
        self.blocks_surface = Surface(self.dim, SRCALPHA)

        def draw_row(progress, surface):
            y = int(progress * W.blocks.shape[0])
            for x, val in enumerate(W.blocks[y]):
                if val != AIR_ID:
                    surface.blit(items[val].image, (x * BLOCK_W, y * BLOCK_W))
            return (y + 1) / W.blocks.shape[0]

        self.blocks_surface.fill(SRCALPHA)
        complete_task(draw_row, task_args=[self.blocks_surface], message="Drawing World")

    def destroy_block(self, pos):
        # Get block coords and break the block if it is not air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if W.blocks[y][x] != AIR_ID:
            old = W.blocks[y][x]
            W.blocks[y][x] = AIR_ID
            block_rect = Rect(int(pos[0] / BLOCK_W) * BLOCK_W, int(pos[1] / BLOCK_W) * BLOCK_W,
                              BLOCK_W, BLOCK_W)
            self.blocks_surface.fill(SRCALPHA, block_rect)
            if items[old].spawner:
                W.remove_spawner(x, y)
            return old
        return AIR_ID

    def place_block(self, pos, block):
        # Get block coords and place the block if it is currently air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if W.blocks[y][x] == AIR_ID and len(get_adjacent(x, y)) > 0:
            W.blocks[y][x] = block
            self.blocks_surface.blit(items[block].image, (x * BLOCK_W, y * BLOCK_W))
            if items[block].spawner:
                W.add_spawner(x, y, block)
            return True
        return False


def get_adjacent(x, y):
    # Get adjacent W.blocks
    adj_blocks = []
    for x1, y1 in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 < x1 < W.blocks.shape[1] and 0 < y1 < W.blocks.shape[0] and \
                W.blocks[y1][x1] != AIR_ID:
            adj_blocks.append(W.blocks[y1][x1])
    return adj_blocks
