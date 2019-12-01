# Created on 23 November 2019
# SpawnBlocks are blocks that spawn enemies

from random import random
from Objects.Items import INV
from Objects.Block import Block
from Tools.constants import AIR_ID, BLOCK_W
import World as w


class SpawnBlock(Block):
    def __init__(self, idx, entity):
        self.entity = entity
        self.test_entity = entity()
        self.rarity = self.test_entity.rarity
        Block.__init__(self, idx, name=self.test_entity.name + " Spawner", hardness=self.rarity,
                       inv_img=INV + "spawner_" + str(self.rarity) + ".png")
        self.spawner = True

    def spawn(self, pos, conditions):
        conditions.check_area(pos, 5 * self.rarity)
        if not self.test_entity.can_spawn(conditions.conditions):
            return
        air = get_spawn_spaces(pos, 5 * self.rarity, self.test_entity.get_move_type())
        places = find_valid_spawns(air, *self.test_entity.dim)
        if len(places) > 0:
            chances = []
            for x_min, x_max, y in places:
                chances.append(x_max - x_min)
            num = random() * sum(chances)
            for idx, chance in enumerate(chances):
                if num < chance:
                    min_x, max_x, y = places[idx]
                    mob = self.entity()
                    x = min_x + (random() * (max_x - min_x - self.test_entity.dim[0]))
                    y = y - self.test_entity.dim[1]
                    mob.set_pos(x * BLOCK_W, y * BLOCK_W)
                    return mob
                else:
                    num -= chance


def get_spawn_spaces(center, r, walking):
    # X range
    v1_min, v1_max = max(0, center[0] - r), min(w.blocks.shape[1], center[0] + r)
    # Y bounds
    v2_min, v2_max = max(0, center[1] - r), max(0, center[1] + r)
    air = {}

    def add_val(v1_, v2_, val):
        if v1_ not in air.keys():
            air[v1_] = {}
        air[v1_][v2_] = val

    for v1 in range(v1_min, v1_max):
        air_count = 0
        v2 = 0
        for v2 in reversed(range(v2_min, v2_max)):
            block = w.blocks[v2][v1] if walking else w.blocks[v1][v2]
            if block != AIR_ID:
                if air_count > 0:
                    add_val(v1, v2 + air_count, air_count)
                air_count = 0
            else:
                air_count += 1
        if air_count > 0:
            add_val(v1, v2 + air_count, air_count)
    return air


def find_valid_spawns(air, dim1, dim2):
    # [(min_v1, max_v1, v2)]
    spawns = []
    v1_vals = air.keys()
    for v1 in v1_vals:
        min_v1 = v1
        v2_vals = air[v1].keys()
        for v2 in v2_vals:
            while v1 in v1_vals and v2 in air[v1].keys() and air[v1][v2] >= dim2:
                if v1 != min_v1:
                    air[v1].pop(v2)
                v1 += 1
            if v1 - min_v1 >= dim1:
                spawns.append((min_v1, v1, v2))
    return spawns
