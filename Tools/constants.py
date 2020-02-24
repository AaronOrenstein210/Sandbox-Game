# Created on 22 October 2019
# Contains all constant values for the project

# NO IMPORTING FROM INSIDE THIS PROJECT!!!!!!
import pygame as pg
import math
from random import randint

# Dimension Constants
MIN_W, MIN_H = 800, 600
# Width of a block
BLOCK_W = 16
# Width of the minimap
MAP_W = min(MIN_W // 4, MIN_H // 3)
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
# 1000 ms/s * 60 s/min
MS_PER_MIN = 60000
# 1000 ms/s * 60 s/min * 24 min/day
MS_PER_DAY = MS_PER_MIN * 24
NOON = MS_PER_DAY // 2
# 1000 ms/s * 60 s/min * 18 min
DAY_START = MS_PER_MIN * 6
NIGHT_START = MS_PER_MIN * 18

# Damage types
MELEE, RANGED, MAGIC, THROWING, SUMMONING = 0, 1, 2, 3, 4
# Ai types
RANDOM, FOLLOW, FLY = 0, 1, 2

# Fonts
pg.init()
# Inventory font, Loading screen font, UI font
inv_font = load_font = ui_font = None


def load_fonts():
    global inv_font, load_font, ui_font
    inv_font = get_scaled_font(INV_W, INV_W // 3, "999")
    load_font = get_scaled_font(-1, MIN_H // 15, "|")
    ui_font = get_scaled_font(-1, INV_W * 2 // 5, "|")


def resize(w, h):
    pg.display.set_mode((max(w, MIN_W), max(h, MIN_H)), pg.RESIZABLE).fill(BACKGROUND)


# Returns angle from start to end
def get_angle(start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    r = math.sqrt(dx * dx + dy * dy)
    if r == 0:
        return 0
    else:
        theta = math.asin(dy/r)
        if dx < 0:
            theta = math.pi - theta
        return theta


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
