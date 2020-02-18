# Created on 22 December 2019

from os import remove
import pygame as pg
from zipfile import ZipFile
from Tools import objects as o


# Generic animations, goes through list of frames
class Animation:
    def __init__(self, gif, dim, delay=100):
        self.frames = []
        # Load frames
        with ZipFile(gif, "r") as file:
            for name in file.namelist():
                file.extract(name)
                if name.endswith(".png"):
                    self.frames.append(pg.transform.scale(pg.image.load(name), dim))
                remove(name)
        self.frame_delay = delay
        self.idx = 0
        self.time = 0

    def update(self):
        self.time += o.dt
        if self.time >= self.frame_delay:
            self.idx = (self.idx + self.time // self.frame_delay) % len(self.frames)
            self.time %= self.frame_delay

    def get_frame(self):
        return self.frames[self.idx]


# This animations goes forwards and backwards through the list of frames
class OscillateAnimation(Animation):
    def __init__(self, **kwargs):
        Animation.__init__(self, **kwargs)
        self.forwards = True

    def update(self):
        self.time += o.dt
        if self.time >= self.frame_delay:
            self.idx += 1 if self.forwards else -1
            if (self.idx == len(self.frames) - 1 and self.forwards) or \
                    (self.idx == 0 and not self.forwards):
                self.forwards = not self.forwards
            self.time %= self.frame_delay
