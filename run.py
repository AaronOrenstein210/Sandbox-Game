# Created on 21 October 2019

from traceback import print_exc
import os, pygame
from pygame.locals import RESIZABLE
from sys import exit
from GameDriver import GameDriver
import World as w
from HelpfulTools import complete_task
from World.WorldSelector import run_selector
from Databases.constants import load_fonts, resize

# Do any initialization of variables and such
pygame.init()
load_fonts()

# Make sure all necessary folders at least exist
folders = ["res", "res/inventory_icons", "res/item_images", "res/entity_images",
           "saves", "saves/players/", "saves/worlds/"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

player, world = run_selector()

player_file = "saves/players/" + player + ".plr"
world_file = "saves/worlds/" + world + ".wld"

if not complete_task(w.load_world_part, args=[world_file], msg="Loading World Blocks"):
    pygame.quit()
    exit(0)

driver = GameDriver()
driver.player.load("saves/players/" + player + ".plr")
driver.draw_blocks()

next_save = 30000
save_progress = 0
saving = False
time = pygame.time.get_ticks()
while True:
    dt = pygame.time.get_ticks() - time
    time = pygame.time.get_ticks()
    w.world_time = (w.world_time + dt) % w.MS_PER_DAY

    if saving:
        save_progress = w.save_world_part(save_progress, world_file, num_rows=10)
        if save_progress >= 1:
            saving = False
            save_progress = 0
            next_save = 30000
    else:
        next_save -= dt
        if next_save <= 0:
            driver.player.write(player_file)
            saving = True

    result = False
    try:
        result = driver.run(pygame.event.get(), dt)
    except:
        print("Crashed", print_exc())
    if not result:
        complete_task(w.save_world_part, args=[world_file], msg="Saving World", can_exit=False)
        driver.player.write(player_file)
        pygame.quit()
        exit(0)

    pygame.display.update()
