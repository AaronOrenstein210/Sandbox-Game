# Created on 5 December 2019
# Runs a dropped item, allowing it to move

import math
import pygame as pg
from Tools import game_vars
from Tools.constants import BLOCK_W, MAX_FALL_SPEED

X_SPEED = 15


class DroppedItem:
    def __init__(self, item_info):
        self.info = item_info
        self.item = game_vars.items[item_info.item_id]
        self.max_stack = self.item.max_stack

        self.rect = pg.Rect((0, 0), self.item.image.get_size())
        # Used to check for collisions with blocks
        self.ratio = (self.rect.w / BLOCK_W, self.rect.h / BLOCK_W)
        # Movement variables
        self.pos = [0., 0.]
        self.v = [0., 0.]
        # Variables for picking up this item
        self.pick_up_immunity = 0
        self.pulled_in = False

    def move(self):
        if game_vars.dt == 0:
            return
        self.pick_up_immunity = max(self.pick_up_immunity - game_vars.dt, 0)
        d = [v * game_vars.dt * BLOCK_W for v in self.v]
        if not self.pulled_in:
            # Update vertical position and velocity
            self.v[0] = math.copysign(max(abs(self.v[0]) - 1, 0), self.v[0])
            self.v[1] += MAX_FALL_SPEED * game_vars.dt / 2
            self.v[1] = min(self.v[1], MAX_FALL_SPEED / 2)
            game_vars.check_collisions(self.pos, self.ratio, d)
        else:
            self.pos = [self.pos[0] + d[0], self.pos[1] + d[1]]
        self.rect.topleft = self.pos

    def drop(self, pos, left):
        self.pulled_in = False
        self.rect.center = pos
        self.pos = [self.rect.left, self.rect.top]
        self.v = [0 if left is None else -X_SPEED if left else X_SPEED, 0]
        self.pick_up_immunity = 1.5 if left is not None else 0

    def attract(self, point):
        # Calculate velocities
        delta = [point[0] - self.rect.centerx, point[1] - self.rect.centery]
        self.v = [math.copysign(4, delta[0]), math.copysign(4, delta[1])]
        self.pulled_in = True
