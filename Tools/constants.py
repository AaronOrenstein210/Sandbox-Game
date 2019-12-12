# Created on 22 October 2019
# Contains all constant values for the project

# NO IMPORTING FROM INSIDE THIS PROJECT!!!!!!
from pygame.font import SysFont
from pygame.display import set_mode
from pygame.locals import RESIZABLE

# Dimension Constants
MIN_W, MIN_H = 800, 600
# Width of a block
BLOCK_W = 16
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
DAY_START = MS_PER_DAY // 4
NIGHT_START = MS_PER_DAY * 3

# Damage types
MELEE, RANGED, MAGIC, THROWING, SUMMONING = 0, 1, 2, 3, 4
# Ai types
RANDOM, FOLLOW, FLY = 0, 1, 2

# Fonts
inv_font, load_font, ui_font = None, None, None


def load_fonts():
    global inv_font, load_font, ui_font
    inv_font = get_scaled_font(INV_W, INV_W // 3, "_" * 3, "Times New Roman")
    load_font = get_scaled_font(MIN_W // 2, MIN_H // 10, "_" * 25, "Times New Roman")
    ui_font = get_scaled_font(MIN_W // 3, MIN_H // 20, "_" * 30, "Times New Roman")


def resize(w, h):
    set_mode((max(w, MIN_W), max(h, MIN_H)), RESIZABLE).fill(BACKGROUND)


# Gets the biggest font that fits the text within max_w and max_h
def get_scaled_font(max_w, max_h, text, font_name):
    font_size = 0
    font = SysFont(font_name, font_size)
    w, h = font.size(text)
    while (w < max_w or max_w == -1) and (h < max_h or max_h == -1):
        font_size += 1
        font = SysFont(font_name, font_size)
        w, h = font.size(text)
    return SysFont(font_name, font_size - 1)


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
