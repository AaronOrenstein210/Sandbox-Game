# Created on 11 November 2019
# Blocks are items that can be placed in the world

from os.path import isfile
from pygame.draw import rect as draw_rect
from pygame.transform import scale
from pygame.image import load
from Databases.constants import BLOCK_W
from Objects.Item import Item


class Block(Item):
    def __init__(self, idx, name="No Name", hardness=0, max_stack=999, amnt=1,
                 inv_img=""):
        Item.__init__(self, idx, name, amnt, max_stack, .3, True)
        self.placeable = True
        self.hardness = hardness
        # Load image if available
        if isfile(inv_img):
            self.image = scale(load(inv_img), (BLOCK_W, BLOCK_W))
            draw_rect(self.image, (0, 0, 0), self.image.get_rect(), 1)

    def get_icon_display(self, w):
        return scale(self.image, (w * 2 // 3, w * 2 // 3))

    def clone(self, amnt):
        return Block(self.idx, self.name, self.hardness, amnt=amnt)
