# Created on 8 December 2019
# Defines the class for ui operations

import pygame as pg


class UIOperation:
    # on_finish() must take the result of check_events as its first input
    def __init__(self):
        self.surface, self.rect = None, None

    def check_events(self, events):
        return

    def run_now(self):
        should_draw = self.surface is not None and self.rect is not None
        result = self.check_events(pg.event.get())
        while result is None:
            result = self.check_events(pg.event.get())
            if should_draw:
                pg.display.get_surface().blit(self.surface, self.rect)
            pg.display.flip()
        return result
