# Created on 31 October 2019
# Defines functions and variables for placeable items

from math import copysign, asin, sin, cos, sqrt, pi, radians
from pygame import Surface, Rect, SRCALPHA
from pygame.transform import scale, rotate
from Tools.constants import ITEM_W, MAX_FALL_SPEED, BLOCK_W
from NPCs.Entity import check_collisions

X_SPEED = 15


class Item:
    def __init__(self, idx, name, amnt, max_stack, use_time, consumable):
        self.idx, self.name = idx, name
        self.max_stack = max_stack
        self.amnt = min(self.max_stack, amnt)
        self.use_time = use_time
        # Information booleans
        self.consumable = consumable
        self.spawner = False
        self.placeable = False
        self.clickable = False
        self.usable = False
        # Create the item's icon, default filled black
        self.rect = Rect(0, 0, ITEM_W, ITEM_W)
        self.icon = Surface((BLOCK_W, BLOCK_W))
        self.image = Surface((BLOCK_W, BLOCK_W))
        # Movement variables
        self.pos = [0., 0.]
        self.v = [0., 0.]
        # Variables for picking up this item
        self.pick_up_immunity = 0
        self.pulled_in = False
        # Attack box, if applicable
        self.polygon = None

    def get_icon_display(self, w):
        return scale(self.icon, (int(w), int(w)))

    def get_dropped_display(self):
        size = self.image.get_size()
        frac = ITEM_W / min(size)
        return scale(self.image, (int(frac * size[0]), int(frac * size[1])))

    def move(self, dt):
        if dt == 0:
            return
        self.pick_up_immunity = max(self.pick_up_immunity - dt, 0)
        dt /= 1000
        d = [self.v[0] * dt * BLOCK_W, self.v[1] * dt * BLOCK_W]
        if not self.pulled_in:
            # Update vertical position and velocity
            self.v[0] = copysign(max(abs(self.v[0]) - 1, 0), self.v[0])
            self.v[1] += MAX_FALL_SPEED * dt / 2
            self.v[1] = min(self.v[1], MAX_FALL_SPEED / 2)

            ratio = ITEM_W / BLOCK_W
            check_collisions(self.pos, (ratio, ratio), d)
        else:
            self.pos = [self.pos[0] + d[0], self.pos[1] + d[1]]
        self.rect.topleft = self.pos

    def drop(self, human_center, left):
        global X_SPEED
        self.pulled_in = False
        self.rect.center = human_center
        self.pos = [self.rect.left, self.rect.top]
        self.v = [0 if left is None else -X_SPEED if left else X_SPEED, 0]
        self.pick_up_immunity = 1500 if left is not None else 0

    def attract(self, point):
        # Calculate velocities
        delta = [point[0] - self.rect.centerx, point[1] - self.rect.centery]
        self.v = [copysign(5, delta[0]), copysign(5, delta[1])]
        self.pulled_in = True

    def use_anim(self, time_used, arm, left, player_center):
        arm_dim = arm.get_size()
        img_dim = self.image.get_size()
        w, h = max(img_dim[0], arm_dim[0]), img_dim[1] + arm_dim[1]
        s = Surface((w, h), SRCALPHA)
        s.blit(arm, (int((w / 2) - (arm_dim[0] / 2)), img_dim[1]))
        s.blit(self.image, (0, 0))

        theta = 120 - (time_used * 165 / self.use_time)
        theta *= 1 if left else -1

        # calculate end of arm that attaches to player
        c = [0, -int(h / 2)]
        # Rotate the center point
        r = sqrt(pow(c[0], 2) + pow(c[1], 2))
        theta_i = asin(c[1] / r)
        if c[0] < 0:
            theta_i = pi - theta_i
        theta_i += radians(theta)
        c[0], c[1] = int(r * cos(theta_i)), int(-r * sin(theta_i))
        # Calculate center of tool image (player center offset by end of arm)
        c = [player_center[0] - c[0], player_center[1] - c[1]]

        return rotate(s, theta), c
