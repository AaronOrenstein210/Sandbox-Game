# Created on 9 December 2019

import pygame as pg


class ActiveUI:
    def __init__(self, ui, rect, pos=(-1, -1), invs=None):
        self.ui, self.rect = ui, rect
        # Used if it is tied to a block
        self.block_pos = list(pos)
        # Can we drag this ui
        self.can_drag = True
        # Stores any inventories
        if invs is None:
            self.invs = {}
        else:
            self.invs = invs

    # Called on exit
    def on_exit(self):
        pass

    # Override these if implementing a UI
    # Called when the screen is resized
    def on_resize(self):
        pass

    # This is called every tick no matter what
    # Events not dependent on user inputs should happen here
    def tick(self):
        pass

    # Remove events if they should not be used
    # Set a specific key of button to be false if it shouldn't be used further
    # This is not called if the user is dragging the ui
    def process_events(self, events, mouse, keys):
        pass

    # Draws stored surface
    def draw(self):
        pg.display.get_surface().blit(self.ui, self.rect)
        self.draw_inventories()

    # Handles mouse hovering over item in inventory
    def draw_inventories(self):
        pos = pg.mouse.get_pos()
        if self.rect.collidepoint(*pos):
            ui_pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
            for inv in self.invs.values():
                if inv.rect.collidepoint(*ui_pos):
                    inv_pos = [ui_pos[0] - inv.rect.x, ui_pos[1] - inv.rect.y]
                    inv.draw_hover_item(inv_pos)
