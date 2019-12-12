# Created on 21 October 2019
# Handles the UI of the game

from pygame import Surface
from pygame.display import get_surface
from pygame.locals import *
from Tools.constants import BLOCK_W, update_dict, remove_from_dict
from Objects.tile_ids import AIR
from UI.Operations import CompleteTask
from Tools import objects as o


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
        self.dim = (BLOCK_W * o.blocks.shape[1], BLOCK_W * o.blocks.shape[0])
        self.blocks_surface = Surface(self.dim, SRCALPHA)

        def draw_row(progress, surface):
            y = int(progress * o.blocks.shape[0])
            for x, val in enumerate(o.blocks[y]):
                if val != AIR:
                    surface.blit(o.tiles[val].image, (x * BLOCK_W, y * BLOCK_W))
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
            if o.tiles[block].spawner:
                update_dict(x, y, block, o.spawners)
            return True
        return False


def get_adjacent(x, y):
    # Get adjacent o.blocks
    adj_blocks = []
    for x1, y1 in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 < x1 < o.blocks.shape[1] and 0 < y1 < o.blocks.shape[0] and \
                o.blocks[y1][x1] != AIR:
            adj_blocks.append(o.blocks[y1][x1])
    return adj_blocks
