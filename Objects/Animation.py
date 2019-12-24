# Created on 22 December 2019

from os.path import isfile
from pygame.transform import scale
from pygame.image import load


class Animation:
    def __init__(self, frames, dim, delay=100):
        self.frames = [f for f in frames if isfile(f)]
        self.frame_delay = delay
        self.dim = dim
        self.idx = 0
        self.time = 0

    def get_frame(self, dt):
        self.time += dt
        if self.time >= self.frame_delay:
            self.idx = (self.idx + self.time // self.frame_delay) % len(self.frames)
            self.time %= self.frame_delay
            return scale(load(self.frames[self.idx]), self.dim)
