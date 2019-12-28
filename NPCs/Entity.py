# Created on 31 October 2019
# Defines functions and variables for the Entity class

from os.path import isfile
from math import copysign, ceil
from random import randint
from pygame import Rect, Surface
from pygame.image import load
from Tools.constants import BLOCK_W
from Objects.tile_ids import AIR
from Tools.constants import scale_to_fit
from Tools import objects as o
from Player.Stats import Stats


# AI functions, takes an entity object as its input
def random_movement(entity):
    entity.time -= o.dt
    # Check if we are standing on the ground
    if touching_blocks_y(entity.pos, entity.dim, False):
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
        if entity.a[0] != 0:
            if (entity.a[0] < 0 and touching_blocks_x(entity.pos, entity.dim, True)) or \
                    (entity.a[0] > 0 and touching_blocks_x(entity.pos, entity.dim, False)):
                entity.v[1] = -12
                entity.time = randint(1000, 3000)


def follow_player(entity):
    # Check if we are standing on the ground
    if touching_blocks_y(entity.pos, entity.dim, False):
        entity.a[0] = copysign(1, o.player.rect.centerx - entity.rect.centerx)
        # Check if we need to jump
        if entity.a[0] != 0:
            if (entity.a[0] < 0 and touching_blocks_x(entity.pos, entity.dim, True)) or \
                    (entity.a[0] > 0 and touching_blocks_x(entity.pos, entity.dim, False)):
                entity.v[1] = -12


def jump(entity, follow):
    # If we are on the ground, progress our timer and make sure we aren't moving
    if touching_blocks_y(entity.pos, entity.dim, False):
        entity.a[0], entity.v[0] = 0, 0
        entity.time -= o.dt
        # If we are done waiting, jump
        if entity.time <= 0:
            if follow:
                entity.a[0] = copysign(1, o.player.rect.centerx - entity.rect.centerx)
            else:
                entity.a[0] = 1 if randint(0, 1) == 0 else -1
            entity.v[0] = entity.stats.spd[0] * entity.a[0]
            entity.v[1] = randint(-15, -5)
            entity.time = randint(1000, 2000)


class Entity:
    def __init__(self, name="No Name", w=1, aggressive=False, rarity=1, img="",
                 stats=Stats()):
        self.rarity = rarity
        # Stores entity info
        self.name = name
        self.stats = stats
        self.aggressive = aggressive

        if isfile(img):
            self.surface = scale_to_fit(load(img), w=w * BLOCK_W)
        else:
            self.surface = Surface((int(w * BLOCK_W), int(w * BLOCK_W)))
        self.dim = (w, self.surface.get_size()[1] / BLOCK_W)
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

    def move(self):
        if self.immunity > 0:
            self.immunity -= o.dt
        dt = o.dt / 1000

        # Figure out change in position
        d = [0, 0]
        for i in range(2):
            d[i] = self.v[i] * dt * BLOCK_W * 2 / 3
            if self.a[i] == 0:
                if self.v[i] != 0:
                    self.v[i] += copysign(min(self.v[0] + (dt * 1), abs(self.v[i])), -self.v[i])
            else:
                self.v[i] += copysign(dt * 20, self.a[i])
                self.v[i] = copysign(min(abs(self.v[i]), self.stats.spd[i]), self.v[i])

        # Update position and check for collisions
        check_collisions(self.pos, self.dim, d)
        self.rect.topleft = self.pos

        # Run ai, ai affects acceleration and velocity
        self.ai()

    # Code the ai here, either using combinations of preexisting
    # ones, ore making a new one
    def ai(self):
        random_movement(self)

    # Take damage, return if we are dead or not
    def hit(self, damage, centerx):
        self.stats.hp -= damage
        self.immunity = 500
        self.time = 0
        self.v = [copysign(5, self.rect.centerx - centerx), -5]
        return self.stats.hp < 0

    def can_spawn(self, conditions):
        return True


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
    blocks = o.world.blocks
    for i in range(2):
        # Get current and next block
        current_block[i] = int(pos[i] / BLOCK_W)
        current_block[i + 2] = ceil((pos[i] + px_dim[i]) / BLOCK_W) - 1
        next_block[i] = int((pos[i] + d[i]) / BLOCK_W)
        next_block[i + 2] = ceil((pos[i] + px_dim[i] + d[i]) / BLOCK_W) - 1
        # If we don't move blocks or we hit the world boundary, just do the movement
        if pos[i] + d[i] < 0:
            pos[i] = 0
            d[i] = 0
        elif next_block[i + 2] >= blocks.shape[1 - i]:
            pos[i] = (blocks.shape[1 - i] * BLOCK_W) - px_dim[i]
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
            collide = blocks[current_block[1]:current_block[3] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = blocks[next_block[1 if d[1] < 0 else 3], current_block[0]:current_block[2] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR) == len(collide):
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
            collide = blocks[current_block[1]:current_block[3] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = blocks[next_block[1 if d[1] < 0 else 3], current_block[0]:current_block[2] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR) == len(collide):
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
            collide = blocks[current_val[0]:current_val[1] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = blocks[next_block[1 if d[1] < 0 else 3], current_val[0]:current_val[1] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR) == len(collide):
            pos[idx2] += d[idx2]
        else:
            pos[idx2] += to_next[idx2]


def touching_blocks_x(pos, dim, left):
    # Get dimensions in pixels
    w, h = dim[0] * BLOCK_W, dim[1] * BLOCK_W
    # Check if we are actually touching a new block (including non-solid)
    if abs(pos[0] + (0 if left else w)) % BLOCK_W == 0:
        # Get next x block
        next_x = int(pos[0] / BLOCK_W) - 1 if left else ceil((pos[0] + w) / BLOCK_W)
        # Check if we are going to the world edge
        if next_x < 0 if left else next_x >= o.world.dim[0]:
            return True
        # Otherwise check if there is a solid block
        else:
            y_range = (int(pos[1] / BLOCK_W), ceil((pos[1] + h) / BLOCK_W))
            collide = o.world.blocks[y_range[0]:y_range[1], next_x].tolist()
            return collide.count(AIR) < len(collide)
    return False


def touching_blocks_y(pos, dim, top):
    # Get dimensions in pixels
    w, h = dim[0] * BLOCK_W, dim[1] * BLOCK_W
    # Check if we are actually touching a new block (including non-solid)
    diff = abs(pos[1] + (0 if top else h)) % BLOCK_W
    touching = diff == 0
    if touching:
        # Get next y block
        next_y = int(pos[1] / BLOCK_W) - 1 if top else ceil((pos[1] + h) / BLOCK_W)
        # Check if we are going to the world edge
        if next_y < 0 if top else next_y >= o.world.dim[1]:
            return True
        # Otherwise check if there is a solid block
        else:
            x_range = (int(pos[0] / BLOCK_W), ceil((pos[0] + w) / BLOCK_W))
            collide = o.world.blocks[next_y, x_range[0]:x_range[1]].tolist()
            return collide.count(AIR) < len(collide)
    return False
