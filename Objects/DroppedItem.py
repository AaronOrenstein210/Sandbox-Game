# Created on 5 December 2019
# Runs a dropped item, allowing it to move

import math
import pygame as pg
from Tools import objects as o
from Tools.constants import BLOCK_W, ITEM_W, MAX_FALL_SPEED
from NPCs.Entity import check_collisions

X_SPEED = 15


class DroppedItem:
    def __init__(self, item_id, amnt):
        self.idx = item_id
        self.item = o.items[item_id]
        self.max_stack = self.item.max_stack
        self.amnt = amnt
        self.rect = pg.Rect(0, 0, ITEM_W, ITEM_W)
        # Movement variables
        self.pos = [0., 0.]
        self.v = [0., 0.]
        # Variables for picking up this item
        self.pick_up_immunity = 0
        self.pulled_in = False

    def move(self):
        if o.dt == 0:
            return
        self.pick_up_immunity = max(self.pick_up_immunity - o.dt, 0)
        dt = o.dt / 1000
        d = [self.v[0] * dt * BLOCK_W, self.v[1] * dt * BLOCK_W]
        if not self.pulled_in:
            # Update vertical position and velocity
            self.v[0] = math.copysign(max(abs(self.v[0]) - 1, 0), self.v[0])
            self.v[1] += MAX_FALL_SPEED * dt / 2
            self.v[1] = min(self.v[1], MAX_FALL_SPEED / 2)

            ratio = ITEM_W / BLOCK_W
            check_collisions(self.pos, (ratio, ratio), d)
        else:
            self.pos = [self.pos[0] + d[0], self.pos[1] + d[1]]
        self.rect.topleft = self.pos

    def drop(self, human_center, left):
        self.pulled_in = False
        self.rect.center = human_center
        self.pos = [self.rect.left, self.rect.top]
        self.v = [0 if left is None else -X_SPEED if left else X_SPEED, 0]
        self.pick_up_immunity = 1500 if left is not None else 0

    def attract(self, point):
        # Calculate velocities
        delta = [point[0] - self.rect.centerx, point[1] - self.rect.centery]
        self.v = [math.copysign(4, delta[0]), math.copysign(4, delta[1])]
        self.pulled_in = True
