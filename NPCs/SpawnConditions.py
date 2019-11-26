# Created on 22 November 2019
# Used to determine the various spawn conditions around a specific block

from NPCs.conditions import *
import World as w


class SpawnConditions:
    def __init__(self):
        self.conditions = {}

    def check_world(self):
        self.conditions[DAY] = w.DAY_START <= w.world_time < w.NIGHT_START
        self.conditions[NIGHT] = not self.conditions[DAY]

    def check_area(self, pos, r):
        self.conditions[SURFACE] = pos[1] >= w.SURFACE
        self.conditions[UNDERGROUND] = pos[1] >= w.CAVE
