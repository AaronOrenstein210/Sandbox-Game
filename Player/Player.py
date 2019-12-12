# Created on 22 October 2019
# Defines methods and variables for the player

import pygame as pg
from pygame.locals import *
from math import copysign
from Tools.constants import BLOCK_W, resize
from Tools import constants as c
from Tools import objects as o
from Objects.tile_ids import AIR
from Player.PlayerInventory import PlayerInventory
from Player.Stats import Stats
from NPCs.Entity import check_collisions, touching_blocks_y
from NPCs.EntityHandler import EntityHandler
from GameDriver import GameDriver
from Objects.DroppedItem import DroppedItem


class Player:
    def __init__(self):
        # Drivers
        self.driver, self.handler = GameDriver(), EntityHandler()
        # Stats
        self.stats = Stats(hp=100, max_speed=[15, 20])
        # Inventory
        self.inventory = PlayerInventory()
        self.item_used, self.use_time = None, 0
        self.used_left = True
        self.first_swing = True
        # Sprite
        self.surface = pg.image.load("res/player/player_pig.png")
        dim = self.surface.get_size()
        self.dim = [1.5, 1.5 * dim[1] / dim[0]]
        # Hit box
        self.rect = Rect(0, 0, BLOCK_W * self.dim[0], BLOCK_W * self.dim[1])
        self.surface = pg.transform.scale(self.surface, self.rect.size)
        self.arm = pg.Surface((int(self.rect.w / 4), int(self.rect.h / 3)), SRCALPHA)
        pg.draw.rect(self.arm, (200, 128, 0), (0, 0, self.arm.get_size()[0], self.arm.get_size()[1]))
        # This determines the area in which items are collected
        self.collection_range = Rect(0, 0, 6 * BLOCK_W, 6 * BLOCK_W)
        self.collection_range.center = self.rect.center
        # This determines the area that you can place blocks
        self.placement_range = Rect(0, 0, 7 * BLOCK_W, 7 * BLOCK_W)
        self.placement_range.center = self.rect.center
        # Physics variables
        self.pos = [0, 0]
        self.v = [0., 0.]
        self.a = [0, 1]
        self.immunity = 0
        self.can_move = True
        # Stores an active ui
        self.active_ui = None
        # Position of block with ui
        self.active_block = [0, 0]

    def load(self, file):
        with open(file, "rb+") as data_file:
            data = data_file.read()
            self.inventory.load(data)

    def write(self, file):
        # See load() for info order
        with open(file, "wb+") as file:
            file.write(self.inventory.write())

    def run(self, events):
        mouse = list(pg.mouse.get_pressed())
        keys = list(pg.key.get_pressed())

        self.handler.spawn(self.rect.center)

        rect = self.driver.get_view_rect(self.rect.center)
        pos = pg.mouse.get_pos()
        global_pos = (pos[0] + rect.x, pos[1] + rect.y)

        if self.active_ui is not None:
            self.active_ui.process_events(events, mouse, keys)

        for e in events:
            if e.type == QUIT:
                return False
            elif e.type == VIDEORESIZE:
                resize(e.w, e.h)
                if self.active_ui is not None:
                    self.active_ui.on_resize()
            elif self.use_time <= 0 and e.type == MOUSEBUTTONUP and \
                    (e.button == BUTTON_WHEELUP or e.button == BUTTON_WHEELDOWN):
                self.inventory.scroll(e.button == BUTTON_WHEELUP)
            elif e.type == KEYUP or e.type == KEYDOWN:
                up = e.type == KEYUP
                # Try to jump
                if e.key == K_SPACE and self.can_move:
                    if up:
                        self.a[1] = 1
                    else:
                        if touching_blocks_y(self.pos, self.rect, False):
                            self.v[1] = -15
                elif self.use_time <= 0 or e.key in [K_ESCAPE]:
                    self.inventory.key_pressed(e.key, up)

        # Item not in use and not touching tile ui
        if self.use_time <= 0 and \
                (self.active_ui is None or not self.active_ui.rect.collidepoint(*pos)):
            # Mouse click events
            if mouse[BUTTON_LEFT - 1]:
                self.left_click(pos, global_pos)
            else:
                self.first_swing = True
                if mouse[BUTTON_RIGHT - 1]:
                    self.right_click(pos, global_pos)
                else:
                    self.inventory.holding_r = 0

        # Key pressed events
        if self.can_move:
            self.a[0] = 0 if not keys[K_a] ^ keys[K_d] else -1 if keys[K_a] \
                else 1

        # If we are using an item, let it handle the use time
        if self.item_used is not None:
            self.item_used.on_tick()
            # Check if we are done using the item
            if self.use_time <= 0:
                self.item_used = None
        # Otherwise decrement the use time
        elif self.use_time >= 0:
            self.use_time -= o.dt

        # Update player and all entities/items/projectiles
        if self.can_move:
            self.move()
        self.handler.move(self.rect.center)
        # Check if anything hit the player
        if self.immunity <= 0:
            dmg, entity_x = self.handler.check_hit_player(self.rect)
            if dmg > 0:
                self.hit(dmg, entity_x)

        # Redraw the screen
        self.draw_ui()
        return True

    def spawn(self):
        self.set_pos((o.world_spawn[0] * BLOCK_W, o.world_spawn[1] * BLOCK_W))

    def move(self):
        if o.dt == 0:
            return

        self.immunity -= o.dt

        dt = o.dt / 1000

        # Do movement
        d = [0., 0.]
        # For each direction
        for i in range(2):
            # Update the position and constrain it within our bounds
            d[i] = (BLOCK_W * 2 / 3) * (self.v[i] * dt)
            if self.a[i] == 0:
                if self.v[i] != 0:
                    self.v[i] += copysign(min(self.v[0] + (dt * 1), abs(self.v[i])), -self.v[i])
            else:
                self.v[i] += copysign(dt * 20, self.a[i])
                self.v[i] = copysign(min(abs(self.v[i]), self.stats.spd[i]), self.v[i])

        check_collisions(self.pos, self.dim, d)
        self.set_pos(self.pos)

        #if touching_blocks_y(self.pos, self.rect, True):
        #    self.v[1] = 1

    def set_pos(self, topleft):
        self.pos = list(topleft)
        self.rect.topleft = topleft
        self.placement_range.center = self.rect.center
        self.collection_range.center = self.rect.center

    def left_click(self, pos, global_pos):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.use_time = self.inventory.left_click(pos)
        else:
            idx = self.inventory.get_held_item()
            if idx != -1:
                item = o.items[idx]
                self.used_left = global_pos[0] < self.rect.centerx
                if self.first_swing or item.auto_use:
                    self.first_swing = False
                    # Use item
                    item.on_left_click()
                    self.item_used = item
                    self.use_time = item.use_time
                    # Check if the item places a block or breaks a block and then
                    # Check if that item can place or break the block
                    if (item.placeable and o.player.place_block(item.block_id)) or (
                            item.breaks_blocks and o.player.break_block()) and item.consumable:
                        self.inventory.use_item()
                    if item.has_ui:
                        self.active_ui = item.UI()

    def right_click(self, pos, global_pos):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.use_time = self.inventory.right_click(pos)
        else:
            block_x, block_y = global_pos[0] // BLOCK_W, global_pos[1] // BLOCK_W
            block = o.tiles[o.blocks[block_y][block_x]]
            # Make sure we didn't click the same block more than once
            if block.clickable and self.placement_range.collidepoint(*global_pos) and \
                    (self.active_ui is None or self.active_ui.block_pos != [block_x, block_y]):
                block.activate((block_x, block_y))
            else:
                # Check if we dropped an item
                drop = self.inventory.drop_item()
                if drop is not None:
                    item, amnt = drop
                    # This determines if we clicked to the left or right of the player
                    left = global_pos[0] < self.rect.centerx
                    self.drop_item(item, amnt, self.rect.center, left)

    def break_block(self):
        # Get mouse pos and viewing rectangle to calculate global mouse pos
        pos = pg.mouse.get_pos()
        rect = self.driver.get_view_rect(self.rect.center)
        pos = (pos[0] + rect.x, pos[1] + rect.y)
        # Calculate block rectangle
        block_x, block_y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        # Make sure this block does not have a ui open
        if self.active_ui is not None and self.active_ui.block_pos == [block_x, block_y]:
            return
        block_rect = Rect(block_x * BLOCK_W, block_y * BLOCK_W, BLOCK_W, BLOCK_W)
        # Check if we can break the block
        if self.placement_range.collidepoint(pos[0], pos[1]) and \
                o.tiles[o.blocks[block_y][block_x]].on_break((block_x, block_y)):
            block = self.driver.destroy_block(pos)
            if block != AIR:
                drops = o.tiles[block].get_drops()
                for drop in drops:
                    item, amnt = drop
                    # Drop an item
                    self.drop_item(item, amnt, block_rect.center, None)
                return True
        return False

    def place_block(self, idx):
        # Get mouse pos and viewing rectangle to calculate global mouse pos
        pos = pg.mouse.get_pos()
        rect = self.driver.get_view_rect(self.rect.center)
        pos = (pos[0] + rect.x, pos[1] + rect.y)
        # Calculate block rectangle
        block_x, block_y = int(pos[0] / BLOCK_W), int(pos[1] / BLOCK_W)
        block_rect = Rect(block_x * BLOCK_W, block_y * BLOCK_W, BLOCK_W, BLOCK_W)
        # Check if we can place the block
        if self.placement_range.collidepoint(pos[0], pos[1]):
            if not self.rect.colliderect(block_rect) and \
                    not self.handler.collides_with_entity(block_rect) and \
                    self.driver.place_block(pos, idx):
                o.tiles[o.blocks[block_y][block_x]].on_place((block_x, block_y))
                return True
        return False

    def drop_item(self, item, amnt, pos, left):
        dropped = DroppedItem(item, amnt)
        dropped.drop(pos, left)
        self.handler.items.append(dropped)

    def pick_up(self, item):
        if self.collection_range.colliderect(item.rect):
            space = self.inventory.room_for_item(item)
            if len(space) != 0:
                item.attract(self.rect.center)
                if abs(self.rect.centerx - item.rect.centerx) <= 1 and \
                        abs(self.rect.centery - item.rect.centery) <= 1:
                    return self.inventory.pick_up_item(item, space)
        else:
            item.pulled_in = False
        return False

    def draw_ui(self):
        rect = self.driver.get_view_rect(self.rect.center)
        display = pg.display.get_surface()
        display.fill(o.get_sky_color())
        # Draw blocks
        display.blit(self.driver.blocks_surface, (0, 0), area=rect)
        # Draw all entities/projectiles/items, in that order
        self.handler.get_display(rect)

        # Draw player and inventory
        display.blit(self.surface, (self.pos[0] - rect.x, self.pos[1] - rect.y))
        display.blit(self.inventory.surface, (0, 0), area=self.inventory.rect)

        # Draw item being used
        if self.item_used is not None:
            center = [self.rect.centerx - rect.x, self.rect.centery - rect.y]
            self.item_used.use_anim(self.use_time, self.arm, self.used_left, center, rect)

        # Draw block ui
        if self.active_ui is not None:
            display.blit(self.active_ui.ui, self.active_ui.rect)

        # Draw other UI
        life_text = str(self.stats.hp) + " / " + str(self.stats.max_hp) + " HP"
        # Draw stats
        text = c.ui_font.render(life_text, 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.right = rect.w
        display.blit(text, text_rect)

        # Draw selected item under cursor if there is one
        cursor = self.inventory.get_cursor_display()
        if cursor is not None:
            display.blit(cursor, pg.mouse.get_pos())

    def hit(self, dmg, centerx):
        self.stats.hp -= dmg
        if self.stats.hp <= 0:
            self.respawn()
        else:
            self.immunity = 1000
            self.v = [copysign(3, self.rect.centerx - centerx), -3]

    def attack(self, damage, polygon):
        # Change damage based on stats
        self.handler.check_hit_entities(self.rect.centerx, polygon, damage)

    def respawn(self):
        self.stats.hp = self.stats.max_hp
        self.immunity = 5000
        self.spawn()


def create_new_player(file_name):
    with open("saves/players/" + file_name + ".plr", "wb+") as file:
        file.write(PlayerInventory().new_inventory())
