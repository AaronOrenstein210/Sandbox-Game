# Created on 24 November 2019
# Allows the user to selct a player and world and create new ones

from os import listdir, remove, mkdir
from os.path import isfile, isdir
from shutil import rmtree
from sys import exit
import pygame as pg
from pygame.locals import *
from Tools.constants import MIN_W, MIN_H
from Tools import constants as c
from World import create_new_world
from Tools.UIOperations import get_input, ask_yes_no
from Player.Player import create_new_player

IMG = "res/images/"
SCROLL_BKGROUND = (0, 0, 128)
ITEM_W, ITEM_H = MIN_W // 2, MIN_H // 10
SCROLL_AMNT = ITEM_H // 3
PLAYER, UNIVERSE, WORLD = 0, 1, 2
path, ext = "saves/", ""


# Load all saved players and worlds
# Returns list of files
def load_files(what):
    data = []
    for name in listdir(path):
        if what != UNIVERSE and name.endswith(ext):
            data.append(trim_file_name(name))
        elif isdir(path + name) and isfile(path + name + "/" + name + ".wld"):
            data.append(name)
    return data


# Draw ui, returns scroll surface
def draw_surface(data, item_rects):
    surface = pg.Surface((ITEM_W, ITEM_H * len(data)))
    item_rects.clear()
    button_w = ITEM_H // 2
    for idx, text in enumerate(data):
        choose = Rect(0, ITEM_H * idx, button_w, button_w)
        trash = choose.move(0, button_w)
        text = c.load_font.render(text, 1, (255, 255, 255))
        text_rect = text.get_rect(center=((ITEM_W + button_w) // 2, ITEM_H * (idx + .5)))
        surface.blit(text, text_rect)
        surface.blit(pg.transform.scale(pg.image.load(IMG + "play.png"), choose.size), choose)
        surface.blit(pg.transform.scale(pg.image.load(IMG + "delete.png"), trash.size), trash)
        item_rects.append([choose, trash])
    return surface


# Selection screen
def run_selector(what, universe=""):
    display = pg.display.get_surface()

    global path, ext
    if what == PLAYER:
        path = "saves/players/"
        ext = ".plr"
    elif what == UNIVERSE:
        path = "saves/universes/"
    elif what == WORLD:
        path = "saves/universes/" + universe + "/"
        ext = ".wld"

    # Stores each item's rect
    item_rects = []
    # Offset of scroller
    off = 0

    # Get data
    data = load_files(what)
    # Draw scroller surface
    surface = draw_surface(data, item_rects)
    # Establish rectangles
    rect, new_rect = Rect(0, ITEM_H, ITEM_W, ITEM_H), Rect(0, 0, ITEM_H, ITEM_H)

    def redraw():
        w, h = display.get_size()
        rect.h = h - (3 * ITEM_H)
        rect.centerx = w // 2
        draw_scroll()
        if what != WORLD:
            new_rect.y = rect.bottom
            new_rect.centerx = w // 2
            display.blit(pg.transform.scale(pg.image.load(IMG + "add.png"), new_rect.size), new_rect)
        return min(0, rect.h - surface.get_size()[1])

    def draw_scroll():
        display.fill(SCROLL_BKGROUND, rect)
        display.blit(surface, rect.move(0, off))
        pg.draw.rect(display, (0, 0, 0), rect, 2)

    # Get maximum scrolling
    off_max = redraw()
    while True:
        for e in pg.event.get():
            # Quit
            if e.type == QUIT:
                quit()
                exit(0)
            # Resize
            elif e.type == VIDEORESIZE:
                c.resize(e.w, e.h)
                off = 0
                off_max = redraw()
            # Any mouse action
            elif e.type == MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()
                # If it happened in this rect
                if rect.collidepoint(*pos):
                    pos = (pos[0] - rect.x, pos[1] - rect.y)
                    # Scroll up
                    if e.button == BUTTON_WHEELUP:
                        off = max(off_max, min(0, off + SCROLL_AMNT))
                    # Scroll down
                    elif e.button == BUTTON_WHEELDOWN:
                        off = max(off_max, min(0, off - SCROLL_AMNT))
                    # Click
                    elif e.button == BUTTON_LEFT:
                        idx = (pos[1] - off) // ITEM_H
                        if idx >= len(item_rects):
                            continue
                        # Check if we chose that item
                        if item_rects[idx][0].collidepoint(*pos):
                            return data[idx]
                        elif item_rects[idx][1].collidepoint(*pos):
                            if ask_yes_no("Delete " + data[idx] + "?", redraw_background=redraw):
                                if what != UNIVERSE:
                                    remove(path + data[idx] + ext)
                                else:
                                    rmtree(path + data[idx])
                                data = load_files(what)
                                surface = draw_surface(data, item_rects)
                            off_max = redraw()
                elif what != WORLD and new_rect.collidepoint(*pos):
                    result = get_input("Input Name", char_limit=10, redraw_background=redraw)
                    if result is not None:
                        if what == PLAYER:
                            create_new_player(result)
                        elif what == WORLD:
                            create_new_world(universe, result)
                        else:
                            mkdir(path + result)
                            create_new_world(result, result)
                        data = load_files(what)
                        surface = draw_surface(data, item_rects)
                    off_max = redraw()
        pg.display.flip()


# Trim the file name
def trim_file_name(name):
    return name[:name.rfind(".")]
