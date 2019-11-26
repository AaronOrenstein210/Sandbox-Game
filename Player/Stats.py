# Created on 12 November 2019
# Defines functions and variables for the stats class


class Stats:
    def __init__(self, hp=100, defense=0, damage=0, max_speed=(6, 10), attack_speed=.3):
        self.max_hp, self.hp = hp, hp
        self.defense = defense
        self.dmg, self.dmg_mult, self.dmg_type_mult = damage, 1, [1, 1, 1, 1, 1]
        self.spd = max_speed
        self.crit_chance, self.crit_mult = 10, 2
        self.atk_spd = attack_speed

    def clone(self):
        return Stats(hp=self.hp, defense=self.defense, damage=self.dmg, max_speed=self.spd,
                     attack_speed=self.atk_spd)
