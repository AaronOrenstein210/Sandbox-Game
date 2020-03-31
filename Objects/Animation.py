# Created on 22 December 2019

from os import listdir
from os.path import isdir
import pygame as pg
from Tools.constants import scale_to_fit


# Generic animations, goes through list of frames
class Animation:
    def __init__(self, folder, dim, delay=.1):
        self.frames = []
        # Load frames
        if isdir(folder):
            for file in listdir(folder):
                if file.endswith(".png") or file.endswith(".jpg"):
                    self.frames.append(scale_to_fit(pg.image.load(folder + file), *dim))
        self.frame_delay = delay
        self.idx = self.time = 0

    def update(self, dt):
        self.time += dt
        if self.time >= self.frame_delay:
            self.idx = int((self.idx + self.time / self.frame_delay) % len(self.frames))
            self.time %= self.frame_delay

    def get_frame(self, **kwargs):
        return self.frames[self.idx]

    def reset(self):
        self.idx = self.time = 0


# This animations goes forwards and backwards through the list of frames
class OscillateAnimation(Animation):
    def __init__(self, **kwargs):
        Animation.__init__(self, **kwargs)
        self.forwards = True

    def update(self, dt):
        self.time += dt
        if self.time >= self.frame_delay:
            self.idx += 1 if self.forwards else -1
            if (self.idx == len(self.frames) - 1 and self.forwards) or \
                    (self.idx == 0 and not self.forwards):
                self.forwards = not self.forwards
            self.time %= self.frame_delay

    def reset(self):
        super().reset()
        self.forwards = True
