# Created on 23 November 2019
# Shows a loading screen while executing a certain function

import pygame as pg
from pygame.locals import *
from Tools import constants as c

IMG = "res/images/"
msg = ""


def def_loading_bar(progress):
    # Get dimensions of ui components
    load_rect, bar_rect = get_ui_dimensions()
    display = pg.display.get_surface()
    # Reset surface
    display.fill(c.BACKGROUND)
    # Progress ellipses
    dots = int(pg.time.get_ticks() / 400) % 4
    text = c.load_font.render(msg + ("." * int(dots)), 1, (255, 255, 255))
    text_rect = text.get_rect(center=load_rect.center)
    display.blit(text, text_rect)
    # Redraw progress bar
    pg.draw.rect(display, (255, 0, 0), Rect(bar_rect.x, bar_rect.y, bar_rect.w * progress, bar_rect.h))
    pg.draw.rect(display, (0, 0, 0), bar_rect, 2)


def get_ui_dimensions():
    # Get display size
    w, h = pg.display.get_surface().get_size()
    text_w, text_h = c.load_font.size(msg + "...")
    # Calculate rects for ui components
    load_rect = Rect(0, 0, text_w, text_h)
    load_rect.centerx, load_rect.bottom = w // 2, (h - text_h) // 2
    bar_rect = Rect(0, 0, c.MIN_W // 2, text_h)
    bar_rect.centerx, bar_rect.top = w // 2, (h + text_h) // 2
    return load_rect, bar_rect


# Complete a task with loading screen
def complete_task(task, task_args=(), message="Loading", can_exit=True, update_ui=def_loading_bar):
    global msg
    msg = message
    # Keep track of our progress
    progress = 0
    while True:
        for e in pg.event.get():
            # Check if we hit exit
            if can_exit and e.type == QUIT:
                return False
            # Check if we resized the screen
            elif e.type == VIDEORESIZE:
                c.resize(e.w, e.h)

        # Perform the task
        progress = task(progress, *task_args)
        if progress is None:
            return False

        # Update ui
        update_ui(progress)
        pg.display.flip()

        if progress >= 1:
            return True


# Generic input box (text)
def get_input(prompt, char_limit=-1, redraw_background=None, redraw_args=()):
    display = pg.display.get_surface()
    # Dimensions
    w, line_h = c.MIN_W // 3, c.MIN_H // 10
    # Set up text for the prompt
    prompt = c.wrap_text(prompt, c.load_font, w)
    if len(prompt) > 3:
        prompt = prompt[:3]
        if c.load_font.size(prompt[-1] + "...")[0] < w:
            prompt[-1] += "..."
        else:
            prompt[-1] = prompt[-1][:-3] + "..."
    # Create main surface and recangles
    surface = pg.Surface((w, line_h * (len(prompt) + 2)))
    s_rect = surface.get_rect()
    box_rect = pg.Rect(0, len(prompt) * line_h, w, line_h)
    margin = (w - (2 * line_h)) // 3
    done_rect = pg.Rect(margin, box_rect.bottom, line_h, line_h)
    quit_rect = done_rect.move(line_h + margin, 0)
    # Draw prompt and exit buttons
    for idx, line in enumerate(prompt):
        text = c.load_font.render(line, 1, (255, 255, 255))
        text_rect = text.get_rect(center=(w // 2, (idx + .5) * line_h))
        surface.blit(text, text_rect)
    surface.blit(pg.transform.scale(pg.image.load(IMG + "confirm.png"), done_rect.size), done_rect)
    surface.blit(pg.transform.scale(pg.image.load(IMG + "cancel.png"), quit_rect.size), quit_rect)
    string = ""

    # Resize screen
    def redraw():
        if redraw_background is not None:
            redraw_background(*redraw_args)
        s_rect.center = display.get_rect().center
        display.blit(surface, s_rect)
        draw_text()

    # Draw inputted text
    def draw_text():
        r = box_rect.move(*s_rect.topleft)
        pg.draw.rect(display, (128, 128, 128), r)
        text_ = c.load_font.render(string, 1, (255, 255, 255))
        display.blit(text_, text_.get_rect(center=r.center))
        pg.draw.rect(display, (0, 0, 0), r, 2)

    redraw()
    while True:
        for e in pg.event.get():
            # Resize
            if e.type == VIDEORESIZE:
                c.resize(e.w, e.h)
                pg.display.get_surface().fill(c.BACKGROUND)
                redraw()
            # Key pressed
            elif e.type == KEYDOWN:
                # Delete las character
                if e.key == K_BACKSPACE:
                    string = string[:-1]
                elif e.key == K_SPACE:
                    string += " "
                # Add single character
                elif len(pg.key.name(e.key)) == 1 and (char_limit == -1 or len(string) < char_limit):
                    string += e.unicode
                draw_text()
            # Clicks
            elif e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                pos = pg.mouse.get_pos()
                if s_rect.collidepoint(pos):
                    pos = (pos[0] - s_rect.x, pos[1] - s_rect.y)
                    if done_rect.collidepoint(*pos) and len(string) > 0:
                        return string
                    elif quit_rect.collidepoint(*pos):
                        return None
        pg.display.flip()


# Asks yes/no question
def ask_yes_no(prompt, redraw_background=None, redraw_args=()):
    # Dimensions
    w, line_h = c.MIN_W // 3, c.MIN_H // 10
    # Set up text for the prompt
    prompt = c.wrap_text(prompt, c.load_font, w)
    if len(prompt) > 3:
        prompt = prompt[:3]
        if c.load_font.size(prompt[-1] + "...")[0] < w:
            prompt[-1] += "..."
        else:
            prompt[-1] = prompt[-1][:-3] + "..."
    # Create main surface and recangles
    surface = pg.Surface((w, line_h * (len(prompt) + 1)))
    s_rect = surface.get_rect()
    # Draw prompt
    for idx, line in enumerate(prompt):
        text = c.load_font.render(line, 1, (255, 255, 255))
        text_rect = text.get_rect(center=(w // 2, (idx + .5) * line_h))
        surface.blit(text, text_rect)
    # Get text dimenstion
    yes_dim, no_dim = c.load_font.size("yes"), c.load_font.size("no")
    dim = [yes_dim[0] + no_dim[0], max(yes_dim[1], no_dim[1])]
    margin = (w - dim[0]) // 3
    # Make yes/no rectangles
    yes_rect = pg.Rect(margin, 0, yes_dim[0], dim[1])
    yes_rect.centery = s_rect.h - (line_h // 2)
    no_rect = yes_rect.move(yes_dim[0] + margin, 0)
    # Draw yes text
    pg.draw.rect(surface, (0, 200, 0), yes_rect)
    yes_text = c.load_font.render("yes", 1, (255, 255, 255))
    yes_text_rect = yes_text.get_rect(center=yes_rect.center)
    surface.blit(yes_text, yes_text_rect)
    # Draw no text
    pg.draw.rect(surface, (200, 0, 0), no_rect)
    no_text = c.load_font.render("no", 1, (255, 255, 255))
    no_text_rect = no_text.get_rect(center=no_rect.center)
    surface.blit(no_text, no_text_rect)

    # Resize screen
    def redraw():
        if redraw_background is not None:
            redraw_background(*redraw_args)
        s_rect.center = display.get_rect().center
        display.blit(surface, s_rect)

    redraw()
    while True:
        for e in pg.event.get():
            if e.type == VIDEORESIZE:
                display = pg.display.set_mode((max(e.w, c.MIN_W), max(e.h, c.MIN_H)), RESIZABLE)
                display.fill(c.BACKGROUND)
                redraw()
            elif e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                pos = pg.mouse.get_pos()
                pos = (pos[0] - s_rect.x, pos[1] - s_rect.y)
                if yes_rect.collidepoint(*pos):
                    return True
                elif no_rect.collidepoint(*pos):
                    return False
        pg.display.flip()
