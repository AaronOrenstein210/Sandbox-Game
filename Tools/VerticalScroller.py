# Created on 28 November 2019

from pygame import Surface, Rect


class VerticalScroller:
    def __init__(self, dim, background=(0, 0, 0)):
        self.background = background
        # Visible area
        self.dim = dim
        # Height of scroll surface
        self.h = 0
        # Scroll offset
        self.scroll, self.max_scroll = 0, 0
        # Saves y-pos and dimensions of current row and keys of items on current row
        self.row_y, self.row_dim, self.row_keys = 0, [0, 0], []
        self.rects = {}
        self.surface = Surface((0, 0))

    def do_scroll(self, up):
        if up:
            self.scroll = min(0, self.scroll + int(self.dim[1] / 10))
        else:
            self.scroll = max(self.max_scroll, self.scroll - int(self.dim[1] / 10))

    def add_item(self, s, key):
        item_dim = s.get_size()
        new_s = Surface((self.dim[0], self.h + item_dim[1]))
        new_s.blit(self.surface, (0, 0))
        self.rects[key] = s.get_rect(center=(self.dim[0] // 2, self.h + (item_dim[1] // 2)))
        new_s.blit(s, self.rects[key])
        self.surface = new_s
        self.h = self.surface.get_size()[1]
        self.max_scroll = min(0, self.dim[1] - self.h)

    def click(self, pos):
        pos = (pos[0], pos[1] - self.scroll)
        for key in self.rects.keys():
            if self.rects[key].collidepoint(pos):
                return key
        return ""
