# Created on 28 November 2019
# Used to move between dimensions

from os import listdir
from pygame import Surface
from pygame.draw import rect as draw_rect
from pygame.mouse import get_pos
from pygame.display import get_surface
from pygame.locals import *
from Objects.Block import Block
from Objects.Items import INV
from Tools.constants import MIN_W, MIN_H, CHANGE_WORLD
from Tools.VerticalScroller import VerticalScroller
from Tools import constants as c


class DimensionHopper(Block):
    def __init__(self, idx):
        Block.__init__(self, idx, name="Dimension Hopper", hardness=2, inv_img=INV + "spawn_1.png")
        self.clickable = True
        self.ui_rect = Rect(MIN_W // 4, MIN_H // 4, MIN_W // 2, MIN_H // 2)
        self.ui = Surface(self.ui_rect.size)
        self.scroller = None

    def activate(self):
        self.resize()
        self.ui = Surface(self.ui_rect.size)
        self.scroller = VerticalScroller(self.ui.get_size(), background=(0, 200, 128))

        font = c.get_scaled_font(self.ui_rect.w, int(self.ui_rect.h / 8), "_" * 25, "Times New Roman")
        for file in listdir("saves/universes/" + c.universe_name):
            if file.endswith(".wld"):
                name = file[:-4]
                text = font.render(name, 1, (255, 255, 255))
                self.scroller.add_item(text, name)

        self.ui.blit(self.scroller.surface, (0, 0))
        draw_rect(self.ui, (0, 0, 0), self.ui.get_rect(), 2)

    def process_event(self, event, item):
        if event.type == BUTTON_WHEELUP or event.type == BUTTON_WHEELDOWN:
            self.scroller.do_scroll(event.type == BUTTON_WHEELUP)
        elif event.type == MOUSEBUTTONUP and event.button == BUTTON_LEFT:
            pos = get_pos()
            if self.ui_rect.collidepoint(*pos):
                pos = (pos[0] - self.ui_rect.x, pos[1] - self.ui_rect.y)
                world = self.scroller.click(pos)
                if world != "":
                    c.world_name = world
                    c.game_state = CHANGE_WORLD
                    self.ui = None
            else:
                return True
        elif event.type == KEYUP and event.key == K_ESCAPE:
            self.ui = None
        else:
            return True
        return False

    def resize(self):
        self.ui_rect.center = get_surface().get_rect().center
