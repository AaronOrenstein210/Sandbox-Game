from sys import byteorder
from os import listdir, remove, mkdir
from os.path import isfile, isdir
from shutil import rmtree
import pygame as pg
from pygame.locals import *
from Tools.constants import MIN_W, MIN_H
from Tools import constants as c
from Tools import game_vars
from UI.Operations import YesNo
from World.World import World, IdleWorld
from World.WorldGenerator import generate_world
from Player.Player import create_new_player

IMG = "res/images/"
SCROLL_BKGROUND = (0, 0, 128)
PLAYER, UNIVERSE = 0, 1
ITEM_W, ITEM_H = MIN_W // 2, MIN_H // 10
BUTTON_W = ITEM_H // 2
SCROLL_AMNT = ITEM_H // 3


class Selector:
    def __init__(self):
        # Store files/folders
        self.files = []
        # Scroll
        self.scroll = self.max_scroll = 0
        # Surfaces and rectangles
        self.surfaces = {"Main": pg.Surface((0, 0)),
                         "Scroll": pg.Surface((0, 0))}
        self.rects = {"Main": pg.Rect(0, 0, 0, 0),
                      "Scroll": pg.Rect(0, 0, 0, 0)}

    def get_surface(self):
        return self.surfaces["Main"]

    def get_rect(self):
        return self.rects["Main"]

    def load_files(self):
        pass

    def draw_items(self):
        pass

    def resize(self, rect=None):
        if not rect:
            rect = pg.display.get_surface().get_rect()
        self.rects["Main"] = rect
        self.surfaces["Main"] = pg.Surface(rect.size)
        self.surfaces["Main"].fill((0, 175, 150))
        # Set up ui variables
        global ITEM_W, ITEM_H, BUTTON_W, SCROLL_AMNT
        ITEM_W = min(rect.w, MIN_W) // 2
        ITEM_H = min(rect.h, MIN_H) // 10
        BUTTON_W = ITEM_H // 2
        SCROLL_AMNT = ITEM_H // 3

    # Draws to screen
    def draw(self):
        pg.display.get_surface().blit(self.surfaces["Main"], self.rects["Main"])

    def draw_scroller(self):
        r = self.rects["Scroll"]
        self.surfaces["Main"].fill(SCROLL_BKGROUND, r)
        self.surfaces["Main"].blit(self.surfaces["Scroll"], r, area=((0, self.scroll), r.size))

    # Handles an event, returns true if we are done
    def handle_events(self, events):
        return True

    # Runs entire selection process at once
    def run(self):
        self.load_files()

        self.resize()
        while True:
            events = []
            for e in pg.event.get():
                if e.type == QUIT:
                    return False
                elif e.type == VIDEORESIZE:
                    c.resize(e.w, e.h)
                    self.resize()
                else:
                    events.append(e)
            result = self.handle_events(events)
            if result is not None:
                return result
            self.draw()
            pg.display.flip()


# Selector for choosing world from a universe
class WorldSelector(Selector):
    def __init__(self, universe):
        super().__init__()
        # Universe folder
        self.universe = universe
        # Can we delete the file
        self.delete = []

        self.load_files()

    @property
    def path(self):
        return "saves/universes/{}/".format(self.universe)

    # Load all saved players and worlds
    def load_files(self):
        self.files.clear()
        self.delete.clear()
        for file in listdir(self.path):
            if file.endswith(".wld"):
                name = remove_ext(file)
                # Make sure this file is not the current world file
                if not game_vars.world or game_vars.world.file.name != name:
                    with open(self.path + file, 'rb') as f:
                        self.delete.append(bool.from_bytes(f.read(1), byteorder))
                    self.files.append(name)
        self.draw_items()

    # Draw ui
    def draw_items(self):
        # Draw play and delete button, in that order
        r = pg.Rect(ITEM_W - BUTTON_W, 0, BUTTON_W, BUTTON_W)
        play = pg.transform.scale(pg.image.load(IMG + "play.png"), r.size)
        delete = pg.transform.scale(pg.image.load(IMG + "delete.png"), r.size)
        grey_del = c.grey_scale(delete)
        # Draw scroll surface
        s = pg.Surface((ITEM_W, ITEM_H * len(self.files)))
        for i, file in enumerate(self.files):
            text = c.load_font.render(file.replace("_", " "), 1, (255, 255, 255))
            text_rect = text.get_rect(center=((ITEM_W - BUTTON_W) // 2, ITEM_H * (i + .5)))
            if text_rect.x < 0:
                text_rect.x = 0
                s.blit(text, text_rect, area=(0, 0, ITEM_W - BUTTON_W, text_rect.h))
            else:
                s.blit(text, text_rect)
            # Draw play and delete buttons
            s.blit(play, r)
            r.move_ip(0, BUTTON_W)
            s.blit(delete if self.delete[i] else grey_del, r)
            r.move_ip(0, BUTTON_W)
        self.surfaces["Scroll"] = s
        self.draw_scroller()

    # Resizes ui
    def resize(self, rect=None):
        super().resize(rect)
        w, h = self.rects["Main"].size
        # Resize rectangles
        self.rects["Scroll"] = pg.Rect((w - ITEM_W) // 2, ITEM_H, ITEM_W, h - ITEM_H * 2)
        self.max_scroll = max(0, self.surfaces["Scroll"].get_size()[1] - self.rects["Scroll"].h)
        # Draw ui
        self.draw_items()
        self.draw_scroller()

    # Handles events
    def handle_events(self, events):
        for e in events:
            # Any mouse action
            if e.type == MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()
                pos = [pos[0] - self.rects["Main"].x, pos[1] - self.rects["Main"].y]
                # If it happened in this rect
                if self.rects["Scroll"].collidepoint(*pos):
                    # Scroll up
                    if e.button == BUTTON_WHEELUP:
                        self.scroll = max(0, self.scroll - SCROLL_AMNT)
                    # Scroll down
                    elif e.button == BUTTON_WHEELDOWN:
                        self.scroll = min(self.max_scroll, self.scroll + SCROLL_AMNT)
                    elif e.button == BUTTON_LEFT:
                        pos = (pos[0] - self.rects["Scroll"].x, pos[1] - self.rects["Scroll"].y)
                        idx = (pos[1] - self.scroll) // ITEM_H
                        if idx < len(self.files) and pos[0] >= ITEM_W - BUTTON_W:
                            world_name = add_spaces(self.files[idx])
                            if (pos[1] - self.scroll) % ITEM_H < BUTTON_W:
                                game_vars.change_world(c.WorldFile(self.universe, name=world_name))
                                return True
                            elif self.delete[idx]:
                                if YesNo("Delete " + world_name + "?", redraw_back=self.draw()).run_now():
                                    remove(c.WorldFile(self.universe, name=world_name).full_file)
                                    self.load_files()


# Selector for choosing universe and world
class MainSelector(Selector):
    def __init__(self):
        super().__init__()
        # Ui variables
        self.surfaces["New"] = pg.Surface((0, 0))
        self.rects["New"] = pg.Rect(0, 0, 0, 0)
        self.rects["Text"] = pg.Rect(BUTTON_W // 4, BUTTON_W // 4, ITEM_W - BUTTON_W * 3 // 2, BUTTON_W * 3 // 2)
        self.rects["Create"] = pg.Rect(ITEM_W - BUTTON_W, BUTTON_W // 2, BUTTON_W, BUTTON_W)
        # Universe folder or player file
        self.file = c.PlayerFile()
        # What we are loading
        self.mode = PLAYER
        # Text has cursor
        self.show_cursor = False

        self.load_files()

    def create_new(self):
        if self.mode == PLAYER:
            create_new_player(self.file)
            self.file = c.PlayerFile()
        elif self.mode == UNIVERSE:
            mkdir(self.file.full_file)
            # Generate a new world
            new = World(c.WorldFile(self.file.name, name="Forest"))
            new.can_delete = False
            generate_world(new)
            new = IdleWorld(c.WorldFile(self.file.name, name="Idle World"))
            generate_world(new)
            del new
            self.file = c.UniverseFolder()
        self.draw_text()
        self.load_files()

    # Load all saved players and worlds
    def load_files(self):
        self.files.clear()
        for file in listdir(self.file.path):
            if self.mode == PLAYER:
                if isfile(self.file.path + file) and file.endswith(self.file.extension):
                    self.files.append(remove_ext(file))
            elif self.mode == UNIVERSE:
                if isdir(self.file.path + file) and any(f.endswith(".wld") for f in listdir(self.file.path + file)):
                    self.files.append(file)
        self.draw_items()

    # Draw ui
    def draw_items(self):
        opt_surf = pg.Surface((BUTTON_W, ITEM_H))
        # Draw play and delete button, in that order
        r = pg.Rect(0, 0, BUTTON_W, BUTTON_W)
        opt_surf.blit(pg.transform.scale(pg.image.load(IMG + "play.png"), r.size), r)
        r.move_ip(0, BUTTON_W)
        opt_surf.blit(pg.transform.scale(pg.image.load(IMG + "delete.png"), r.size), r)
        # Draw scroll surface
        s = pg.Surface((ITEM_W, ITEM_H * len(self.files)))
        for i, text in enumerate(self.files):
            text = c.load_font.render(text.replace("_", " "), 1, (255, 255, 255))
            text_rect = text.get_rect(center=((ITEM_W - BUTTON_W) // 2, ITEM_H * (i + .5)))
            if text_rect.x < 0:
                text_rect.x = 0
                s.blit(text, text_rect, area=(0, 0, ITEM_W - BUTTON_W, text_rect.h))
            else:
                s.blit(text, text_rect)
            s.blit(opt_surf, (ITEM_W - BUTTON_W, ITEM_H * i))
        self.surfaces["Scroll"] = s
        # Draw new world surface
        s = pg.Surface((ITEM_W, ITEM_H))
        s.fill(SCROLL_BKGROUND)
        s.fill((128, 128, 128), self.rects["Text"])
        r = self.rects["Create"]
        s.blit(pg.transform.scale(pg.image.load(IMG + "add.png"), r.size), r)
        self.surfaces["New"] = s
        self.draw_scroller()

    # Resizes ui, returns the main surface
    def resize(self, rect=None):
        super().resize(rect)
        w, h = self.rects["Main"].size
        # Resize rectangles
        self.rects["Scroll"] = pg.Rect((w - ITEM_W) // 2, ITEM_H, ITEM_W, h - ITEM_H * 3)
        r = self.rects["Scroll"]
        self.rects["New"] = pg.Rect(r.x, r.bottom, r.w, ITEM_H)
        self.max_scroll = max(0, self.surfaces["Scroll"].get_size()[1] - self.rects["Scroll"].h)
        # Draw ui
        self.draw_items()
        self.draw_text()

    # Draws new world name text
    def draw_text(self):
        text = self.file.name + ("|" if self.show_cursor else "")
        text = c.load_font.render(text, 1, (255, 255, 255))
        r = text.get_rect(centery=self.rects["Text"].centery, left=self.rects["Text"].left)
        self.surfaces["New"].fill((0, 0, 0), self.rects["Text"])
        text_w = self.rects["Text"].w
        if r.w > text_w:
            self.surfaces["New"].blit(text, r, area=(r.w - text_w, 0, text_w, r.h))
        else:
            self.surfaces["New"].blit(text, r)
        self.surfaces["Main"].blit(self.surfaces["New"], self.rects["New"])

    # Handles events
    def handle_events(self, events):
        temp = (pg.time.get_ticks() // 400) % 2 == 0
        if temp != self.show_cursor:
            self.show_cursor = temp
            self.draw_text()
        for e in events:
            # Any mouse action
            if e.type == MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()
                pos = [pos[0] - self.rects["Main"].x, pos[1] - self.rects["Main"].y]
                # If it happened in this rect
                if self.rects["Scroll"].collidepoint(*pos):
                    # Scroll up
                    if e.button == BUTTON_WHEELUP:
                        self.scroll = max(0, self.scroll - SCROLL_AMNT)
                    # Scroll down
                    elif e.button == BUTTON_WHEELDOWN:
                        self.scroll = min(self.max_scroll, self.scroll + SCROLL_AMNT)
                    elif e.button == BUTTON_LEFT:
                        pos = [pos[0] - self.rects["Scroll"].x, pos[1] - self.rects["Scroll"].y]
                        idx = (pos[1] - self.scroll) // ITEM_H
                        if idx < len(self.files) and pos[0] >= ITEM_W - BUTTON_W:
                            # Top button is play button
                            if (pos[1] - self.scroll) % ITEM_H < BUTTON_W:
                                if self.mode == PLAYER:
                                    from Player.Player import Player
                                    game_vars.player = Player(c.PlayerFile(name=self.files[idx]))
                                    game_vars.player.load()
                                    self.mode = UNIVERSE
                                    self.file = c.UniverseFolder()
                                    self.load_files()
                                else:
                                    return WorldSelector(self.files[idx]).run()
                            # Bottom button is delete button
                            else:
                                if YesNo("Delete " + add_spaces(self.files[idx]) + "?",
                                         redraw_back=self.draw()).run_now():
                                    if self.mode == PLAYER:
                                        remove(self.file.path + self.files[idx] + self.file.extension)
                                    elif self.mode == UNIVERSE:
                                        rmtree(self.file.path + self.files[idx] + self.file.extension)
                                    self.load_files()
                elif self.rects["New"].collidepoint(*pos) and self.file.valid:
                    pos = [pos[0] - self.rects["New"].x, pos[1] - self.rects["New"].y]
                    if self.rects["Create"].collidepoint(*pos):
                        self.create_new()
            # Key press
            elif e.type == KEYDOWN:
                if e.key == K_RETURN:
                    self.create_new()
                else:
                    self.file.type_char(e)
                self.draw_text()


# Takes off extension
def remove_ext(name):
    return name[:name.rfind(".")]


# Switches '_' to ' '
def add_spaces(file_name):
    return file_name.replace('_', ' ')
