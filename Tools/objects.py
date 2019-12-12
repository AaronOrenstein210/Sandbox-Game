# Created on 3 December 2019
# Contains variable data that multiple objects need

# BE WARY OF IMPORT LOOPS!!!
from os.path import isfile
from sys import byteorder, exit
from numpy import full, int16
import pygame as pg
from Tools.constants import MS_PER_DAY, NOON, update_dict, get_from_dict
from UI.Operations import CompleteTask
from Objects.tile_ids import AIR

items, tiles, player = {}, {}, None
world_spawn = (0, 0)
blocks, spawners = None, {}
block_data = {}
# Current universe and world
universe_name, world_name = "", ""
# Current world and player files
world_file, player_file = "", ""
# World time
world_time = MS_PER_DAY * .4
# Amount of time since last update
dt = 0


def init(player_name, universe):
    global world_name, world_file, player_file, universe_name
    player_file = "saves/players/" + player_name + ".plr"
    player.load(player_file)

    universe_name = universe
    universe_folder = "saves/universes/" + universe_name + "/"
    world_name = universe_name
    world_file = universe_folder + world_name + ".wld"


def get_sky_color():
    return 0, 0, 255 * (1 - pow((world_time - NOON) / NOON, 2))


def tick(delta_time):
    global world_time, dt
    dt = delta_time
    world_time = (world_time + dt) % MS_PER_DAY


# Closes current world
def close_world():
    CompleteTask(save_world_part, task_args=[world_file, 2], draw_args=("Saving World",), can_exit=False).run_now()
    player.write(player_file)


# Loads a new world
def load_world():
    if not CompleteTask(load_world_part, task_args=[world_file, 2], draw_args=("Loading World Blocks",)).run_now():
        pg.quit()
        exit(0)
    player.driver.draw_blocks()
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

    global world_file
    CompleteTask(save_world_part, task_args=[world_file, 10], can_exit=False,
                 draw_ui=screen_goes_white, draw_args=()).run_now()
    player.write(player_file)
    universe_folder = "saves/universes/" + universe_name + "/"
    world_file = universe_folder + new_world + ".wld"
    load_world()


# Save world, put none for data, spawn, and extra_data to use current world's data
def save_world_part(progress, file, num_rows, data=None, spawn=None, extra_data=None):
    if data is None:
        data = blocks
    if spawn is None:
        spawn = world_spawn
    if extra_data is None:
        extra_data = block_data
    if data is not None:
        code = "wb+" if progress == 0 else "ab+"
        with open(file, code) as file:
            h, w = data.shape
            # If this is the first call, save world dimensions ad spawn
            if progress == 0:
                file.write(w.to_bytes(2, byteorder))
                file.write(h.to_bytes(2, byteorder))
                file.write(spawn[0].to_bytes(2, byteorder))
                file.write(spawn[1].to_bytes(2, byteorder))
            # Save the requested rows
            y = int(progress * h)
            for dy, row in enumerate(data[y: min(y + num_rows, h), :]):
                for x, val in enumerate(row):
                    val = int(val)
                    if val > 7:
                        print(val)
                    file.write(val.to_bytes(2, byteorder))
                    # Write any extra data
                    bytes_ = get_from_dict(x, y + dy, extra_data)
                    if bytes_ is not None:
                        file.write(bytes_)
            return (y + num_rows) / h
    return 1


# Saves the which byte we are currently on when loading a world
current_byte = 0


# Load world
def load_world_part(progress, file, num_rows=1):
    global current_byte
    if isfile(file):
        # Open file
        with open(file, "rb") as world_data:
            data = world_data.read()
            # If it's the first time, read dimensions
            if progress == 0:
                w, h = int.from_bytes(data[:2], byteorder), int.from_bytes(data[2:4], byteorder)
                global world_spawn
                world_spawn = (int.from_bytes(data[4:6], byteorder), int.from_bytes(data[6:8], byteorder))
                global blocks
                blocks = full((h, w), AIR, dtype=int16)
                current_byte = 8
            # Get current height and data for that row
            current_y = int(progress * blocks.shape[0])
            data = data[current_byte:]
            # Write data to array
            for y in range(current_y, min(current_y + num_rows, blocks.shape[0])):
                for x in range(blocks.shape[1]):
                    val = int.from_bytes(data[:2], byteorder)
                    if val != AIR:
                        blocks[y][x] = val
                        # Save it if it is a spawner
                        if tiles[val].spawner:
                            update_dict(x, y, val, spawners)
                        # Check if we should be loading extra data
                        num_bytes = tiles[val].data_bytes
                        if num_bytes > 0:
                            update_dict(x, y, data[2:num_bytes], block_data)
                            data = data[num_bytes:]
                            current_byte += num_bytes
                    data = data[2:]
            # Increment our current byte by the number of bytes in each row
            current_byte += num_rows * blocks.shape[1] * 2
            return float((y + 1) / blocks.shape[0])
