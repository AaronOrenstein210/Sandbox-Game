# Created on 8 December 2019

import pygame as pg
from pygame.locals import *
from UI.UIOperation import UIOperation
from Tools import constants as c


def loading_bar(progress, msg):
    display = pg.display.get_surface()
    display.fill(c.BACKGROUND)
    # Get display size
    w, h = display.get_size()
    text_w, text_h = c.load_font.size(msg + "...")
    # Calculate rects for ui components
    load_rect = pg.Rect(0, 0, text_w, text_h)
    load_rect.centerx, load_rect.bottom = w // 2, (h - text_h) // 2
    bar_rect = pg.Rect(0, 0, c.MIN_W // 2, text_h)
    bar_rect.centerx, bar_rect.top = w // 2, (h + text_h) // 2

    # Progress ellipses
    dots = int(pg.time.get_ticks() / 400) % 4
    text = c.load_font.render(msg + ("." * int(dots)), 1, (255, 255, 255))
    text_rect = text.get_rect(center=load_rect.center)
    display.blit(text, text_rect)
    # Redraw progress bar
    pg.draw.rect(display, (255, 0, 0), (bar_rect.x, bar_rect.y, bar_rect.w * progress, bar_rect.h))
    pg.draw.rect(display, (0, 0, 0), bar_rect, 2)


def percent(progress, msg):
    display = pg.display.get_surface()
    display.fill(c.BACKGROUND)
    # Get display size
    w, h = display.get_size()
    text_h = c.load_font.size("|")[1]
    # Calculate center of each text block
    load_c = [w // 2, (h // 2) - text_h]
    perc_c = [w // 2, (h // 2) + text_h]

    # Progress ellipses
    dots = int(pg.time.get_ticks() / 400) % 4
    text = c.load_font.render(msg + ("." * int(dots)), 1, (255, 255, 255))
    text_rect = text.get_rect(center=load_c)
    display.blit(text, text_rect)
    # Draw percent text
    text = c.load_font.render(str(int(progress * 100)) + "%", 1, (255, 255, 255))
    text_rect = text.get_rect(center=perc_c)
    display.blit(text, text_rect)


class CompleteTask(UIOperation):
    def __init__(self, task, task_args, draw_ui, draw_args, can_exit=True):
        UIOperation.__init__(self)
        self.progress = 0
        self.task = task
        self.task_args = task_args
        self.draw_ui = draw_ui
        self.draw_args = draw_args
        self.can_exit = can_exit

    def check_events(self, events):
        for e in events:
            # Check if we hit exit
            if self.can_exit and e.type == QUIT:
                return False
            # Check if we resized the screen
            elif e.type == VIDEORESIZE:
                c.resize(e.w, e.h)

        # Perform the task
        self.progress = self.task(self.progress, *self.task_args)
        if self.progress is None:
            return False

        if self.draw_ui:
            # Update ui
            self.draw_ui(self.progress, *self.draw_args)

        if self.progress >= 1:
            return True

    def reset(self):
        self.progress = 0


class LoadWorld(CompleteTask):
    def __init__(self, world):
        super().__init__(world.load_world, [], percent, ["Loading World Blocks"])

    def check_events(self, events):
        self.draw_args = ["Loading World Blocks"] if self.progress <= .5 else ["Drawing World"]
        return super().check_events(events)


class SaveWorld(CompleteTask):
    def __init__(self, world):
        super().__init__(world.save_world, [], percent, ["Saving World Blocks"], can_exit=False)

    def check_events(self, events):
        self.draw_args = ["Saving World Blocks"] if self.progress < .5 else ["Saving World Map"]
        return super().check_events(events)


class TextInput(UIOperation):
    IMG = "res/images/"

    def __init__(self, prompt, char_limit=-1, redraw_back=None, redraw_args=()):
        UIOperation.__init__(self)
        # Rectangles
        self.input_rect, self.done_rect, self.quit_rect = None, None, None
        self.input = ""
        self.char_limit = char_limit
        self.redraw_back = redraw_back
        self.redraw_args = redraw_args
        # Create display
        self.draw_surface(prompt)
        self.redraw()

    # Draw surface
    def draw_surface(self, prompt):
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
        # Create main surface and rectangles
        self.surface = pg.Surface((w, line_h * (len(prompt) + 2)))
        self.rect = self.surface.get_rect()
        self.input_rect = pg.Rect(0, len(prompt) * line_h, w, line_h)
        margin = (w - (2 * line_h)) // 3
        self.done_rect = pg.Rect(margin, self.input_rect.bottom, line_h, line_h)
        self.quit_rect = self.done_rect.move(line_h + margin, 0)
        # Draw prompt and exit buttons
        for idx, line in enumerate(prompt):
            text = c.load_font.render(line, 1, (255, 255, 255))
            text_rect = text.get_rect(center=(w // 2, (idx + .5) * line_h))
            self.surface.blit(text, text_rect)
        self.surface.blit(pg.transform.scale(pg.image.load(self.IMG + "confirm.png"), self.done_rect.size),
                          self.done_rect)
        self.surface.blit(pg.transform.scale(pg.image.load(self.IMG + "cancel.png"), self.quit_rect.size),
                          self.quit_rect)

    # Resize screen
    def redraw(self):
        display = pg.display.get_surface()
        if self.redraw_back is not None:
            self.redraw_back(*self.redraw_args)
        self.rect.center = display.get_rect().center
        self.draw_text()
        display.blit(self.surface, self.rect)

    # Draw inputted text
    def draw_text(self):
        pg.draw.rect(self.surface, (128, 128, 128), self.input_rect)
        text = c.load_font.render(self.input, 1, (255, 255, 255))
        self.surface.blit(text, text.get_rect(center=self.input_rect.center))
        pg.draw.rect(self.surface, (0, 0, 0), self.input_rect, 2)

    # Generic input box (text)
    def check_events(self, events):
        for e in events:
            # Resize
            if e.type == VIDEORESIZE:
                c.resize(e.w, e.h)
                pg.display.get_surface().fill(c.BACKGROUND)
            # Key pressed
            elif e.type == KEYDOWN:
                # Delete last character
                if e.key == K_BACKSPACE:
                    self.input = self.input[:-1]
                elif e.key == K_SPACE:
                    self.input += " "
                # Add single character
                elif len(pg.key.name(e.key)) == 1 and \
                        (self.char_limit == -1 or len(self.input) < self.char_limit):
                    self.input += e.unicode
            # Clicks
            elif e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                pos = pg.mouse.get_pos()
                if self.rect.collidepoint(pos):
                    pos = (pos[0] - self.rect.x, pos[1] - self.rect.y)
                    if self.done_rect.collidepoint(*pos) and len(self.input) > 0:
                        return self.input
                    elif self.quit_rect.collidepoint(*pos):
                        return ""
        self.redraw()


class YesNo(UIOperation):
    def __init__(self, prompt, redraw_back=None, redraw_args=()):
        UIOperation.__init__(self)
        # Yes/No rectangles
        self.yes_rect, self.no_rect = None, None
        self.redraw_back = redraw_back
        self.redraw_args = redraw_args
        # Create display
        self.draw_surface(prompt)
        self.redraw()

    def draw_surface(self, prompt):
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
        self.surface = pg.Surface((w, line_h * (len(prompt) + 1)))
        self.rect = self.surface.get_rect()
        # Draw prompt
        for idx, line in enumerate(prompt):
            text = c.load_font.render(line, 1, (255, 255, 255))
            text_rect = text.get_rect(center=(w // 2, (idx + .5) * line_h))
            self.surface.blit(text, text_rect)
        # Get text dimenstion
        yes_dim, no_dim = c.load_font.size("yes"), c.load_font.size("no")
        dim = [yes_dim[0] + no_dim[0], max(yes_dim[1], no_dim[1])]
        margin = (w - dim[0]) // 3
        # Make yes/no rectangles
        self.yes_rect = pg.Rect(margin, 0, yes_dim[0], dim[1])
        self.yes_rect.centery = self.rect.h - (line_h // 2)
        self.no_rect = self.yes_rect.move(yes_dim[0] + margin, 0)
        # Draw yes text
        pg.draw.rect(self.surface, (0, 200, 0), self.yes_rect)
        yes_text = c.load_font.render("yes", 1, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=self.yes_rect.center)
        self.surface.blit(yes_text, yes_text_rect)
        # Draw no text
        pg.draw.rect(self.surface, (200, 0, 0), self.no_rect)
        no_text = c.load_font.render("no", 1, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=self.no_rect.center)
        self.surface.blit(no_text, no_text_rect)

    # Resize screen
    def redraw(self):
        display = pg.display.get_surface()
        if self.redraw_back is not None:
            self.redraw_back(*self.redraw_args)
        self.rect.center = display.get_rect().center
        display.blit(self.surface, self.rect)

    # Asks yes/no question
    def check_events(self, events):
        for e in events:
            if e.type == VIDEORESIZE:
                c.resize(e.w, e.h)
            elif e.type == MOUSEBUTTONUP and e.button == BUTTON_LEFT:
                pos = pg.mouse.get_pos()
                pos = (pos[0] - self.rect.x, pos[1] - self.rect.y)
                if self.yes_rect.collidepoint(*pos):
                    return True
                elif self.no_rect.collidepoint(*pos):
                    return False
        self.redraw()
