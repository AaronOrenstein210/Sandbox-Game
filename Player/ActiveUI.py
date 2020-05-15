# Created on 9 December 2019

import pygame as pg
from pygame.locals import BUTTON_LEFT, BUTTON_RIGHT
from Tools import game_vars


class ActiveUI:
    def __init__(self, ui, rect, pos=(-1, -1)):
        self.ui, self.rect = ui, rect
        # Used if it is tied to a block
        self.block_pos = list(pos)
        # Can we drag this ui
        self.can_drag = True

    # Called on exit
    def on_exit(self):
        pass

    # Override these if implementing a UI
    # Called when the screen is resized
    def on_resize(self):
        pass

    # Returns any inventories this ui has
    def get_inventories(self):
        return []

    # Called whenever one of the inventories returned by get_inventories()
    # picks up an item (this is otherwise undetectable)
    def on_inv_pickup(self):
        pass

    # This is called every tick no matter what
    # Events not dependent on user inputs should happen here
    def tick(self):
        pass

    # Checks all the inventories, return if any of them were clicked
    def click_inventories(self, mouse):
        # Make sure the player can click and we did click
        if game_vars.player.use_time <= 0 and (mouse[BUTTON_LEFT - 1] or mouse[BUTTON_RIGHT - 1]):
            pos = pg.mouse.get_pos()
            # Check if we clicked our ui
            if self.rect.collidepoint(*pos):
                pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
                # Check if we clicked any inventories
                for inv in self.get_inventories():
                    if inv.rect.collidepoint(*pos):
                        pos = [pos[0] - inv.rect.x, pos[1] - inv.rect.y]
                        # Perform the click
                        if mouse[BUTTON_LEFT - 1]:
                            inv.left_click(pos)
                        else:
                            inv.right_click(pos)
                        return True
        return False

    # Remove events if they should not be used
    # Set a specific key of button to be false if it shouldn't be used further
    # This is not called if the user is dragging the ui
    def process_events(self, events, mouse, keys):
        pass

    # Draws stored surface, automatically draws all inventories returned
    # by get_inventories()
    def draw(self):
        d = pg.display.get_surface()
        if self.ui:
            d.blit(self.ui, self.rect)
        pos = pg.mouse.get_pos()
        for inv in self.get_inventories():
            inv.draw(pos, parent_pos=self.rect.topleft)
