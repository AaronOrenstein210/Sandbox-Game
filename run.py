# Created on 21 October 2019

import pygame as pg
from traceback import print_exc
import os
from sys import exit
from Tools import game_vars
from Tools.constants import load_fonts, resize, MIN_W, MIN_H

# Make sure all necessary folders exist
folders = ["res", "res/items", "res/items", "res/entities",
           "saves", "saves/players/", "saves/universes/"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Do any initialization of variables and such
pg.init()
load_fonts()
resize(MIN_W, MIN_H)

game_vars.init()

clock = pg.time.Clock()

while True:
    result = False
    try:
        result = game_vars.tick()
    except:
        print("Crashed", print_exc())

    if not result:
        game_vars.close_world()
        pg.quit()
        exit(0)

    pg.display.flip()
    clock.tick(60)
