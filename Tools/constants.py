# Created on 22 October 2019
# Contains all constant values for the project

# NO IMPORTING FROM INSIDE THIS PROJECT!!!!!!
from os import listdir
from os.path import isfile, isdir
import pygame as pg
import math
from random import randint

# Acceptable error due to rounding
ROUND_ERR = 1e-10

# Dimension Constants
MIN_W, MIN_H = 800, 600
# Width of a block
BLOCK_W = 16
# Width of the minimap
MAP_W = min(MIN_W // 4, MIN_H // 3)
# Max dimension of map sprites
SPRITE_W = MAP_W // 15
# Width of an item on the ground
ITEM_W = BLOCK_W * 3 // 4
# Width of an inventory slot
INV_W = min(MIN_W // 20, MIN_H // 10)
# Width of an image in the inventory
INV_IMG_W = INV_W * 4 // 5

# Misc. Constants
MAX_FALL_SPEED = 10
BACKGROUND = (0, 128, 128)

# Time Constants
# 60 s/min * 24 min/day
SEC_PER_DAY = 60 * 24
NOON = SEC_PER_DAY // 2
# 60 s/min * 18 min
DAY_START = 60 * 6
NIGHT_START = 60 * 18

# Damage types
MELEE, RANGED, MAGIC, THROWING, SUMMONING = range(5)
# Ai types
RANDOM, FOLLOW, FLY = range(3)

# Save paths
PLR = "save/player/"
WLD = "save/universe/"

# Inventory font, Loading screen font, UI font
inv_font = load_font = ui_font = None

# Screen width, height, and center
screen_w = screen_h = 0
screen_center = [MIN_W // 2, MIN_H // 2]


def load_fonts():
    global inv_font, load_font, ui_font
    inv_font = get_scaled_font(INV_W, INV_W // 3, "999")
    load_font = get_scaled_font(-1, MIN_H // 15, "|")
    ui_font = get_scaled_font(-1, INV_W * 2 // 5, "|")


def load_image(file, w, h):
    if isfile(file) and (file.endswith(".png") or file.endswith(".jpg")):
        return scale_to_fit(pg.image.load(file), w=w, h=h)
    else:
        return pg.Surface((w, h))


def resize(w, h):
    global screen_w, screen_h, screen_center
    screen_w, screen_h = max(w, MIN_W), max(h, MIN_H)
    # Set the new screen dimensions and get screen center
    screen_center = pg.display.set_mode((screen_w, screen_h), pg.RESIZABLE).fill(BACKGROUND).center


# Returns angle from start to end
# Note: pixel angle and -sin = normal angle and +sin
# In other words, you don't need to get the pixel angle for trig, just if the angle has other meaning
def get_angle(start, end, pixels=False):
    dx, dy = end[0] - start[0], end[1] - start[1]
    # Flip y for pixel coordinates
    if pixels:
        dy *= -1
    r = math.sqrt(dx * dx + dy * dy)
    if r == 0:
        return 0
    else:
        theta = math.asin(dy / r)
        if dx < 0:
            theta = math.pi - theta
        return theta % (2 * math.pi)


def distance(p1, p2):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    return math.sqrt(dx ** 2 + dy ** 2)


# Resizes surface to fit within desired dimensions, keeping surface's w:h ratio
def scale_to_fit(s, w=-1, h=-1):
    if w == -1 and h == -1:
        return s
    dim = s.get_size()
    if w == -1:
        frac = h / dim[1]
    elif h == -1:
        frac = w / dim[0]
    else:
        frac = min(w / dim[0], h / dim[1])
    return pg.transform.scale(s, (int(frac * dim[0]), int(frac * dim[1])))


def random_sign():
    return 1 if randint(0, 1) == 0 else -1


def grey_scale(s):
    arr = pg.surfarray.array3d(s)
    arr = arr.dot([0.298, 0.587, 0.114])[:, :, None].repeat(3, axis=2)
    return pg.surfarray.make_surface(arr)


# Gets the biggest font size that fits the text within max_w and max_h
def get_scaled_font(max_w, max_h, text, font_name="Times New Roman"):
    font_size = 1
    font = pg.font.SysFont(font_name, font_size)
    w, h = font.size(text)
    min_size = max_size = 1
    while (max_w == -1 or w < max_w) and (max_h == -1 or h < max_h):
        font_size *= 2
        min_size = max_size
        max_size = font_size
        font = pg.font.SysFont(font_name, font_size)
        w, h = font.size(text)
    if font_size == 1:
        return font
    while True:
        font_size = (max_size + min_size) // 2
        font = pg.font.SysFont(font_name, font_size)
        w, h = font.size(text)
        # Too small
        if (max_w == -1 or w < max_w) and (max_h == -1 or h < max_h):
            # Check if the next size is too big
            font_ = pg.font.SysFont(font_name, font_size + 1)
            w, h = font_.size(text)
            if (max_w == -1 or w < max_w) and (max_h == -1 or h < max_h):
                min_size = font_size + 1
            else:
                return font
        # Too big
        else:
            # Check if the previous size is too small
            font_ = pg.font.SysFont(font_name, font_size - 1)
            w, h = font_.size(text)
            if (max_w == -1 or w < max_w) and (max_h == -1 or h < max_h):
                return font
            else:
                max_size = font_size - 1


def get_widest_string(strs, font_name="Times New Roman"):
    biggest = ""
    last_w = 0
    font = pg.font.SysFont(font_name, 12)
    for string in strs:
        if font.size(string)[0] > last_w:
            biggest = string
            last_w = font.size(string)[0]
    return biggest


def wrap_text(string, font, w):
    words = string.split(" ")
    strs = []
    line = ""
    i = 0
    # Go through each word
    while i < len(words):
        # Get the new line and check its width
        temp = line + (" " if line != "" else "") + words[i]
        # If it fits, go to the next word
        if font.size(temp)[0] < w:
            line = temp
            i += 1
        # If it doesn't and our line has other words, add the line
        elif line != "":
            strs.append(line)
            line = ""
        # Otherwise the word doesn't fit in one line so break it up
        else:
            wrap = wrap_string(temp, font, w)
            for text in wrap[:-1]:
                strs.append(text)
            if i < len(words) - 1:
                line = wrap[len(wrap) - 1]
            else:
                strs.append(wrap[len(wrap) - 1])
            i += 1
    strs.append(line)
    return strs


def wrap_string(string, font, w):
    strs = []
    text = ""
    for char in string:
        if font.size(text + char)[0] >= w:
            strs.append(text)
            text = ""
        text += char
    return strs


def remove_from_dict(x, y, dictionary):
    if x in dictionary.keys() and y in dictionary[x].keys():
        dictionary[x].pop(y)
        if len(dictionary[x]) == 0:
            dictionary.pop(x)


def update_dict(x, y, val, dictionary):
    if x not in dictionary.keys():
        dictionary[x] = {}
    dictionary[x][y] = val


def get_from_dict(x, y, dictionary):
    if x in dictionary.keys() and y in dictionary[x].keys():
        return dictionary[x][y]


# Handles creating a player file name
class PlayerFile:
    def __init__(self, name=""):
        self.name = name
        self.extension = ".plr"
        self.path = "saves/players/"

    @property
    def file_name(self):
        return self.name.replace(" ", "_")

    @property
    def full_file(self):
        return self.path + self.file_name + self.extension

    @property
    def valid(self):
        return self.name.count(" ") != len(self.name) and not isfile(self.full_file)

    def type_char(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_BACKSPACE:
                self.name = self.name[:-1]
            elif len(self.name) < 20:
                if event.key == pg.K_SPACE:
                    self.name += " "
                else:
                    char = event.unicode
                    if char.isalpha() and len(char) == 1:
                        self.name += char
                    elif char.isnumeric():
                        self.name += char


# Handles creating a world file name
class WorldFile(PlayerFile):
    def __init__(self, universe, **kwargs):
        super().__init__(**kwargs)
        self.extension = ".wld"
        self.path = "saves/universes/{}/".format(universe)
        self.universe = universe


# Handles creation of a new universe folder name
class UniverseFolder(PlayerFile):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.extension = "/"
        self.path = "saves/universes/"

    @property
    def file_name(self):
        return self.name

    @property
    def valid(self):
        return self.name.count(" ") != len(self.name) and not isdir(self.full_file)
