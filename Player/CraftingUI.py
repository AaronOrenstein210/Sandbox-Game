# Created on 23 December 2019

import pygame as pg
from pygame.locals import *
from math import ceil
from Tools.constants import BLOCK_W, INV_W
from Tools import game_vars, constants as c, item_ids as items
from Player.ActiveUI import ActiveUI


class CraftingUI(ActiveUI):
    def __init__(self, player):
        self.player = player
        # Recipes that we can and can't craft
        self.can_craft, self.cant_craft = [], []
        # Recipes
        self.recipes = []
        # Crafting stations
        self.blocks = []
        # Ui scroll amount
        self.scroll = 0
        # Set rectangle based on player inventory rectangle
        inv_rect = player.inventory.surface.get_rect(topleft=player.inventory.rect.topleft)
        self.rect = inv_rect.move(0, inv_rect.h)
        # Used to scroll horizontally on a recipe
        self.hold_x = -1
        # Length of time we have been right click crafting
        self.held_right = 0
        # Variables for the current recipe
        self.selected = []
        self.selected_ui = None
        self.selected_scroll = 0
        self.max_off = 0
        # Craft button
        font = c.get_scaled_font(self.rect.w, INV_W, "Craft", "Times New Roman")
        self.craft = font.render("Craft", 1, (0, 0, 0))
        self.craft_rect = self.craft.get_rect(centery=self.rect.h - INV_W // 2, right=self.rect.right - 2)
        self.recipe_rect = pg.Rect(0, self.craft_rect.y, self.craft_rect.x, INV_W)
        super().__init__(None, self.rect)
        self.can_drag = False

        # Recipes that don't need a crafting station
        self.HAND_CRAFTS = [[[items.WORK_TABLE, 1], [items.WOOD, 10]]]
        for item in game_vars.items:
            self.HAND_CRAFTS.append([[item, 1]])

    @property
    def max_scroll(self):
        rows = ceil(len(self.can_craft) // 10) + 1
        return 0 if rows <= 4 else (rows - 4) * INV_W

    @property
    def wait_time(self):
        return max(.75 / (self.held_right + 1), .01)

    def i_can_craft(self, pos):
        return self.craft_rect.collidepoint(*pos) and self.player.use_time <= 0 and \
               self.selected != []

    def update_blocks(self):
        prev = self.can_craft.copy()

        crafters = game_vars.world.crafters
        # Get all crafting blocks in the area and load their recipes
        rect = self.player.placement_range
        blocks = []
        self.recipes.clear()
        self.recipes += self.HAND_CRAFTS
        for x in crafters.keys():
            for y in crafters[x].keys():
                tile = game_vars.tiles[crafters[x][y]]
                if tile.idx not in blocks:
                    r = (x * BLOCK_W, y * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
                    if rect.colliderect(r):
                        blocks.append(tile.idx)
                        self.recipes += tile.recipes
        self.recipes.sort(key=lambda arr: arr[0][0])
        # Check which items we can craft
        self.can_craft.clear(), self.cant_craft.clear()
        resources = self.player.inventory.get_materials()
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
            found = False
            for i, idx in enumerate(self.can_craft):
                recipe = self.recipes[idx]
                # If we found the recipe, stop
                if recipe == self.selected:
                    found = True
                    break
                # If we are on the last element or we past our goal, remove selected
                elif recipe[0][0] > goal:
                    break
            # If we didn't find it, remove selected
            if not found:
                self.selected = []
                self.selected_ui = None

        self.scroll = min(self.scroll, self.max_scroll)

        return self.can_craft != prev

    def update_ui(self, indexes):
        # Trim scroll if necessary
        self.scroll = min(self.scroll, self.max_scroll)
        # Draw recipes
        self.ui = pg.Surface(self.rect.size, pg.SRCALPHA)
        self.ui.fill((0, 200, 200, 128))
        min_row = self.scroll / INV_W
        x, y = -INV_W, -(self.scroll % INV_W)
        for idx in indexes[int(min_row) * 10: ceil(min_row + 4) * 10]:
            # Get rectangle
            x += INV_W
            if x >= self.rect.w:
                x = 0
                y += INV_W
            rect = pg.Rect(x, y, INV_W, INV_W)
            # Get the recipe
            r = self.recipes[idx]
            # Draw the result item's image
            img = game_vars.items[r[0][0]].inv_img
            self.ui.blit(img, img.get_rect(center=rect.center))
            # Draw result amount
            text = c.inv_font.render(str(r[0][1]), 1, (255, 255, 255))
            self.ui.blit(text, text.get_rect(bottomright=rect.bottomright))
        # Draw selected recipe
        self.ui.fill((0, 200, 200, 128), (self.recipe_rect.topleft, (self.rect.w, INV_W)))
        if self.selected_ui:
            self.ui.blit(self.selected_ui, self.recipe_rect.topleft,
                         area=(-self.selected_scroll, 0, *self.recipe_rect.size))
            pg.draw.rect(self.ui, (200, 200, 0), self.recipe_rect, 2)
        self.ui.blit(self.craft, self.craft_rect)

    def draw(self):
        if self.update_blocks():
            self.update_ui(self.can_craft)
        pg.display.get_surface().blit(self.ui, self.rect)
        pos = pg.mouse.get_pos()
        if self.rect.collidepoint(*pos):
            pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
            # Draw description for result item
            if not pos[1] >= self.recipe_rect.y:
                # Get recipe we are hovering over
                x, y = pos[0] // INV_W, (pos[1] + self.scroll) // INV_W
                idx = y * 10 + x
                if idx < len(self.can_craft):
                    item = game_vars.items[self.recipes[self.can_craft[idx]][0][0]]
                    item.draw_description(item.new())
            # Draw description for recipe item
            elif self.recipe_rect.collidepoint(*pos):
                # Get index of recipe item we are hovering over
                # +1 to skip the result item
                idx = (pos[0] - self.selected_scroll) // INV_W + 1
                if idx < len(self.selected):
                    item = game_vars.items[self.selected[idx][0]]
                    item.draw_description(item.new())

    def process_events(self, events, mouse, keys):
        pos = pg.mouse.get_pos()
        # Check for dragging
        if self.hold_x != -1:
            # Moved mouse
            if mouse[BUTTON_LEFT - 1]:
                self.selected_scroll += pos[0] - self.hold_x
                if self.selected_scroll > 0:
                    self.selected_scroll = 0
                elif self.selected_scroll < self.max_off:
                    self.selected_scroll = self.max_off
                self.hold_x = pos[0]
            # Stopped dragging
            else:
                self.hold_x = -1
            mouse[BUTTON_LEFT - 1] = False
        # Check events
        elif self.rect.collidepoint(*pos):
            pos = [pos[0] - self.rect.x, pos[1] - self.rect.y]
            inv = self.player.inventory
            if mouse[BUTTON_RIGHT - 1] and self.i_can_craft(pos):
                inv.craft(self.selected)
                if self.held_right == 0:
                    self.held_right += game_vars.dt
                else:
                    self.held_right += self.wait_time
                self.player.use_time = self.wait_time
            else:
                if not mouse[BUTTON_RIGHT - 1]:
                    self.held_right = 0
                # Check for clicking
                for e in events:
                    if e.type == MOUSEBUTTONUP:
                        if e.button == BUTTON_LEFT:
                            # Craft the item
                            if self.i_can_craft(pos):
                                # Use up ingredients
                                inv.craft(self.selected)
                                self.player.use_time = .5
                                return
                            # Select a new recipe
                            elif pos[1] < self.recipe_rect.y:
                                row = (pos[1] + self.scroll) // INV_W
                                col = pos[0] // INV_W
                                idx = row * 10 + col
                                if idx < len(self.can_craft):
                                    self.selected = self.recipes[self.can_craft[idx]]
                                    parts = self.selected[1:]
                                    w = len(parts) * INV_W
                                    # Draw ingredients
                                    self.selected_ui = pg.Surface((w, INV_W), pg.SRCALPHA)
                                    for i, (item, amnt) in enumerate(parts):
                                        rect = pg.Rect(i * INV_W, 0, INV_W, INV_W)
                                        img = game_vars.items[item].inv_img
                                        self.selected_ui.blit(img, img.get_rect(center=rect.center))
                                        text = c.inv_font.render(str(amnt), 1, (255, 255, 255))
                                        self.selected_ui.blit(text, text.get_rect(bottomright=rect.bottomright))
                                    # Reset ingredient scroll
                                    if w > self.recipe_rect.w:
                                        self.max_off = self.recipe_rect.w - w
                                    else:
                                        self.max_off = 0
                                    self.selected_scroll = 0
                                    # Draw recipe
                                    self.ui.fill((0, 200, 200, 128), (self.recipe_rect.topleft, (self.rect.w, INV_W)))
                                    self.ui.blit(self.selected_ui, self.recipe_rect.topleft,
                                                 area=(-self.selected_scroll, 0, *self.recipe_rect.size))
                                    pg.draw.rect(self.ui, (200, 200, 0), self.recipe_rect, 2)
                                    self.ui.blit(self.craft, self.craft_rect)
                        elif e.button == BUTTON_WHEELUP:
                            self.scroll -= INV_W // 2
                            if self.scroll < 0:
                                self.scroll = 0
                            self.update_ui(self.can_craft)
                        elif e.button == BUTTON_WHEELDOWN:
                            self.scroll += INV_W // 2
                            if self.scroll > self.max_scroll:
                                self.scroll = self.max_scroll
                            self.update_ui(self.can_craft)
                    # Start dragging
                    elif e.type == MOUSEBUTTONDOWN and e.button == BUTTON_LEFT and \
                            self.recipe_rect.collidepoint(*pos):
                        self.hold_x = pos[0]
                    else:
                        continue
                    events.remove(e)
