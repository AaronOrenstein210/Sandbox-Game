# Created on 30 December 2019


class Drop:
    def __init__(self, item, min_num, max_num, chance):
        self.item = item
        self.min, self.max = min_num, max_num
        self.chance = chance


class DropsList:
    def __init__(self, drops):
        self.drops = drops
        self.chance_sum = 0
        for d in drops:
            self.chance_sum += d.chance

    # Randomly selects a drop
    def get_drop(self):
        from random import randint
        num = randint(1, self.chance_sum)
        for d in self.drops:
            if d.chance < num:
                num -= d.chance
            else:
                return num, randint(d.min, d.max)

    def get_drop_list(self):
        items = []
        from random import randint
        for d in self.drops:
            if randint(1, 100) <= d.chance:
                items.append((d.item, randint(d.min, d.max)))
