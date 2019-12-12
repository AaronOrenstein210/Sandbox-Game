# Created on 9 December 2019

import pygame as pg
from pygame.locals import *
from Tools import objects as o


class ActiveUI:
    def __init__(self, ui, rect, pos=(-1, -1)):
        self.ui, self.rect = ui, rect
        # Used if it is tied to a block
        self.block_pos = list(pos)

    # Override these if implementing a UI
    # Called when the screen is resized
    def on_resize(self):
        return

    # Remove events if they should not be used
    # Set a specific key of button to be false if it shouldn't be used further
    def process_events(self, events, mouse, keys):
        return
