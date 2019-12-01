# Created on 22 October 2019
# Defines methods and variables for the player

from sys import byteorder
import pygame as pg
from pygame.locals import *
from math import copysign
from Tools.constants import *
from Tools import constants as c
import World as W
from Player.Inventory import Inventory
from Objects.Tool import Tool
from NPCs.Entity import check_collisions, touching_blocks_y
from Player.Stats import Stats
from Tools.lists import items
from NPCs.EntityHandler import EntityHandler
from GameDriver import GameDriver

DIM = (1.5, 3)


class Player:
    def __init__(self):
        # Drivers
        self.driver, self.handler = GameDriver(), EntityHandler()
        # Stats
        self.stats = Stats(hp=100, max_speed=[15, 15])
        # Inventory
        self.inventory = Inventory()
        self.item_used, self.use_time = None, 0
        self.used_left = True
        # Hit box
        self.rect = Rect(0, 0, BLOCK_W * DIM[0], BLOCK_W * DIM[1])
        self.arm = pg.Surface((int(self.rect.w / 4), int(self.rect.h / 3)), SRCALPHA)
        pg.draw.rect(self.arm, (200, 128, 0), (0, 0, self.arm.get_size()[0], self.arm.get_size()[1]))
        # This determines the area in which items are collected
        self.collection_range = Rect(0, 0, 6 * BLOCK_W, 6 * BLOCK_W)
        self.collection_range.center = self.rect.center
        # This determines the area that you can place blocks
        self.placement_range = Rect(0, 0, 7 * BLOCK_W, 7 * BLOCK_W)
        self.placement_range.center = self.rect.center
        # Sprite
        self.surface = pg.transform.scale(pg.image.load("res/player/player_0.png"),
                                          self.rect.size)
        # Physics variables
        self.pos = [0, 0]
        self.rect.topleft = self.pos
        self.v = [0., 0.]
        self.a = [0, 1]
        # # Holds all events that are on a timer
        # self.events = {}
        # self.add_timed_event(self.regen, 2)
        self.immunity = 0
        # Stores a block whose UI is active
        self.ui_block = None

    def load(self, file):
        with open(file, "rb+") as data_file:
            data = data_file.read()
            # Bytes 1&2 are HP
            # Everything else is inventory
            self.inventory.load(data)

    def write(self, file):
        # See load() for info order
        with open(file, "wb+") as file:
            file.write(self.inventory.write())

    def run(self, events, dt):
        self.handler.spawn(self.rect.center)

        rect = self.driver.get_view_rect(self.rect.center)
        pos = pg.mouse.get_pos()
        global_pos = (pos[0] + rect.x, pos[1] + rect.y)

        for e in events:
            if self.ui_block is None or self.ui_block.process_event(e, -1):
                if e.type == QUIT:
                    c.game_state = c.END_GAME
                elif e.type == VIDEORESIZE:
                    c.resize(e.w, e.h)
                    if self.ui_block is not None:
                        self.ui_block.resize()
                elif e.type == MOUSEBUTTONUP and \
                        (e.button == BUTTON_WHEELUP or e.button == BUTTON_WHEELDOWN):
                    self.inventory.scroll(e.button == BUTTON_WHEELUP)
                elif e.type == KEYUP or e.type == KEYDOWN:
                    up = e.type == KEYUP
                    # Try to jump
                    if e.key == K_SPACE:
                        if up:
                            self.a[1] = 1
                        else:
                            if touching_blocks_y(self.pos, self.rect, False):
                                self.v[1] = -15
                    elif self.use_item == -1 or True:
                        self.inventory.key_pressed(e.key, up)

        mouse = pg.mouse.get_pressed()
        keys = pg.key.get_pressed()
        if self.ui_block is not None:
            self.ui_block.process_pressed(mouse, keys)

        # Mouse click events
        if mouse[BUTTON_LEFT - 1]:
            self.left_click(pos, global_pos)
        elif mouse[BUTTON_RIGHT - 1]:
            self.right_click(pos, global_pos, dt)
        if not mouse[BUTTON_RIGHT - 1]:
            self.inventory.holding_r = 0

        # Key pressed events
        self.a[0] = 0 if not keys[K_a] ^ keys[K_d] else -1 if keys[K_a] \
            else 1

        # Update player and all entities/items/projectiles
        self.move(dt)
        self.handler.move(dt, self.rect.center, self.pick_up)
        # Check if anything hit the player
        if self.immunity <= 0:
            dmg, entity_x = self.handler.check_hit_player(self.rect)
            if dmg > 0:
                self.hit(dmg, entity_x)
        # Check if the player hit anything
        if self.item_used is not None and self.item_used.polygon is not None:
            self.handler.check_hit_entities(self.rect.centerx, self.item_used)

        # Redraw the screen
        self.draw_ui()

    def spawn(self):
        self.pos = [W.world_spawn[0] * BLOCK_W, (W.world_spawn[1] - DIM[1]) * BLOCK_W]
        self.rect.topleft = self.pos

    def move(self, dt):
        if dt == 0:
            return

        self.immunity -= dt

        dt /= 1000

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

        check_collisions(self.pos, DIM, d)
        self.rect.topleft = self.pos
        self.collection_range.center = self.rect.center
        self.placement_range.center = self.rect.center

        if touching_blocks_y(self.pos, self.rect, True):
            self.v[1] = 1

        # Use an item
        if self.use_time > 0:
            self.use_time -= dt
            if self.use_time <= 0:
                self.item_used = None

        # # Do anything on a timer
        # delete = []
        # for key in self.events.keys():
        #     self.events[key][0] -= dt
        #     t_left, t_max, iter_left = self.events[key]
        #     if t_left <= 0:
        #         key()
        #         if iter_left != -1:
        #             self.events[key][2] -= 1
        #         if iter_left - 1 == 0:
        #             delete.append(key)
        #         else:
        #             self.events[key][0] = t_max
        # for key in delete:
        #     self.events.pop(key)

    def left_click(self, pos, global_pos):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.use_time = self.inventory.left_click(pos)
        elif self.use_time <= 0:
            idx = self.inventory.get_held_item()
            if idx != -1:
                item = items[idx]
                self.used_left = global_pos[0] < self.rect.centerx
                in_range = self.placement_range.collidepoint(global_pos[0], global_pos[1])
                block_rect = Rect(int(global_pos[0] / BLOCK_W) * BLOCK_W, int(global_pos[1] / BLOCK_W) * BLOCK_W,
                                  BLOCK_W, BLOCK_W)
                if in_range and item.placeable:
                    if not self.rect.colliderect(block_rect) and \
                            not self.handler.collides_with_entity(block_rect) and \
                            self.driver.place_block(global_pos, idx):
                        self.use_item()
                else:
                    self.use_item()
                    if in_range and item.break_blocks:
                        broken = self.driver.destroy_block(global_pos)
                        if broken != AIR_ID:
                            dropped = items[broken].clone(1)
                            dropped.drop(block_rect.center, None)
                            self.handler.items.append(dropped)

    def right_click(self, pos, global_pos, dt):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.use_time = self.inventory.right_click(pos, dt)
        elif self.use_time <= 0:
            block_x, block_y = global_pos[0] // BLOCK_W, global_pos[1] // BLOCK_W
            block = items[W.blocks[block_y][block_x]]
            if block.clickable:
                block.activate()
                self.ui_block = block
            else:
                # Check if we dropped an item
                drop = self.inventory.drop_item()
                if drop is not None:
                    val, amnt = drop
                    # This determines if we clicked to the left or right of the player
                    left = global_pos[0] < self.rect.centerx
                    obj = items[val].clone(amnt)
                    obj.drop(self.rect.center, left)
                    self.handler.items.append(drop)

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
        display.fill(W.get_day_color())
        # Draw blocks
        display.blit(self.driver.blocks_surface, (0, 0), area=rect)
        # Draw all entities/projectiles/items, in that order
        self.handler.get_display(rect)

        # Draw player and inventory
        display.blit(self.surface, (self.pos[0] - rect.x, self.pos[1] - rect.y))
        display.blit(self.inventory.surface, (0, 0), area=self.inventory.rect)

        # Draw item being used
        if self.item_used is not None:
            # Get use animation state
            s, center = self.item_used.use_anim(self.use_time, self.arm, self.used_left, self.rect.center)
            s_rect = s.get_rect()
            s_rect.center = [center[0] - rect.x,
                             center[1] - rect.y]
            display.blit(s, s_rect)

        # Draw block ui
        if self.ui_block is not None:
            if self.ui_block.ui is not None:
                display.blit(self.ui_block.ui, self.ui_block.ui_rect)
            else:
                self.ui_block = None

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

    def use_item(self):
        self.item_used = items[self.inventory.get_held_item()]
        self.use_time = self.item_used.use_time
        if self.item_used.consumable:
            self.inventory.use_item()

    def get_damage(self):
        if isinstance(self.item_used, Tool):
            return (self.item_used.damage + self.stats.dmg) * self.stats.dmg_mult
        return 0

    def hit(self, dmg, centerx):
        self.stats.hp -= dmg
        if self.stats.hp <= 0:
            self.respawn()
        else:
            self.immunity = 1000
            self.v = [copysign(3, self.rect.centerx - centerx), -3]

    def respawn(self):
        self.stats.hp = self.stats.max_hp
        self.immunity = 5000
        self.pos = [0., 0.]
        self.rect.topleft = self.pos

    # def add_timed_event(self, func, max_time, iterations=-1):
    #     self.events[func] = [max_time, max_time, iterations]
    #
    # def regen(self):
    #     if self.stats.hp < self.stats.max_hp:
    #         self.stats.hp += 1


def create_new_player(file_name):
    with open("saves/players/" + file_name + ".plr", "wb+") as file:
        file.write((1).to_bytes(2, byteorder))
        file.write((3).to_bytes(2, byteorder))
        file.write((1).to_bytes(2, byteorder))
        file.write((4).to_bytes(2, byteorder))
        file.write((5).to_bytes(2, byteorder))
        file.write((7).to_bytes(2, byteorder))
        nothing = (0).to_bytes(2, byteorder)
        file.write(nothing * 92)
