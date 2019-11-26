# Created on 22 October 2019
# Defines methods and variables for the player

from sys import byteorder
from pygame.image import load
from pygame.transform import scale
from pygame.locals import *
from pygame.draw import rect as draw_rect
from pygame.mouse import get_pos
from pygame import Surface
from math import ceil, copysign
from Databases.constants import *
from Databases import constants as c
from Databases.ai import check_collisions
import World as w
from Player.Inventory import Inventory
from Objects.Block import Block
from Objects.Tool import Tool
from Player.Stats import Stats
from Databases.lists import items

DIM = (1.5, 3)


class Player:
    def __init__(self):
        self.pos = [w.world_spawn[0] * BLOCK_W, (w.world_spawn[1] - DIM[1]) * BLOCK_W]
        # Stats
        self.stats = Stats(hp=100, max_speed=[15, 15])
        # Inventory
        self.inventory = Inventory()
        self.item_used, self.use_time = None, 0
        self.used_left = True
        # Hit box
        self.rect = Rect(self.pos[0], self.pos[1], BLOCK_W * DIM[0], BLOCK_W * DIM[1])
        self.arm = Surface((int(self.rect.w / 4), int(self.rect.h / 3)), SRCALPHA)
        draw_rect(self.arm, (200, 128, 0), (0, 0, self.arm.get_size()[0], self.arm.get_size()[1]))
        # This determines the area in which items are collected
        self.collection_range = Rect(0, 0, 6 * BLOCK_W, 6 * BLOCK_W)
        self.collection_range.center = self.rect.center
        # This determines the area that you can place blocks
        self.placement_range = Rect(0, 0, 7 * BLOCK_W, 7 * BLOCK_W)
        self.placement_range.center = self.rect.center
        # Sprite
        self.surface = scale(load("res/player/player_0.png"), self.rect.size)
        # Physics variables
        self.rect.topleft = self.pos
        self.v = [0., 0.]
        self.a = [0, 1]
        # Holds all events that are on a timer
        self.events = {}
        self.add_timed_event(self.regen, 2)
        self.immunity = 0
        # Handles clicks
        self.left, self.right = False, False

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

        check_collisions(w.blocks, self.pos, DIM, d)
        self.rect.topleft = self.pos
        self.collection_range.center = self.rect.center
        self.placement_range.center = self.rect.center

        if self.touching_blocks_y(True):
            self.v[1] = 1

        # Use an item
        if self.use_time > 0:
            self.use_time -= dt
            if self.use_time <= 0:
                self.item_used = None

        # Do anything on a timer
        delete = []
        for key in self.events.keys():
            self.events[key][0] -= dt
            t_left, t_max, iter_left = self.events[key]
            if t_left <= 0:
                key()
                if iter_left != -1:
                    self.events[key][2] -= 1
                if iter_left - 1 == 0:
                    delete.append(key)
                else:
                    self.events[key][0] = t_max
        for key in delete:
            self.events.pop(key)

    def touching_blocks_x(self, left):
        # Check if we are actually touching a new block (including non-solid)
        touching = (self.rect.left if left else self.rect.right) % BLOCK_W == 0
        if touching:
            # Get next x block
            next_x = int(self.rect.left / BLOCK_W) - 1 if left else ceil(self.rect.right / BLOCK_W)
            # Check if we are going to the world edge
            if next_x < 0 if left else next_x >= w.blocks.shape[1]:
                return True
            # Otherwise check if there is a solid block
            else:
                y_range = (int(self.rect.top / BLOCK_W), ceil(self.rect.bottom / BLOCK_W))
                collide = w.blocks[y_range[0]:y_range[1], next_x].tolist()
                return collide.count(AIR_ID) < len(collide)
        return False

    def touching_blocks_y(self, top):
        # Check if we are actually touching a new block (including non-solid)
        touching = (self.rect.top if top else self.rect.bottom) % BLOCK_W == 0
        if touching:
            # Get next y block
            next_y = int(self.rect.top / BLOCK_W) - 1 if top else ceil(self.rect.bottom / BLOCK_W)
            # Check if we are going to the world edge
            if next_y < 0 if top else next_y >= w.blocks.shape[0]:
                return True
            # Otherwise check if there is a solid block
            else:
                x_range = (int(self.rect.left / BLOCK_W), ceil(self.rect.right / BLOCK_W))
                collide = w.blocks[next_y, x_range[0]:x_range[1]].tolist()
                return collide.count(AIR_ID) < len(collide)
        return False

    def key_pressed(self, key, up):
        # Move Left
        if key == K_a:
            self.a[0] += 1 if up else -1
        # Move Right
        elif key == K_d:
            self.a[0] += -1 if up else 1
        # Try to jump
        elif key == K_SPACE:
            if up:
                self.a[1] = 1
            else:
                if self.touching_blocks_y(False):
                    self.v[1] = -15
        elif self.use_item == -1 or True:
            self.inventory.key_pressed(key, up)

    def mouse_pressed(self, button, up):
        if (button == BUTTON_WHEELUP or button == BUTTON_WHEELDOWN) and not up:
            self.inventory.scroll(button == BUTTON_WHEELUP)
        elif button == BUTTON_LEFT:
            self.left = not up
        elif button == BUTTON_RIGHT:
            self.right = not up
            if up:
                self.inventory.holding_r = 0

    # Returns int - id of block to put at mouse location, None if not placing block
    def left_click(self, pos, global_pos):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.use_time = self.inventory.left_click(pos)
        elif self.use_time <= 0:
            item = self.inventory.get_held_item()
            if item != -1:
                item = items[item]
                self.used_left = global_pos[0] < self.rect.centerx
                in_range = self.placement_range.collidepoint(global_pos[0], global_pos[1])
                rect = Rect(int(global_pos[0] / BLOCK_W) * BLOCK_W, int(global_pos[1] / BLOCK_W) * BLOCK_W,
                            BLOCK_W, BLOCK_W)
                if isinstance(item, Block) and in_range and not self.rect.colliderect(rect):
                    return item.idx
                elif isinstance(item, Tool):
                    self.use_item()
                    if item.break_blocks and in_range:
                        return AIR_ID

    # Returns Item - item representing amount and count of object to be dropped, None if not dropping
    def right_click(self, pos, global_pos, dt):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.use_time = self.inventory.right_click(pos, dt)
        elif self.use_time <= 0:
            # Check if we dropped an item
            drop = self.inventory.drop_item()
            if drop is not None:
                val, amnt = drop
                # This determines if we clicked to the left or right of the player
                left = global_pos[0] < self.rect.centerx
                obj = items[val].clone(amnt)
                obj.drop(self.rect.center, left)
                return obj

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

    def draw_ui(self, rect):
        c.display.blit(self.surface, (self.pos[0] - rect.x, self.pos[1] - rect.y))
        c.display.blit(self.inventory.surface, (0, 0), area=self.inventory.rect)

        # Draw item being used
        if self.item_used is not None:
            # Get use animation state
            s, center = self.item_used.use_anim(self.use_time, self.arm, self.used_left, self.rect.center)
            s_rect = s.get_rect()
            s_rect.center = [center[0] - rect.x,
                             center[1] - rect.y]
            c.display.blit(s, s_rect)

        life_text = str(self.stats.hp) + " / " + str(self.stats.max_hp) + " HP"
        # Draw stats
        text = c.ui_font.render(life_text, 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.right = rect.w
        c.display.blit(text, text_rect)

        # Draw selected item under cursor if there is one
        cursor = self.inventory.get_cursor_display()
        if cursor is not None:
            c.display.blit(cursor, get_pos())

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

    def add_timed_event(self, func, max_time, iterations=-1):
        self.events[func] = [max_time, max_time, iterations]

    def regen(self):
        if self.stats.hp < self.stats.max_hp:
            self.stats.hp += 1


def create_new_player(file_name):
    with open("saves/players/" + file_name + ".plr", "wb+") as file:
        file.write((1).to_bytes(2, byteorder))
        file.write((3).to_bytes(2, byteorder))
        file.write((1).to_bytes(2, byteorder))
        file.write((4).to_bytes(2, byteorder))
        nothing = (0).to_bytes(2, byteorder)
        for i in range(48):
            file.write(nothing)
