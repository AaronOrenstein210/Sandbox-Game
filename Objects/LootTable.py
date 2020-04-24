# Created on 23 April 2020
# Defines the Loot Table class

import random


# TODO: Item amounts
class LootTable:
    # Takes in (item, amnt) arguments
    def __init__(self, *items):
        self.items = {i[0]: i[1] for i in items}

    @property
    def sum(self):
        return sum(i for i in self.items.values())

    def add(self, item, amnt):
        if item not in self.items.keys():
            self.items[item] = amnt
        else:
            self.items[item] += amnt

    def subtract(self, item, amnt):
        if item in self.items.keys():
            self.items[item] -= amnt
            if self.items[item] <= 0:
                self.items[item] = None

    def delete(self, item):
        self.items[item] = None

    def random(self):
        num = random.randint(1, self.sum)
        for key, val in self.items.items():
            if num <= val:
                return key
            else:
                num -= val
        # If it failed for some reason, return 0
        print("Loot Table failed to choose random drop")
        return random.choice(self.items.keys())
