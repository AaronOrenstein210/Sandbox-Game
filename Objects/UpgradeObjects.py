# Created on 14 March 2020
# Defines upgrades, upgrade paths, and upgrade trees

from Objects.Upgrade import UpgradeTree, UpgradePath, Upgrade, BaseUpgrade, AddUpgrade, MultiUpgrade
from Tools import item_ids as items

# Armor upgrades
head = chest = legs = feet = None
# Sword and pickaxe upgrades
sword = pickaxe = None


def set_upgrade_trees():
    # Defense
    def1 = BaseUpgrade(items.STONE, 5, 1, "defense")
    def2 = BaseUpgrade(items.IRON_BAR, 1, 1, "defense")
    def3 = BaseUpgrade(items.IRON_BAR, 2, 1, "defense")
    def4 = BaseUpgrade(items.OBSIDIAN, 1, 2, "defense")
    # Speed
    spd1 = MultiUpgrade(items.LEAVES, 5, .05, "max_speedx")
    # Acceleration
    # acc1 = BaseUpgrade(items.HELICOPTER_WING, 2, 2, "acceleration")

    global head
    arr = []
    # Defense
    lvl1 = [def1, def2, def1, def3, def4]
    arr.append(UpgradePath([lvl1]))
    # Light/sight based (light, enemies, ore/treasure
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    # Specialty buffs (water breathing, space breathing)
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    head = UpgradeTree(arr)

    global chest
    arr = []
    # Defense + damage reduction
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    # Shield + lava immunity
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    # Specialty buffs (thorns, debuffs on attacking enemies)
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    chest = UpgradeTree(arr)

    global legs
    arr = []
    # Defense
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    # Jump -> flight
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    # Specialty buffs
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    legs = UpgradeTree(arr)

    global feet
    arr = []
    # Defense
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    # Speed + swimming
    lvl1 = [spd1] * 8
    arr.append(UpgradePath([lvl1]))
    # Specialty boosts (liquid walking)
    lvl1 = [def1]
    arr.append(UpgradePath([lvl1]))
    feet = UpgradeTree(arr)


set_upgrade_trees()
