# Created on 23 December 2019

import pygame as pg
from pygame.locals import *
from math import ceil
from Tools.constants import BLOCK_W, INV_W
from Tools import objects as o, constants as c
from Player.ActiveUI import ActiveUI


class CraftingUI(ActiveUI):
    def __init__(self, player):
        self.player = player
        self.can_craft, self.cant_craft = [], []
        self.recipes = []
        self.blocks = []
        self.scroll = 0
        self.rect = pg.Rect(0, 5 * INV_W, 10 * INV_W, 5 * INV_W)
        self.hold_x = -1
        # Variables for the current recipe
        self.selected = []
        self.selected_ui = None
        self.selected_off = 0
        self.max_off = 0
        # Craft button
        font = c.get_scaled_font(self.rect.w, INV_W, "Craft", "Times New Roman")
        self.craft = font.render("Craft", 1, (0, 0, 0))
        self.craft_rect = self.craft.get_rect(centery=self.rect.h - INV_W // 2, right=self.rect.right - 2)
        self.recipe_rect = pg.Rect(0, self.craft_rect.y, self.craft_rect.x, INV_W)
        ActiveUI.__init__(self, None, self.rect)

    @property
    def max_scroll(self):
        rows = ceil(len(self.recipes) // 10)
        return 0 if rows <= 4 else (4 - rows) * INV_W

    def i_can_craft(self, pos):
        return self.craft_rect.collidepoint(*pos) and o.player.use_time <= 0 and \
               self.selected != []

    def update_blocks(self):
        crafters = o.world.crafters
        # Get all crafting blocks in the area and load their recipes
        rect = self.player.placement_range
        blocks = []
        self.recipes.clear()
        for x in crafters.keys():
            for y in crafters[x].keys():
                tile = o.tiles[crafters[x][y]]
                if tile.idx not in blocks:
                    r = (x * BLOCK_W, y * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
                    if rect.colliderect(r):
                        blocks.append(tile.idx)
                        self.recipes += tile.recipes
        self.recipes.sort(key=lambda arr: arr[0][0])
        # Check which items we can craft
        self.can_craft.clear(), self.cant_craft.clear()
        resources = o.player.inventory.get_all_items()
        for j, r in enumerate(self.recipes):
            r = r[1:]
            i = 0
            # Loop through our resources, breaking if we complete the requirements,
            # we fail a requirement, or we run out of resources
            while len(r) > 0 and i < len(resources):
                item = resources[i][0]
                # Check if we passed our ingredient
                if r[0][0] < item:
                    break
                # Otherwise, make sure we have enough
                elif r[0][0] == item:
                    amnt = resources[i][1]
                    if r[0][1] > amnt:
                        break
                    else:
                        del r[0]
                i += 1
            # Check if we successfully removed every ingredient
            if len(r) == 0:
                self.can_craft.append(j)
            else:
                self.cant_craft.append(j)

        # Make sure the selected recipe is still there
        if self.selected:
            goal = self.selected[0][0]
            # Take care of special cases
            if len(self.can_craft) == 0:
                self.selected_ui = None
            else:
                for i, idx in enumerate(self.can_craft):
                    recipe = self.recipes[idx]
                    if recipe[0][0] == goal and recipe == self.selected:
                        break
                    # If the selected item was skipped over, then it isn't craftable
                    if recipe[0][0] > goal or idx == len(self.can_craft) - 1:
                        self.selected_ui = None
                        break

    def update_ui(self, indexes):
        # 10 items per row
        num = len(indexes)
        num_rows = ceil(num / 10)
        # Trim scroll if necessary
        if num_rows <= 4:
            self.scroll = 0
        else:
            self.scroll = max(self.scroll, (5 - num_rows) * INV_W)
        # Draw recipes
        surface = pg.Surface(self.rect.size, pg.SRCALPHA)
        surface.fill((0, 200, 200, 128))
        min_row = -self.scroll / INV_W
        for i, idx in enumerate(indexes[int(min_row) * 10: ceil(min_row + 4) * 10]):
            r = self.recipes[idx]
            img = pg.transform.scale(o.items[r[0][0]].inv_img, (INV_W, INV_W))
            text = c.inv_font.render(str(r[0][1]), 1, (255, 255, 255))
            text_rect = text.get_rect(bottomright=(INV_W, INV_W))
            img.blit(text, text_rect)
            # img.convert_alpha()
            # img.fill((255, 255, 255, 128), None, pg.BLEND_RGBA_MULT)
            surface.blit(img, ((i % 10) * INV_W, (i // 10) * INV_W + self.scroll))
        if self.selected_ui is not None:
            surface.blit(self.selected_ui, self.recipe_rect.topleft,
                         area=(-self.selected_off, 0, *self.recipe_rect.size))
        surface.blit(self.craft, self.craft_rect)
        pg.display.get_surface().blit(surface, self.rect)
        del surface

    def draw(self):
        self.update_blocks()
        self.update_ui(self.can_craft)

    def process_events(self, events, mouse, keys):
        pos = pg.mouse.get_pos()
        # Check for dragging
        if self.hold_x != -1:
            # Moved mouse
            if mouse[BUTTON_LEFT - 1]:
                self.selected_off += pos[0] - self.hold_x
                if self.selected_off > 0:
                    self.selected_off = 0
                elif self.selected_off < self.max_off:
                    self.selected_off = self.max_off
                self.hold_x = pos[0]
            # Stopped dragging
            else:
                self.hold_x = -1
            mouse[BUTTON_LEFT - 1] = False
        elif self.rect.collidepoint(*pos):
            pos = [pos[0], pos[1] - self.rect.y]
            inv = o.player.inventory
            if mouse[BUTTON_RIGHT - 1] and self.i_can_craft(pos):
                inv.craft(self.selected)
                o.player.use_time = 500
                return
            # Check for clicking
            for e in events:
                if e.type == MOUSEBUTTONUP:
                    if e.button == BUTTON_LEFT:
                        # Craft the item
                        if self.i_can_craft(pos):
                            # Use up ingredients
                            inv.craft(self.selected)
                            o.player.use_time = 500
                            return
                        # Select a new recipe
                        elif pos[1] < self.recipe_rect.y:
                            row = (pos[1] - self.scroll) // INV_W
                            col = pos[0] // INV_W
                            idx = row * 10 + col
                            if idx < len(self.can_craft):
                                self.selected = self.recipes[self.can_craft[idx]]
                                items = self.selected[1:]
                                w = len(items) * INV_W
                                # Draw ingredients
                                self.selected_ui = pg.Surface((w, INV_W), pg.SRCALPHA)
                                for i, (item, amnt) in enumerate(items):
                                    img = pg.transform.scale(o.items[item].inv_img, (INV_W, INV_W))
                                    text = c.inv_font.render(str(amnt), 1, (255, 255, 255))
                                    text_rect = text.get_rect(bottomright=(INV_W, INV_W))
                                    img.blit(text, text_rect)
                                    self.selected_ui.blit(img, (i * INV_W, 0))
                                # Reset ingredient scroll
                                if w > self.recipe_rect.w:
                                    self.max_off = self.recipe_rect.w - w
                                else:
                                    self.max_off = 0
                                self.selected_off = 0
                    elif e.button in [BUTTON_WHEELUP, BUTTON_WHEELDOWN]:
                        self.scroll += INV_W // 2 * (1 if e.button == BUTTON_WHEELUP else -1)
                        if self.scroll > 0:
                            self.scroll = 0
                        else:
                            ub = self.max_scroll
                            if self.scroll < ub:
                                self.scroll = self.max_scroll
                # Start dragging
                elif e.type == MOUSEBUTTONDOWN and e.button == BUTTON_LEFT and \
                        self.recipe_rect.collidepoint(*pos):
                    self.hold_x = pos[0]
                else:
                    continue
                events.remove(e)
