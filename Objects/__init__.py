from random import randint
from Tools import item_ids as i
from Objects.LootTable import LootTable

INV = "res/items/"
MOB = "res/entities/"
PROJ = "res/projectiles/"
# Drops from crushing stuff
CRUSH_DROPS = {
    i.SHINY_STONE_1: LootTable((i.IRON_ORE, 3), (i.GOLD_ORE, 1)),
    i.SHINY_STONE_2: LootTable((i.IRON_ORE, 2), (i.GOLD_ORE, 2), (i.SPHALERITE, 1)),
    i.SHINY_STONE_3: LootTable((i.IRON_ORE, 3), (i.GOLD_ORE, 8), (i.SPHALERITE, 6), (i.PYRITE, 3)),
    i.GEODE: LootTable((i.PEARL, 3), (i.JADE, 3), (i.AMETHYST, 2), (i.SAPPHIRE, 1), (i.OPAL, 1))
}
