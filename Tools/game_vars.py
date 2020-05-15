# Created on 3 December 2019
# Contains variable data that multiple objects need

# BE WARY OF IMPORT LOOPS!!!
from sys import exit, byteorder
from time import time
import pygame as pg
import math
from pygame.locals import QUIT, VIDEORESIZE
from Tools.constants import BLOCK_W, resize
from Tools import constants as c
from Tools.tile_ids import AIR
from UI.Operations import CompleteTask, LoadWorld, SaveWorld

# Object dictionaries
items, tiles = {}, {}
biomes, structures = {}, {}
# All non-solid tiles
non_solid = []
# Current animations
animations = []
# Game objects, each of these gets set ONCE
world = handler = player = None
# Game time and time since last update (seconds)
game_time = dt = 0
# Change in mouse pos since last update
d_mouse = [0, 0]
# Damage text boxes ([surface, rect, timer])
dmg_text = []


def init():
    global game_time
    game_time = time()

    # Load object lists
    from inspect import getmembers, isclass
    from Objects import ItemObjects, TileObjects
    from World import WorldGenParts

    # Compile a list of items, tiles, biomes, and structures
    items.clear(), tiles.clear(), biomes.clear(), structures.clear(), non_solid.clear()
    for module in [ItemObjects, TileObjects, WorldGenParts]:
        for name, obj in getmembers(module):
            if isclass(obj) and module.__name__ in str(obj):
                # The constructor automatically adds the item to the list
                if module == TileObjects:
                    tile = obj()
                    if not tile.barrier:
                        non_solid.append(tile.idx)
                else:
                    obj()

    # Load world and player and initialize entity handler
    from NPCs.EntityHandler import EntityHandler
    from World.Selector import MainSelector

    global handler
    handler = EntityHandler()
    # Selects player, universe, and world
    if not MainSelector().run():
        pg.quit()
        exit(0)


def tick():
    # Update game time and get time since last tick
    global game_time, dt, d_mouse
    dt = time() - game_time
    game_time += dt
    d_mouse = pg.mouse.get_rel()

    # Check events
    events = pg.event.get()
    for e in events:
        if e.type == QUIT:
            return False
        elif e.type == VIDEORESIZE:
            resize(e.w, e.h)
            player.on_resize()
            events.remove(e)

    # Update every animation
    for a in animations:
        a.update(dt)

    # Update world
    world.tick(dt)

    # Update the player
    if player.map_open:
        player.run_map(events)
    else:
        player.run_main(events)

    # Spawn entities
    handler.spawn()
    # Move entities, dropped items, and projectiles
    # Also checks collisions and attacks
    handler.move(player)

    draw()
    return True


def draw():
    display = pg.display.get_surface()
    display.fill(world.sky_color)
    rect = world.get_screen_rect(player.rect.center)

    if player.map_open:
        # Draw world map
        player.draw_map()
    else:
        # Draw background - sky and blocks
        world.manager.draw(rect)
        # Draw enemies, items, and projectiles
        handler.draw_display(rect)
        # Draw pre-ui player visuals
        player.draw_pre_ui(rect)
        # Draw lighting
        # world.draw_light(rect)
        # Draw damage text boxes
        for arr in dmg_text:
            # Decrement textbox counter
            arr[2] -= dt
            # Check if the textbox is done
            if arr[2] <= 0:
                dmg_text.remove(arr)
            else:
                # Move the text up
                arr[1][1] -= BLOCK_W * 1.5 * dt
                # Check if we need to blit it
                r = arr[0].get_rect(center=arr[1])
                if r.colliderect(rect):
                    display.blit(arr[0], (r.x - rect.x, r.y - rect.y))
        # Draw player ui
        player.draw_ui(rect)

    # Draw fps
    fps = int(1 / dt)
    print("\r" + str(fps), end=" ")
    text = c.ui_font.render(str(fps) + " FPS", 1, (255, 255, 255))
    text_rect = text.get_rect(bottom=pg.display.get_surface().get_size()[1])
    pg.display.get_surface().blit(text, text_rect)


def player_inventory():
    return player.inventory


# Functions that affect the world object
# Current universe name
def universe():
    return world.file.universe


# World dimensions in blocks
def world_dim():
    return world.dim


# Returns position of mouse with respect to the entire world
def global_mouse_pos(blocks=False):
    pos = pg.mouse.get_pos()
    screen_c = c.screen_center
    world_c = world.get_screen_rect(player.rect.center).center
    if blocks:
        return [(pos[i] - screen_c[i] + world_c[i]) // BLOCK_W for i in range(2)]
    else:
        return [pos[i] - screen_c[i] + world_c[i] for i in range(2)]


# Get block at position
def get_block_at(x, y):
    if 0 <= x < world.dim[0] and 0 <= y < world.dim[1]:
        x, y = get_topleft(x, y)
        return world.blocks[y, x]
    print("get_block_at(): Coords out of bounds: {}, {}".format(x, y))
    return 0


# Returns the topleft coordinates of the block at x,y (for multiblocks)
def get_topleft(x, y):
    if 0 <= x < world.dim[0] and 0 <= y < world.dim[1]:
        idx = world.blocks[y][x]
        if idx < 0:
            idx *= -1
            x -= idx // 100
            y -= idx % 100
        return x, y
    else:
        print("get_topleft(): Coords out of bounds: {}, {}".format(x, y))
    return 0, 0


# Get block data
def get_block_data(pos):
    return c.get_from_dict(*pos, world.block_data)


# Write block data, input data as none to remove
def write_block_data(pos, data):
    if data is not None:
        c.update_dict(*pos, data, world.block_data)
    else:
        c.remove_from_dict(*pos, world.block_data)


# Attempts to break a block, returns true if successful, false otherwise
def break_block(x, y):
    if 0 <= x < world.dim[0] and 0 <= y < world.dim[1]:
        x, y = get_topleft(x, y)
        block = world.blocks[y][x]
        if block != AIR:
            tile = tiles[block]
            if tile.on_break((x, y)):
                world.destroy_block(x, y)
                block_rect = pg.Rect(x * BLOCK_W, y * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
                drops = tile.get_drops()
                from Objects.DroppedItem import DroppedItem
                for drop in drops:
                    # Drop an item
                    drop_item(DroppedItem(drop), None, pos_=block_rect.center)
                return True
    return False


# Attempts to place a block, returns true if successful, false otherwise
def place_block(x, y, idx):
    tile = tiles[idx]
    # Calculate block rectangle
    block_rect = pg.Rect(x * BLOCK_W, y * BLOCK_W, tile.dim[0] * BLOCK_W, tile.dim[0] * BLOCK_W)
    if not player.rect.colliderect(block_rect) and \
            not handler.collides_with_entity(block_rect) and tile.can_place((x, y)):
        world.place_block(x, y, idx)
        tile.on_place((x, y))
        return True
    return False


# Functions that affect the entity handler object
# Drops an item - input position in pixels
#               - left = None drops the item straight down
def drop_item(drop, left, pos_=None):
    if pos_ is None:
        pos_ = player.rect.center
    drop.drop(pos_, left)
    handler.items.append(drop)


# Spawns an enemy
def spawn_entity(entity, pos=None):
    if pos:
        entity.set_pos(*pos)
    handler.add_entity(entity)


# Shoots a projectile
def shoot_projectile(projectile):
    handler.projectiles[projectile.type].append(projectile)


# Adds a damage text box
def add_damage_text(dmg, pos):
    text = c.ui_font.render(str(dmg), 1, (255, 0, 0))
    dmg_text.append([text, list(pos), 1])


# Functions that affect the player object
# Center of the player rectangle, if blocks = True, return in block coords
def player_pos(in_blocks=False):
    if not in_blocks:
        return player.rect.center
    else:
        return [p / BLOCK_W for p in player.rect.center]


# Top left of the player rectangle, see above for in_blocks
def player_topleft(in_blocks=False):
    if not in_blocks:
        return player.pos
    else:
        return [p / BLOCK_W for p in player.pos]


# Functions that check the world blocks
# Checks if a chunk contains only a given tile
def contains_only(x, y, w, h, tile):
    # If the chunk is outside the world, return false
    if not 0 <= x < world.dim[0] - w or not 0 <= y < world.dim[1] - h:
        return False
    for y1 in range(y, y + h):
        for x1 in range(x, x + w):
            if world.blocks[y1][x1] != tile:
                return False
    return True


# Checks if a chunk contains a given tile
def contains(x, y, w, h, tile):
    # lb must be >= 0, If ub < 0 then d is now <= 0
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    # ub must be < world size, if lb > world size then d is now <= 0
    if x + w > world.dim[0]:
        w = world.dim[0] - x
    if y + h > world.dim[1]:
        h = world.dim[1] - y
    if not (w <= 0 or h <= 0):
        for y1 in range(y, y + h):
            for x1 in range(x, x + w):
                if world.blocks[y1][x1] == tile:
                    return True
    return False


# Checks if the blocks adjacent to a chunk conatain
# a given tile or only contain a given tile
def adjacent(x, y, w, h, tile, only):
    left, top, right, bot = True, True, True, True
    # lb must be >= 0, If ub < 0 then d is now <= 0
    if x < 1:
        w += x - 1
        x = 1
        left = False
    if y < 1:
        h += y - 1
        y = 1
        top = False
    # ub must be < world size, if lb > world size then d is now <= 0
    if x + w > world.dim[0] - 1:
        w = world.dim[0] - x - 1
        right = False
    if y + h > world.dim[1] - 1:
        h = world.dim[1] - y - 1
        bot = False
    if not (left or right) or not (top or bot):
        return False
    # Iterate through relevant data
    x_points = ([x - 1] if left else []) + ([x + w] if right else [])
    y_points = ([y - 1] if top else []) + ([y + h] if bot else [])
    data = world.blocks[y:y + h + 1, x_points].flatten() + world.blocks[y_points, x:x + w + 1].flatten()
    for val in data:
        equal = val == tile
        if only and not equal:
            return False
        elif not only and equal:
            return True
    return only


# Checks if any blocks in the given chunk are solid
def any_solid(x1, x2, y1, y2):
    return any(get_block_at(x, y) not in non_solid for x in range(x1, x2) for y in range(y1, y2))


# Handles movement, checking for collisions with blocks
def check_collisions(pos, block_dim, d):
    px_dim = (BLOCK_W * block_dim[0], BLOCK_W * block_dim[1])
    # Break up displacement into smaller parts
    while any(val != 0 for val in d):
        perc = min(BLOCK_W / max(abs(val) for val in d), 1)
        d_ = [d[0] * perc, d[1] * perc]
        d = [d[0] - d_[0], d[1] - d_[1]]

        # Calculate current and next block (left, top, right, bottom)
        current_block = [0, 0, 0, 0]
        next_block = [0, 0]
        to_next = [0, 0]
        blocks = world.blocks
        for i in range(2):
            # Get current and next block
            current_block[i] = int(pos[i] / BLOCK_W)
            current_block[i + 2] = math.ceil((pos[i] + px_dim[i]) / BLOCK_W) - 1
            if d_[i] < 0:
                next_block[i] = int((pos[i] + d_[i]) / BLOCK_W)
            else:
                next_block[i] = math.ceil((pos[i] + px_dim[i] + d_[i]) / BLOCK_W) - 1
            # We didn't move a block in that direction
            if current_block[i if d_[i] < 0 else i + 2] == next_block[i]:
                pos[i] += d_[i]
                d_[i] = 0
            # If our next block is past the world boundary, just move to the world boundary
            elif next_block[i] < 0:
                pos[i] = 0
                d_[i] = 0
            elif next_block[i] >= blocks.shape[1 - i]:
                pos[i] = (blocks.shape[1 - i] * BLOCK_W) - px_dim[i]
                d_[i] = 0
            # Otherwise move up to the next block
            else:
                # End pos - begin pos, accounting for using right or bottom sides
                to_next[i] = (next_block[i] * BLOCK_W) - pos[i] - (
                    -BLOCK_W if d_[i] < 0 else px_dim[i])

        if d_.count(0) == 1:
            idx = 1 - d_.index(0)
            if idx == 0:
                # From lowest row to highest row, at the next column over
                x = next_block[0]
                solid = any_solid(x, x + 1, current_block[1], current_block[3] + 1)
            else:
                # From the lowest column to the highest column, at the next row over
                y = next_block[1]
                solid = any_solid(current_block[0], current_block[2] + 1, y, y + 1)
            # >= 1 block is solid, truncate movement
            if solid:
                pos[idx] += to_next[idx]
            # All blocks are non_solid, just do the move
            else:
                pos[idx] += d_[idx]
        elif d_.count(0) == 0:
            # Index of shortest time to next block
            perc = [to_next[0] / d_[0], to_next[1] / d_[1]]
            idx = perc.index(min(perc))
            # Index of longest time to next block
            idx2 = 1 - idx
            # When the idx direction hits the next block, idx2 has not changed blocks
            if idx == 0:
                # From lowest row to highest row, at the next column over
                x = next_block[0]
                solid = any_solid(x, x + 1, current_block[1], current_block[3] + 1)
            else:
                # From the lowest column to the highest column, at the next row over
                y = next_block[1]
                solid = any_solid(current_block[0], current_block[2] + 1, y, y + 1)
            # Just move to next block and truncate delta
            if solid:
                pos[idx] += to_next[idx]
            # All blocks are non-solid, do the move
            else:
                pos[idx] += d_[idx]

            # Calculate our new position along the axis we just moved
            current_pos = [int(pos[idx] / BLOCK_W), math.ceil((pos[idx] + px_dim[idx]) / BLOCK_W) - 1]
            if idx2 == 0:
                # From lowest row to highest row, at the next column over
                x = next_block[0]
                solid = any_solid(x, x + 1, current_pos[0], current_pos[1] + 1)
            else:
                # From the lowest column to the highest column, at the next row over
                y = next_block[1]
                solid = any_solid(current_pos[0], current_pos[1] + 1, y, y + 1)
            # All blocks are air, just do the move
            if solid:
                pos[idx2] += to_next[idx2]
            else:
                pos[idx2] += d_[idx2]


# Checks if we are touching blocks on the left or right
def touching_blocks_x(pos, dim, left):
    # Get dimensions in pixels
    w, h = dim[0] * BLOCK_W, dim[1] * BLOCK_W
    # Check if we are actually touching a new block (including non-solid)
    if abs(pos[0] + (0 if left else w)) % BLOCK_W == 0:
        # Get next x block
        next_x = int(pos[0] / BLOCK_W) - 1 if left else math.ceil((pos[0] + w) / BLOCK_W)
        # Check if we are going to the world edge
        if next_x < 0 if left else next_x >= world.dim[0]:
            return True
        # Otherwise check if there is a solid block
        else:
            y_range = (int(pos[1] / BLOCK_W), math.ceil((pos[1] + h) / BLOCK_W))
            return any_solid(next_x, next_x + 1, y_range[0], y_range[1])
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
        next_y = int(pos[1] / BLOCK_W) - 1 if top else math.ceil((pos[1] + h) / BLOCK_W)
        # Check if we are going to the world edge
        if next_y < 0 if top else next_y >= world.dim[1]:
            return True
        # Otherwise check if there is a solid block
        else:
            x_range = (int(pos[0] / BLOCK_W), math.ceil((pos[0] + w) / BLOCK_W))
            return any_solid(x_range[0], x_range[1], next_y, next_y + 1)
    return False


# Checks if we are inside a block
def in_block(pos, dim):
    block_pos = [pos[0] / BLOCK_W, pos[1] / BLOCK_W]
    left, top = int(block_pos[0]), int(block_pos[1])
    right, bottom = math.ceil(block_pos[0] + dim[0]), math.ceil(block_pos[1] + dim[1])
    return not (world.blocks[top:bottom, left:right]).any()


# Functions that change the world
# Closes current world
def close_world():
    SaveWorld(world).run_now()
    player.write()


# Loads a new world
def load_world(world_file):
    from World import World

    # Reset entity handler
    handler.reset()

    # Get world type
    with open(world_file.full_file, "rb") as file:
        world_type = int.from_bytes(file.read(2)[1:2], byteorder)

    # Load world
    global world
    del world
    if world_type == World.WORLD:
        world = World.World(world_file)
    elif world_type == World.IDLE:
        world = World.IdleWorld(world_file)
    # Load the world
    if not LoadWorld(world).run_now():
        pg.quit()
        exit(0)
    # Set up player map
    player.set_map_source(world.map)
    # Spawn the player
    player.spawn()


# Changes world
def change_world(world_file):
    def screen_goes_white(progress):
        display = pg.display.get_surface()
        draw()
        overlay = pg.Surface(display.get_size())
        overlay.fill((255 * progress, 255 * progress, 255))
        overlay.set_alpha(255 * progress)
        display.blit(overlay, (0, 0))

    # If the world exists, save it with a fade animation
    if world:
        CompleteTask(world.save_world, [], screen_goes_white, [], can_exit=False).run_now()
    player.write()
    load_world(world_file)
