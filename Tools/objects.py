# Created on 3 December 2019
# Contains variable data that multiple objects need

# BE WARY OF IMPORT LOOPS!!!
from sys import exit
from math import ceil
import pygame as pg
from Tools.constants import MS_PER_DAY, NOON, BLOCK_W
from Tools.tile_ids import AIR
from UI.Operations import CompleteTask, loading_bar, percent

items, tiles = {}, {}
biomes, structures = {}, {}
animations = []
player, world = None, None
# World time
world_time = MS_PER_DAY * .4
# Amount of time since last update
dt = 0


def init():
    from inspect import getmembers, isclass
    from Player.Player import Player
    from Objects import ItemObjects, TileObjects
    from World import WorldGenParts
    from World.World import World
    from World.WorldSelector import run_selector, PLAYER, UNIVERSE

    # Compile a list of items
    items.clear(), tiles.clear(), biomes.clear(), structures.clear()
    for module in [ItemObjects, TileObjects, WorldGenParts]:
        for name, obj in getmembers(module):
            if isclass(obj) and module.__name__ in str(obj):
                # The constructor automatically adds the item to the list
                obj()

    global player, world
    player = Player(run_selector(PLAYER))
    player.load()

    universe_name = run_selector(UNIVERSE)
    world = World(universe_name, universe_name)


def get_sky_color():
    return 0, 0, 255 * (1 - pow((world_time - NOON) / NOON, 2))


def tick(delta_time):
    global world_time, dt
    dt = delta_time
    world_time = (world_time + dt) % MS_PER_DAY
    
    
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
    blocks = world.blocks
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


# Checks if we are touching blocks on the left or right
def touching_blocks_x(pos, dim, left):
    # Get dimensions in pixels
    w, h = dim[0] * BLOCK_W, dim[1] * BLOCK_W
    # Check if we are actually touching a new block (including non-solid)
    if abs(pos[0] + (0 if left else w)) % BLOCK_W == 0:
        # Get next x block
        next_x = int(pos[0] / BLOCK_W) - 1 if left else ceil((pos[0] + w) / BLOCK_W)
        # Check if we are going to the world edge
        if next_x < 0 if left else next_x >= world.dim[0]:
            return True
        # Otherwise check if there is a solid block
        else:
            y_range = (int(pos[1] / BLOCK_W), ceil((pos[1] + h) / BLOCK_W))
            collide = world.blocks[y_range[0]:y_range[1], next_x].tolist()
            return collide.count(AIR) < len(collide)
    return False


# Checks if we are touching blocks on the top or bottom
def touching_blocks_y(pos, dim, top):
    # Get dimensions in pixels
    w, h = dim[0] * BLOCK_W, dim[1] * BLOCK_W
    # Check if we are actually touching a new block (including non-solid)
    diff = (pos[1] + (0 if top else h)) % BLOCK_W
    touching = diff == 0
    if touching:
        # Get next y block
        next_y = int(pos[1] / BLOCK_W) - 1 if top else ceil((pos[1] + h) / BLOCK_W)
        # Check if we are going to the world edge
        if next_y < 0 if top else next_y >= world.dim[1]:
            return True
        # Otherwise check if there is a solid block
        else:
            x_range = (int(pos[0] / BLOCK_W), ceil((pos[0] + w) / BLOCK_W))
            collide = world.blocks[next_y, x_range[0]:x_range[1]].tolist()
            return collide.count(AIR) < len(collide)
    return False


# Closes current world
def close_world():
    CompleteTask(world.save_part, [3], loading_bar, ["Saving World"], can_exit=False).run_now()
    player.write()


# Loads a new world
def load_world():
    # Reset world variables
    global world_time
    world_time = MS_PER_DAY * .4
    if not CompleteTask(world.load_part, [], percent, ["Loading World Blocks"]).run_now():
        pg.quit()
        exit(0)
    world.draw_blocks()
    player.handler.reset()
    player.spawn()


# Changes world
def change_world(new_world):
    def screen_goes_white(progress):
        display = pg.display.get_surface()
        player.draw_ui()
        overlay = pg.Surface(display.get_size())
        overlay.fill((255 * progress, 255 * progress, 255))
        overlay.set_alpha(255 * progress)
        display.blit(overlay, (0, 0))

    CompleteTask(world.save_part, [10], screen_goes_white, [], can_exit=False).run_now()
    player.write()
    world.name = new_world
    load_world()
