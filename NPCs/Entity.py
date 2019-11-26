# Created on 31 October 2019
# Defines functions and variables for the Entity class

from os.path import isfile
from pygame import Rect, Surface
from pygame.image import load
from pygame.transform import scale
from Databases.ai import *
from Databases.constants import RANDOM, FOLLOW
from Player.Stats import Stats


class Entity:
    def __init__(self, name="No Name", w=1, ai=RANDOM, aggressive=False, rarity=1, img="",
                 stats=Stats()):
        self.rarity = rarity
        # Stores entity info
        self.name = name
        self.stats = stats
        # Stores ai type to use
        self.ai = ai
        self.aggressive = aggressive

        self.dim = (w, w)
        self.surface = Surface((int(w * BLOCK_W), int(w * BLOCK_W)))
        if isfile(img):
            self.surface = load(img)
            size = self.surface.get_size()
            self.dim = (w, size[1] * w / size[0])
            self.surface = scale(self.surface, (int(self.dim[0] * BLOCK_W), int(self.dim[1] * BLOCK_W)))
        # Hit box
        self.rect = Rect(0, 0, self.surface.get_size()[0], self.surface.get_size()[1])
        # Movement variables
        self.pos = [0., 0.]
        self.v = [0., 0.]
        self.a = [0, 1]
        self.time = 0
        self.immunity = 0

    def set_pos(self, x, y):
        self.pos = [x, y]
        self.rect.topleft = self.pos

    def move(self, blocks, player_pos, dt):
        self.time -= dt
        if self.immunity > 0:
            self.immunity -= dt
        dt /= 1000

        # Figure out change in position
        d = [0, 0]
        for i in range(2):
            d[i] = self.v[i] * dt * BLOCK_W
            # Update the position and constrain it within our bounds
            d[i] = (BLOCK_W * 2 / 3) * (self.v[i] * dt)
            if self.a[i] == 0:
                if self.v[i] != 0:
                    self.v[i] += copysign(min(self.v[0] + (dt * 1), abs(self.v[i])), -self.v[i])
            else:
                self.v[i] += copysign(dt * 20, self.a[i])
                self.v[i] = copysign(min(abs(self.v[i]), self.stats.spd[i]), self.v[i])

        # Run ai, ai mostly influences horizontal motion but can also rewrite vertical motion
        if self.ai == RANDOM:
            random_movement(blocks, self)
        elif self.ai == FOLLOW:
            follow_player(blocks, self, player_pos)

        check_collisions(blocks, self.pos, self.dim, d)
        self.rect.topleft = self.pos

    # Take damage, return if we are dead or not
    def hit(self, damage, centerx):
        self.stats.hp -= damage
        self.immunity = 500
        self.time = 0
        self.v = [copysign(5, self.rect.centerx - centerx), -5]
        return self.stats.hp < 0

    # Checks if we are standing on solid blocks
    def is_standing(self, blocks):
        next_y = ceil((self.pos[1] + self.rect.h) / BLOCK_W)
        if next_y >= blocks.shape[0]:
            return True
        ground = blocks[next_y, int(
            self.pos[0] / BLOCK_W):ceil((self.pos[0] + self.rect.w) / BLOCK_W)].tolist()
        return ground.count(AIR_ID) < len(ground)

    # Checks if we have hit a wall and in which direction
    def hit_wall(self, blocks):
        # Check left and then right
        for i, x in enumerate((int(self.pos[0] / BLOCK_W) - 1, ceil((self.pos[0] + self.rect.w) / BLOCK_W))):
            if x < 0 or x >= blocks.shape[1]:
                return True
            wall = blocks[int(self.pos[1] / BLOCK_W):ceil((self.pos[1] + self.rect.h) / BLOCK_W), x].tolist()
            if wall.count(AIR_ID) < len(wall):
                return -1 if i == 0 else 1
        return None

    def can_spawn(self, conditions):
        return True

    def get_move_type(self):
        return self.ai in (RANDOM, FOLLOW)
