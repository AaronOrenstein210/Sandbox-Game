# Created on 21 October 2019

import pygame as pg
from traceback import print_exc
import os
from sys import exit
from Tools import objects as o
from Tools.constants import load_fonts, resize, MIN_W, MIN_H, get_scaled_font

# Make sure all necessary folders exist
folders = ["res", "res/item_images", "res/item_images", "res/entity_images",
           "saves", "saves/players/", "saves/universes/"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Do any initialization of variables and such
pg.init()
load_fonts()
fps_font = get_scaled_font(50, 20, "000 FPS", "Times New Roman")
resize(MIN_W, MIN_H)

o.init()

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
        save_progress = o.world.save_part(save_progress, 1)
        if save_progress >= 1:
            saving = False
            save_progress = 0
            next_save = 30000
    else:
        next_save -= dt
        if next_save <= 0:
            o.player.write()
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

    if dt != 0:
        fps = 1000 // dt
        print("\r" + str(fps), end=" ")
        text = fps_font.render(str(fps) + " FPS", 1, (0, 0, 0))
        text_rect = text.get_rect(bottom=pg.display.get_surface().get_size()[1])
        pg.display.get_surface().blit(text, text_rect)

    pg.display.flip()
