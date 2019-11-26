# Created on 21 October 2019
# Handles the UI of the game

from pygame import Surface
from pygame.mouse import get_pos
from pygame.locals import *
from HelpfulTools import complete_task
from NPCs.EntityHandler import EntityHandler
from Player.Player import Player
from Databases.constants import BLOCK_W, AIR_ID
from Databases import constants as c
import World as w
from Databases.lists import items


class GameDriver:
    def __init__(self):
        # Calculate pixel dimensions
        self.dim = (BLOCK_W * w.blocks.shape[1], BLOCK_W * w.blocks.shape[0])
        self.blocks_surface = Surface(self.dim, SRCALPHA)
        # Handles all entities
        self.handler = EntityHandler()
        # Handles everything to do with the player
        self.player = Player()

    def run(self, events, dt):
        self.handler.spawn(self.player.rect.center)

        rect = self.get_view_rect()
        pos = get_pos()
        global_pos = (pos[0] + rect.x, pos[1] + rect.y)

        for e in events:
            if e.type == QUIT:
                return False
            elif e.type == VIDEORESIZE:
                c.resize(e.w, e.h)
            elif e.type == MOUSEBUTTONUP or e.type == MOUSEBUTTONDOWN:
                self.player.mouse_pressed(e.button, e.type == MOUSEBUTTONUP)
            elif e.type == KEYUP or e.type == KEYDOWN:
                self.player.key_pressed(e.key, e.type == KEYUP)

        # Check for player clicks
        if self.player.use_time <= 0:
            # Left click
            if self.player.left:
                block_rect = Rect((global_pos[0] // BLOCK_W) * BLOCK_W, (global_pos[1] // BLOCK_W) * BLOCK_W,
                                  BLOCK_W, BLOCK_W)
                # Get the block to place
                block = self.player.left_click(pos, global_pos)
                if block == AIR_ID:
                    broken = self.destroy_block(global_pos)
                    if broken is not None:
                        dropped = items[broken].clone(1)
                        dropped.drop(block_rect.center, None)
                        self.handler.items.append(dropped)
                elif block is not None:
                    # Check if we can place the block
                    if not self.handler.collides_with_entity(block_rect) and self.place_block(global_pos, block):
                        self.player.use_item()
            # Right click
            elif self.player.right:
                # Get items to drop
                drop = self.player.right_click(pos, global_pos, dt)
                if drop is not None:
                    self.handler.items.append(drop)

        # Update player and all entities/items/projectiles
        self.player.move(dt)
        self.handler.move(dt, self.player.rect.center, self.player.pick_up)
        if self.player.immunity <= 0:
            # Check if anything hit the player
            dmg, entity_x = self.handler.check_hit_player(self.player.rect)
            if dmg > 0:
                self.player.hit(dmg, entity_x)
        # Check if the player hit anything
        if self.player.item_used is not None and self.player.item_used.polygon is not None:
            self.handler.check_hit_entities(self.player.rect.centerx, self.player.item_used)
        # Redraw the screen
        self.update_screen()
        return True

    def destroy_block(self, pos):
        # Get block coords and break the block if it is not air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if w.blocks[y][x] != AIR_ID:
            old = w.blocks[y][x]
            w.blocks[y][x] = AIR_ID
            block_rect = Rect(int(pos[0] / BLOCK_W) * BLOCK_W, int(pos[1] / BLOCK_W) * BLOCK_W,
                              BLOCK_W, BLOCK_W)
            self.blocks_surface.fill(SRCALPHA, block_rect)
            if items[old].spawner:
                w.remove_spawner(x, y)
            return old

    def place_block(self, pos, block):
        # Get block coords and place the block if it is currently air
        x, y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        if w.blocks[y][x] == AIR_ID and len(self.get_adjacent(x, y)) > 0:
            w.blocks[y][x] = block
            self.blocks_surface.blit(items[block].image, (x * BLOCK_W, y * BLOCK_W))
            if items[block].spawner:
                w.add_spawner(x, y, block)
            return True
        return False

    def get_adjacent(self, x, y):
        # Get adjacent w.blocks
        adj_blocks = []
        for x1, y1 in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 < x1 < w.blocks.shape[1] and 0 < y1 < w.blocks.shape[0] and \
                    w.blocks[y1][x1] != AIR_ID:
                adj_blocks.append(w.blocks[y1][x1])
        return adj_blocks

    def get_view_rect(self):
        dim = c.display.get_size()
        rect = Rect(0, 0, dim[0], dim[1])
        rect.center = self.player.rect.center
        rect.x = max(min(rect.x, self.dim[0] - dim[0]), 0)
        rect.y = max(min(rect.y, self.dim[1] - dim[1]), 0)
        return rect

    def draw_blocks(self):
        def draw_row(progress, surface):
            y = int(progress * w.blocks.shape[0])
            for x, val in enumerate(w.blocks[y]):
                if val != AIR_ID:
                    surface.blit(items[val].image, (x * BLOCK_W, y * BLOCK_W))
            return (y + 1) / w.blocks.shape[0]

        self.blocks_surface.fill(SRCALPHA)
        complete_task(draw_row, args=[self.blocks_surface], msg="Drawing World")

    def update_screen(self):
        c.display.fill(w.get_day_color())
        rect = self.get_view_rect()
        # Draw w.blocks
        c.display.blit(self.blocks_surface, (-rect.x, -rect.y))
        # Draw all entities/projectiles/items, in that order
        self.handler.get_display(rect)
        # Draw Player UI
        self.player.draw_ui(rect)
