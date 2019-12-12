# Created on 22 November 2019
# Used to determine the various spawn conditions around a specific block

from NPCs.conditions import *
from Tools.constants import DAY_START, NIGHT_START
from Tools import objects as o


class SpawnConditions:
    def __init__(self):
        self.conditions = {}

    def check_world(self):
        self.conditions[DAY] = DAY_START <= o.world_time < NIGHT_START
        self.conditions[NIGHT] = not self.conditions[DAY]

    def check_area(self, pos, r):
        self.conditions[SURFACE] = pos[1] >= SURFACE
        self.conditions[UNDERGROUND] = pos[1] >= CAVE
