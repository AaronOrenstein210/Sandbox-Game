from os.path import isfile
from sys import byteorder
from numpy import full, int16
from Tools import constants as c
from Tools.lists import items
from World.WorldGenerator import generate_world
from Tools.UIOperations import complete_task

# Defines world zones
SURFACE, CAVE = 0, 0
# 1000 ms/s * 60 s/min
MS_PER_MIN = 60000
# 1000 ms/s * 60 s/min * 24 min/day
MS_PER_DAY = MS_PER_MIN * 24
NOON = MS_PER_DAY // 2
# 1000 ms/s * 60 s/min * 18 min
DAY_START = MS_PER_DAY // 4
NIGHT_START = MS_PER_DAY * 3
# Defines world sizes, (h, w)
SMALL, MED, LARGE = 0, 1, 2
world_dim = {SMALL: (300, 100), MED: (500, 300), LARGE: (1000, 500)}
# All blocks and spawners
blocks = None
spawners = {}
# World time
world_time = MS_PER_MIN * 10
# World spawn
world_spawn = [0, 0]


# Create new world
def create_new_world(universe, name):
    data = full(world_dim[LARGE], c.AIR_ID, dtype=int16)
    spawn = generate_world(data)
    file = "saves/universes/" + universe + "/" + name + ".wld"
    complete_task(save_world_part, task_args=[file, data, spawn], message="Creating new world",
                  can_exit=False)


# Load world
def load_world_part(progress, file, num_rows=1):
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
                blocks = full((h, w), c.AIR_ID, dtype=int16)
            # Get current height and data for that row
            current_y = int(progress * blocks.shape[0])
            data = data[8 + (current_y * 2 * blocks.shape[1]):]
            # Write data to array
            for y in range(current_y, min(current_y + num_rows, blocks.shape[0])):
                for x in range(blocks.shape[1]):
                    val = int.from_bytes(data[:2], byteorder)
                    if val != c.AIR_ID:
                        blocks[y][x] = val
                        # Save it if it is a spawner
                        if items[val].spawner:
                            add_spawner(x, y, val)
                    data = data[2:]
            return float((y + 1) / blocks.shape[0])


# Save world
def save_world_part(progress, file, data=None, spawn=None, num_rows=1):
    if data is None:
        data = blocks
    if spawn is None:
        spawn = world_spawn
    if data is not None:
        code = "wb+" if progress == 0 else "ab+"
        with open(file, code) as file:
            h, w = data.shape
            if progress == 0:
                file.write(w.to_bytes(2, byteorder))
                file.write(h.to_bytes(2, byteorder))
                file.write(spawn[0].to_bytes(2, byteorder))
                file.write(spawn[1].to_bytes(2, byteorder))
            y = int(progress * h)
            for row in data[y: min(y + num_rows, h), :]:
                for val in row:
                    val = int(val)
                    file.write(val.to_bytes(2, byteorder))
            return (y + num_rows) / h
    return 1


def get_day_color():
    return 0, 0, 255 * (1 - pow((world_time - NOON) / NOON, 2))


# Adding/removing spawners
def remove_spawner(x, y):
    if x in spawners.keys() and y in spawners[x].keys():
        spawners[x].pop(y)
        if len(spawners[x]) == 0:
            spawners.pop(x)


def add_spawner(x, y, item_id):
    if x not in spawners.keys():
        spawners[x] = {}
    spawners[x][y] = item_id
