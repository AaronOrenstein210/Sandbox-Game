# Created on 31 October 2019
# Defines functions and variables for the Entity class

from os.path import isfile
from math import copysign, ceil
from random import randint
from pygame import Rect, Surface
from pygame.image import load
from pygame.transform import scale
from Tools.constants import RANDOM, FOLLOW, BLOCK_W, AIR_ID
import World as W
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

    def move(self, player_pos, dt):
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
            random_movement(self)
        elif self.ai == FOLLOW:
            follow_player(self, player_pos)

        check_collisions(self.pos, self.dim, d)
        self.rect.topleft = self.pos

    # Take damage, return if we are dead or not
    def hit(self, damage, centerx):
        self.stats.hp -= damage
        self.immunity = 500
        self.time = 0
        self.v = [copysign(5, self.rect.centerx - centerx), -5]
        return self.stats.hp < 0

    def can_spawn(self, conditions):
        return True

    def get_move_type(self):
        return self.ai in (RANDOM, FOLLOW)


# Handles movement, checking for collisions with blocks
def check_collisions(pos, block_dim, d):
    abs_d = [abs(val) for val in d]
    px_dim = (BLOCK_W * block_dim[0], BLOCK_W * block_dim[1])
    # Break up displacement into smaller parts
    while max(abs_d) > BLOCK_W:
        perc = BLOCK_W / max(abs_d)
        d_ = [d[0] * perc, d[1] * perc]
        check_collisions(pos, block_dim, d_)
        d = [d[0] - d_[0], d[1] - d_[1]]
        abs_d = [abs(val) for val in d]

    # Calculate current and next block (left, top, right, bottom)
    current_block = [0, 0, 0, 0]
    next_block = [0, 0, 0, 0]
    to_next = [0, 0]
    for i in range(2):
        # Get current anc next block
        current_block[i] = int(pos[i] / BLOCK_W)
        current_block[i + 2] = ceil((pos[i] + px_dim[i]) / BLOCK_W) - 1
        next_block[i] = int((pos[i] + d[i]) / BLOCK_W)
        next_block[i + 2] = ceil((pos[i] + px_dim[i] + d[i]) / BLOCK_W) - 1
        # If we don't move blocks or we hit the world boundary, just do the movement
        if pos[i] + d[i] < 0:
            pos[i] = 0
            d[i] = 0
        elif next_block[i + 2] >= W.blocks.shape[1 - i]:
            pos[i] = (W.blocks.shape[1 - i] * BLOCK_W) - px_dim[i]
            d[i] = 0
        elif current_block[i if d[i] < 0 else i + 2] == next_block[i if d[i] < 0 else i + 2]:
            pos[i] += d[i]
            d[i] = 0
        else:
            # End pos - begin pos, accounting for using right or bottom sides
            to_next[i] = (next_block[i + (0 if d[i] < 0 else 2)] * BLOCK_W) - pos[i] - (
                -BLOCK_W if d[i] < 0 else px_dim[i])

    if d.count(0) == 1:
        idx = 1 - d.index(0)
        if idx == 0:
            # From lowest row to highest row, at the next column over
            collide = W.blocks[current_block[1]:current_block[3] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = W.blocks[next_block[1 if d[1] < 0 else 3], current_block[0]:current_block[2] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR_ID) == len(collide):
            pos[idx] += d[idx]
        # >= 1 block is solid, truncate movement
        else:
            pos[idx] += to_next[idx]
    elif d.count(0) == 0:
        perc = [to_next[0] / d[0], to_next[1] / d[1]]
        # Index of shortest time to next block
        idx = perc.index(min(perc))
        # Index of longest time to next block
        idx2 = 1 - idx
        delta = d[idx] * max(perc)
        # When the idx direction hits the next block, idx2 has not changed blocks
        if idx == 0:
            # From lowest row to highest row, at the next column over
            collide = W.blocks[current_block[1]:current_block[3] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = W.blocks[next_block[1 if d[1] < 0 else 3], current_block[0]:current_block[2] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR_ID) == len(collide):
            pos[idx] += d[idx]
        else:
            # Just move to next block and cuttoff delta
            pos[idx] += to_next[idx]
            delta = to_next[idx]

        # Calculate bounds in the direction of idx when the direction of idx2 hits the next block
        current_val = [int((pos[idx] + delta) / BLOCK_W),
                       ceil((pos[idx] + px_dim[idx] + delta) / BLOCK_W) - 1]
        if idx2 == 0:
            # From lowest row to highest row, at the next column over
            collide = W.blocks[current_val[0]:current_val[1] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = W.blocks[next_block[1 if d[1] < 0 else 3], current_val[0]:current_val[1] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR_ID) == len(collide):
            pos[idx2] += d[idx2]
        else:
            pos[idx2] += to_next[idx2]


def touching_blocks_x(pos, rect, left):
    # Check if we are actually touching a new block (including non-solid)
    touching = abs(pos[0] + (0 if left else rect.w)) % BLOCK_W <= .1
    if touching:
        # Get next x block
        next_x = int(rect.left / BLOCK_W) - 1 if left else ceil(rect.right / BLOCK_W)
        # Check if we are going to the world edge
        if next_x < 0 if left else next_x >= W.blocks.shape[1]:
            return True
        # Otherwise check if there is a solid block
        else:
            y_range = (int(rect.top / BLOCK_W), ceil(rect.bottom / BLOCK_W))
            collide = W.blocks[y_range[0]:y_range[1], next_x].tolist()
            return collide.count(AIR_ID) < len(collide)
    return False


def touching_blocks_y(pos, rect, top):
    # Check if we are actually touching a new block (including non-solid)
    touching = abs(pos[1] + (0 if top else rect.h)) % BLOCK_W <= .1
    if touching:
        # Get next y block
        next_y = int(pos[1] / BLOCK_W) - 1 if top else ceil(rect.bottom / BLOCK_W)
        # Check if we are going to the world edge
        if next_y < 0 if top else next_y >= W.blocks.shape[0]:
            return True
        # Otherwise check if there is a solid block
        else:
            x_range = (int(rect.left / BLOCK_W), ceil(rect.right / BLOCK_W))
            collide = W.blocks[next_y, x_range[0]:x_range[1]].tolist()
            return collide.count(AIR_ID) < len(collide)
    return False


# Handles directionless movement, code = RANDOM
def random_movement(entity):
    # Check if we are standing on the ground
    if touching_blocks_y(entity.pos, entity.rect, False):
        # Check if we are ready to start/stop moving
        if entity.time <= 0:
            # We were stopped
            if entity.a[0] == 0:
                entity.a[0] = 1 if randint(0, 1) == 0 else -1
                entity.time = randint(2500, 5000)
            # We were moving
            else:
                entity.a[0] = 0
                entity.time = randint(1000, 3000)
        # Check if we need to jump
        hit_wall = -1 if touching_blocks_x(entity.pos, entity.rect, True) else 1 if \
            touching_blocks_x(entity.pos, entity.rect, False) else None
        if hit_wall is not None:
            entity.v[1] = -12
            entity.a[0] = copysign(1, hit_wall)
            entity.time = randint(1000, 3000)


# Handles movement following the player, code = FOLLOW
def follow_player(entity, player_pos):
    if entity.time <= 0:
        # Check if we are standing on the ground
        if touching_blocks_y(entity.pos, entity.rect, False):
            entity.a[0] = copysign(1, player_pos[0] - entity.rect.centerx)
            # Check if we need to jump
            hit_wall = -1 if touching_blocks_x(entity.pos, entity.rect, True) else 1 if \
                touching_blocks_x(entity.pos, entity.rect, False) else None
            if hit_wall is not None:
                entity.v[1] = -12
        entity.time = 0
