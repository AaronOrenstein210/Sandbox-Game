# Created on 12 November 2019
# Defines functions and variables for the stats class

ENEMY_STATS = ["damage", "hp", "defense", "max_speedx", "max_speedy", "jump_speed", "acceleration"]
WEAPON_STATS = ["damage", "crit_chance", "crit_damage", "use_speed", "knockback"]
TOOL_STATS = WEAPON_STATS + ["power"]
# Combine above and remove duplicates
STATS = list(dict.fromkeys(TOOL_STATS + ENEMY_STATS).keys())

DEF_PLAYER = {"hp": 100, "max_speedx": 8, "acceleration": 10, "jump_speed": 12, "max_speedy": 20}
DEF_MOB = {"jump_speed": 12, "acceleration": 10, "max_speedy": 20, "max_speedx": 7}


class Stats:
    def __init__(self, stats_list, defaults=None, **kwargs):
        if defaults:
            kwargs.update({k: v for k, v in defaults.items() if k not in kwargs.keys()})
        # Dictionaries of base stats, additive bonuses, and multiplicative bonuses
        self.base = {k: 0 for k in stats_list}
        self.add, self.multi = self.base.copy(), self.base.copy()
        self.base.update(kwargs)
        # Other stats objects to add to this one
        self.other_stats = []
        # Current hp
        self.hp = self.get_stat("hp")

    def get_stat(self, stat):
        arr = [s for s in self.other_stats + [self] if stat in s.base.keys()]
        base = sum(s.base[stat] for s in arr)
        multi = sum((s.multi[stat] for s in arr), 1)
        add = sum(s.add[stat] for s in arr)
        return base * multi + add

    def add_stats(self, stats):
        self.other_stats.append(stats)

    def remove_stats(self, stats):
        if stats in self.other_stats:
            self.other_stats.remove(stats)

    def reset(self):
        for key in self.base.keys():
            self.base[key] = self.add[key] = self.multi[key] = 0

    def clone(self):
        s = Stats(self.base.keys())
        s.base = self.base.copy()
        s.add = self.add.copy()
        s.multi = self.multi.copy()
        return s
