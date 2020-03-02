from random import randint
from Tools import item_ids as i

INV = "res/item_images/"
MOB = "res/entity_images/"
PROJ = "res/projectile_images/"
# Drops from crushing stuff
CRUSH_DROPS = {
    i.SHINY_STONE_1: lambda num: (i.IRON_ORE, randint(1, 2)) if num <= 75 else (
        i.GOLD_ORE, 1),
    i.SHINY_STONE_2: lambda num: (i.IRON_ORE, randint(1, 3)) if num <= 40 else (
        i.GOLD_ORE, randint(1, 2)) if num <= 80 else (
        i.SPHALERITE, randint(1, 2)),
    i.SHINY_STONE_3: lambda num: (i.IRON_ORE, randint(1, 5)) if num <= 15 else (
        i.GOLD_ORE, randint(1, 3)) if num <= 55 else (
        i.SPHALERITE, randint(1, 2)) if num <= 85 else (
        i.PYRITE, randint(1, 2))
}
