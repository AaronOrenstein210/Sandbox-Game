# Created on 21 October 2019

import pygame as pg
from inspect import getmembers, isclass
from traceback import print_exc
import os
from sys import exit
from Player.Player import Player
from Tools import objects as o
from Tools.constants import load_fonts, resize, MIN_W, MIN_H
from World.WorldSelector import run_selector, PLAYER, UNIVERSE
from Objects import ItemObjects, TileObjects

# Make sure all necessary folders exist
folders = ["res", "res/inventory_icons", "res/item_images", "res/entity_images",
           "saves", "saves/players/", "saves/universes/"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Do any initialization of variables and such
pg.init()
load_fonts()
resize(MIN_W, MIN_H)

# Initialize player so that blocks/items can use it
o.player = Player()

# Compile a list of items
o.items.clear()
for name, obj in getmembers(ItemObjects):
    if isclass(obj):
        if "Objects.ItemObjects" in str(obj):
            instance = obj()
            o.items[instance.idx] = instance

# Compile a list of tiles
o.tiles.clear()
for name, obj in getmembers(TileObjects):
    if isclass(obj):
        if "Objects.TileObjects" in str(obj):
            instance = obj()
            o.tiles[instance.idx] = instance

# Choose player and universe, blocks and items need to be load to do this
o.init(run_selector(PLAYER), run_selector(UNIVERSE))

o.load_world()

next_save = 30000
save_progress = 0
saving = False
time = pg.time.get_ticks()
while True:
    dt = pg.time.get_ticks() - time
    time = pg.time.get_ticks()
    o.tick(dt)

    if saving:
        save_progress = o.save_world_part(save_progress, o.world_file, 10)
        if save_progress >= 1:
            saving = False
            save_progress = 0
            next_save = 30000
    else:
        next_save -= dt
        if next_save <= 0:
            o.player.write(o.player_file)
            saving = True

    result = False
    try:
        result = o.player.run(pg.event.get())
    except:
        print("Crashed", print_exc())
    if not result:
        o.close_world()
        pg.quit()
        exit(0)

    pg.display.flip()
