# Created on 24 November 2019
# Allows the user to selct a player and world and create new ones

from os import listdir, remove
from sys import exit
from pygame import Surface, quit
from pygame.display import flip
from pygame.event import get
from pygame.mouse import get_pos
from pygame.draw import rect as draw_rect
from pygame.image import load
from pygame.transform import scale
from pygame.locals import *
from Databases.constants import MIN_W, MIN_H
from Databases import constants as c
from World import create_new_world
from HelpfulTools import get_input, ask_yes_no
from Player.Player import create_new_player

IMG = "res/images/"
SCROLL_BKGROUND = (0, 0, 128)
ITEM_W, ITEM_H = MIN_W // 2, MIN_H // 10
SCROLL_AMNT = ITEM_H // 3


# Load all saved players and worlds
# Returns list of files
def load_files(player):
    path = "saves/players/" if player else "saves/worlds"
    ext = ".plr" if player else ".wld"
    data = []
    for file in listdir(path):
        if file.endswith(ext):
            data.append(trim_file_name(file))
    return data


# Draw ui, returns scroll surface
def draw_surface(data, item_rects):
    surface = Surface((ITEM_W, ITEM_H * len(data)))
    item_rects.clear()
    button_w = ITEM_H // 2
    for idx, text in enumerate(data):
        choose = Rect(0, ITEM_H * idx, button_w, button_w)
        trash = choose.move(0, button_w)
        text = c.load_font.render(text, 1, (255, 255, 255))
        text_rect = text.get_rect(center=((ITEM_W + button_w) // 2, ITEM_H * (idx + .5)))
        surface.blit(text, text_rect)
        surface.blit(scale(load(IMG + "play.png"), choose.size), choose)
        surface.blit(scale(load(IMG + "delete.png"), trash.size), trash)
        item_rects.append([choose, trash])
    return surface


# Selection screen
def run_selector():
    player = ""
    # Stores each item's rect
    item_rects = []
    # Offset of scroller
    off = 0

    # Get data
    data = load_files(True)
    # Draw scroller surface
    surface = draw_surface(data, item_rects)
    # Establish rectangles
    rect, new_rect = Rect(0, ITEM_H, ITEM_W, ITEM_H), Rect(0, 0, ITEM_H, ITEM_H)

    def redraw():
        w, h = c.display.get_size()
        rect.h = h - (3 * ITEM_H)
        rect.centerx = w // 2
        new_rect.y = rect.bottom
        new_rect.centerx = w // 2
        draw_scroll()
        c.display.blit(scale(load(IMG + "add.png"), new_rect.size), new_rect)
        return min(0, rect.h - surface.get_size()[1])

    def draw_scroll():
        c.display.fill(SCROLL_BKGROUND, rect)
        c.display.blit(surface, rect.move(0, off))
        draw_rect(c.display, (0, 0, 0), rect, 2)

    # Get maximum scrolling
    off_max = redraw()
    while True:
        for e in get():
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
                pos = get_pos()
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
                            # Choose player
                            if player == "":
                                player = data[idx]
                                data = load_files(False)
                                surface = draw_surface(data, item_rects)
                                off_max = redraw()
                            # Choose world
                            else:
                                return player, data[idx]
                        elif item_rects[idx][1].collidepoint(*pos):
                            if ask_yes_no("Delete " + data[idx] + "?", redraw_background=redraw):
                                file = "saves/" + ("players/" if player == "" else "worlds/") + data[idx] + \
                                       (".plr" if player == "" else ".wld")
                                remove(file)
                                data = load_files(player == "")
                                surface = draw_surface(data, item_rects)
                            off_max = redraw()
                elif new_rect.collidepoint(*pos):
                    result = get_input("Input Name", char_limit=10, redraw_background=redraw)
                    if result is not None:
                        if player == "":
                            create_new_player(result)
                            data = load_files(True)
                        else:
                            create_new_world(result)
                            data = load_files(False)
                        surface = draw_surface(data, item_rects)
                    off_max = redraw()
        flip()


# Trim the file name
def trim_file_name(name):
    return name[name.rfind("/") + 1:name.rfind(".")]
