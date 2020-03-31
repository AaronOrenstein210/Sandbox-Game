# Created on 21 October 2019

import threading
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

playing = True


def draw_loop():
    global playing
    while playing:
        try:
            game_vars.draw()
        except:
            print("Draw Loop Crashed", print_exc())
            playing = False

        pg.display.flip()
        clock.tick(60)


# Set up and start draw loop in a separate thread
thread1 = threading.Thread(target=draw_loop)
thread1.start()

# Run the game loop
while playing:
    result = False
    try:
        result = game_vars.tick()
    except:
        print("Game Loop Crashed", print_exc())

    if not result:
        playing = False
    clock.tick(60)

# Once the game loop finishes, wait for the draw loop
thread1.join()

# Save and close the world
game_vars.close_world()
pg.quit()
exit(0)
