# Created on 22 November 2019
# Used to determine the various spawn conditions around a specific block

from NPCs import conditions as con
from Tools.constants import DAY_START, NIGHT_START
from Tools import game_vars


class SpawnConditions:
    def __init__(self):
        self.conditions = {}

    def check_world(self):
        self.conditions[con.DAY] = DAY_START <= game_vars.world.time < NIGHT_START
        self.conditions[con.NIGHT] = not self.conditions[con.DAY]

    def check_area(self, pos, r):
        self.conditions[con.SURFACE] = pos[1] >= 0
        self.conditions[con.UNDERGROUND] = pos[1] >= 0
