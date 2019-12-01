# Created on 21 October 2019

from traceback import print_exc
import os
import pygame as pg
from sys import exit
import World as W
from Player.Player import Player
from Tools import constants as c
from World.WorldSelector import run_selector, PLAYER, UNIVERSE
from Tools.UIOperations import complete_task

# Do any initialization of variables and such
pg.init()
c.load_fonts()
c.resize(c.MIN_W, c.MIN_H)

# Make sure all necessary folders at least exist
folders = ["res", "res/inventory_icons", "res/item_images", "res/entity_images",
           "saves", "saves/players/", "saves/universes/"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

player_file = "saves/players/" + run_selector(PLAYER) + ".plr"
player = Player()
player.load(player_file)

c.universe_name = run_selector(UNIVERSE)
universe_folder = "saves/universes/" + c.universe_name + "/"
c.world_name = c.universe_name
world_file = universe_folder + c.world_name + ".wld"


def close_world():
    complete_task(W.save_world_part, task_args=[world_file], message="Saving World", can_exit=False)
    player.write(player_file)


def load_world():
    if not complete_task(W.load_world_part, task_args=[world_file, 5], message="Loading World Blocks"):
        pg.quit()
        exit(0)
    player.driver.draw_blocks()
    player.spawn()


def change_world():
    def screen_goes_white(progress):
        display = pg.display.get_surface()
        player.draw_ui()
        overlay = pg.Surface(display.get_size())
        overlay.fill((255 * progress, 255 * progress, 255))
        overlay.set_alpha(255 * progress)
        display.blit(overlay, (0, 0))

    global world_file
    complete_task(W.save_world_part, task_args=[world_file, None, None, 10], can_exit=False,
                  update_ui=screen_goes_white)
    player.write(player_file)
    world_file = universe_folder + c.world_name + ".wld"
    load_world()
    c.game_state = c.PLAYING


load_world()

next_save = 30000
save_progress = 0
saving = False
time = pg.time.get_ticks()
while True:
    dt = pg.time.get_ticks() - time
    time = pg.time.get_ticks()
    W.world_time = (W.world_time + dt) % W.MS_PER_DAY

    if saving:
        save_progress = W.save_world_part(save_progress, world_file, num_rows=10)
        if save_progress >= 1:
            saving = False
            save_progress = 0
            next_save = 30000
    else:
        next_save -= dt
        if next_save <= 0:
            player.write(player_file)
            saving = True

    try:
        player.run(pg.event.get(), dt)
    except:
        print("Crashed", print_exc())
        c.game_state = c.END_GAME
    if c.game_state == c.END_GAME:
        close_world()
        pg.quit()
        exit(0)
    elif c.game_state == c.CHANGE_WORLD:
        change_world()

    pg.display.update()
