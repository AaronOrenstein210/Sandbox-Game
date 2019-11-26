# Created on 31 October 2019
# Defines functions handling various movement AI's

from Databases.constants import BLOCK_W, MAX_FALL_SPEED, AIR_ID
from math import ceil, copysign
from random import randint


# Handles movement, checking for collisions with blocks
def check_collisions(blocks, pos, block_dim, d):
    abs_d = [abs(val) for val in d]
    px_dim = (BLOCK_W * block_dim[0], BLOCK_W * block_dim[1])
    # Break up displacement into smaller parts
    while max(abs_d) > BLOCK_W:
        perc = BLOCK_W / max(abs_d)
        d_ = [d[0] * perc, d[1] * perc]
        check_collisions(blocks, pos, block_dim, d_)
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
            collide = blocks[current_block[1]:current_block[3] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = blocks[next_block[1 if d[1] < 0 else 3], current_block[0]:current_block[2] + 1]
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
            collide = blocks[current_val[0]:current_val[1] + 1, next_block[0 if d[0] < 0 else 2]]
        else:
            # From the lowest column to the highest column, at the next row over
            collide = blocks[next_block[1 if d[1] < 0 else 3], current_val[0]:current_val[1] + 1]
        collide = collide.tolist()
        # All blocks are air, just do the move
        if collide.count(AIR_ID) == len(collide):
            pos[idx2] += d[idx2]
        else:
            pos[idx2] += to_next[idx2]


# Handles directionless movement, code = RANDOM
def random_movement(blocks, entity):
    # Check if we are standing on the ground
    if entity.is_standing(blocks):
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
        hit_wall = entity.hit_wall(blocks)
        if hit_wall is not None:
            entity.v[1] = -12
            entity.a[0] = copysign(1, hit_wall)
            entity.time = randint(1000, 3000)


# Handles movement following the player, code = FOLLOW
def follow_player(blocks, entity, player_pos):
    if entity.time <= 0:
        # Check if we are standing on the ground
        if entity.is_standing(blocks):
            entity.a[0] = copysign(1, player_pos[0] - entity.rect.centerx)
            # Check if we need to jump
            hit_wall = entity.hit_wall(blocks)
            if hit_wall is not None:
                entity.v[1] = -12
        entity.time = 0
