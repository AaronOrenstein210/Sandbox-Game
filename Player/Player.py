# Created on 22 October 2019
# Defines methods and variables for the player

import pygame as pg
from pygame.locals import *
from math import copysign, ceil
from Tools.constants import BLOCK_W
from Tools import constants as c
from Tools import game_vars
from Tools.tile_ids import AIR
from Player.PlayerInventory import PlayerInventory, new_inventory
from Player.CraftingUI import CraftingUI
from Player.Stats import Stats, STATS, DEF_PLAYER, TOOL_STATS
from Player.Map import Map


class Player:
    def __init__(self, player_file):
        self.file = player_file
        # Stats
        self.stats = Stats(STATS, defaults=DEF_PLAYER)
        # Stats object for held weapon/tool
        self.item_stats = Stats(TOOL_STATS)
        self.stats.add_stats(self.item_stats)
        # Inventory
        self.inventory = PlayerInventory(self)
        self.item_used, self.use_time = None, 0
        self.used_left = True
        self.first_swing = True
        # Player image
        self.surface = c.scale_to_fit(pg.image.load("res/player/player_pig.png"), w=1.5 * BLOCK_W)
        # Rectangle and block dimensions
        self.rect = pg.Rect((0, 0), self.surface.get_size())
        self.dim = [1.5, self.rect.h / BLOCK_W]
        # Player sprite for world map
        self.sprite = c.scale_to_fit(self.surface, w=c.SPRITE_W, h=c.SPRITE_W)
        # Arm sprite
        self.arm = pg.Surface((int(self.rect.w / 4), int(self.rect.h / 3)))
        self.arm.fill((200, 128, 0))
        # This determines the area in which items are collected
        self.collection_range = Rect(0, 0, 6 * BLOCK_W, 6 * BLOCK_W)
        # This determines the area that you can place blocks
        self.placement_range = Rect(0, 0, 7 * BLOCK_W, 7 * BLOCK_W)
        # Physics variables
        self.pos = [0, 0]
        self.v = [0., 0.]
        self.a = [0., 20.]
        # Collisions  in x and y
        self.collisions = [0, 0]
        # Distance fallen
        self.fall_dist = 0
        # Attack immunity
        self.immunity = 0
        # Respawn counter
        self.respawn_counter = 0
        # Whether we can move or not
        self.can_move = True
        # Stores an active ui and position of source block if applicable
        self.active_ui = None
        self.active_block = [0, 0]
        self.active_ui_pos = [0, 0]
        self.dragging_ui = False
        # Crafting UI
        self.crafting_ui = CraftingUI(self)
        self.crafting_open = True
        # If the world map is open or not
        self.map_open = False
        # Map object
        self.map = None

        self.set_pos((0, 0))

    @property
    def immune(self):
        return self.immunity > 0 or self.respawn_counter > 0

    def load(self):
        with open(self.file.full_file, "rb+") as data_file:
            data = data_file.read()
            self.inventory.load(data)

    def write(self):
        # See load() for info order
        with open(self.file.full_file, "wb+") as file:
            file.write(self.inventory.write())

    def set_map_source(self, surface):
        self.map = Map(surface)
        self.map.set_center(self.rect.center)

    # Interprets events during normal gameplay
    def run_main(self, events):
        # Update mouse position
        pos = pg.mouse.get_pos()

        # If we are dead, decrement respawn counter
        if self.respawn_counter > 0:
            self.respawn_counter -= game_vars.dt
            if self.respawn_counter <= 0:
                self.respawn()
        # Otherwise interpret events
        else:
            mouse = list(pg.mouse.get_pressed())
            keys = list(pg.key.get_pressed())
            mods = pg.key.get_mods()

            # Open the crafting ui if the inventory is open, crafting should be open,
            # and there is no current ui
            if self.inventory.open and self.crafting_open:
                if not self.active_ui:
                    self.set_active_ui(self.crafting_ui)
            # Close the crafting ui if it is open and the inventory is closed of it
            # should not be open
            elif self.active_ui is self.crafting_ui:
                self.set_active_ui(None)

            # Send events to the active ui
            if self.active_ui:
                self.active_ui.tick()
                if self.dragging_ui:
                    # Check if we are done dragging
                    if not mouse[BUTTON_RIGHT - 1]:
                        self.dragging_ui = False
                    else:
                        w, h = self.active_ui.rect.size
                        # Move x
                        x = self.active_ui_pos[0] * c.screen_w + game_vars.d_mouse[0]
                        x = max(w // 2, min(x, c.screen_w - w // 2))
                        self.active_ui_pos[0] = x / c.screen_w
                        self.active_ui.rect.centerx = x
                        # Move y
                        y = self.active_ui_pos[1] * c.screen_h + game_vars.d_mouse[1]
                        y = max(h // 2, min(y, c.screen_h - h // 2))
                        self.active_ui_pos[1] = y / c.screen_h
                        self.active_ui.rect.centery = y
                else:
                    self.active_ui.process_events(events, mouse, keys)

            # Process events
            for e in events:
                if self.use_time <= 0 and e.type == MOUSEBUTTONUP:
                    # Scroll the inventory
                    if e.button == BUTTON_WHEELUP:
                        self.inventory.scroll(True)
                    elif e.button == BUTTON_WHEELDOWN:
                        self.inventory.scroll(False)
                elif e.type == MOUSEBUTTONDOWN and e.button == BUTTON_RIGHT:
                    if mods & KMOD_SHIFT and self.active_ui and self.active_ui.can_drag and \
                            self.active_ui.rect.collidepoint(*pos):
                        self.dragging_ui = True
                elif e.type == KEYDOWN:
                    # Try to jump
                    if e.key == K_SPACE and self.can_move:
                        if game_vars.touching_blocks_y(self.pos, self.dim, False):
                            self.v[1] = -15
                    # Close current active ui
                    if e.key == K_ESCAPE and self.active_ui and self.active_ui != self.crafting_ui:
                        self.active_ui.on_exit()
                        self.active_ui = None
                    # Inventory buttons
                    elif self.use_time <= 0:
                        self.inventory.key_pressed(e.key)
                elif e.type == KEYUP:
                    # Open map
                    if e.key == K_m:
                        self.map_open = True
                        self.map.set_center([p / BLOCK_W for p in self.rect.center])
                        self.map.zoom = 1

            # Check keys
            if keys[K_RIGHT]:
                self.map.zoom += game_vars.dt * 10
                if self.map.zoom > 5:
                    self.map.zoom = 5
            if keys[K_LEFT]:
                self.map.zoom -= game_vars.dt * 10
                if self.map.zoom < 1:
                    self.map.zoom = 1

            # No item in use and not clicking tile ui
            if self.use_time <= 0 and (self.active_ui is None or
                                       not self.active_ui.rect.collidepoint(*pos)):
                # Mouse click events
                if mouse[BUTTON_LEFT - 1]:
                    self.left_click()
                else:
                    self.first_swing = True
                    if mouse[BUTTON_RIGHT - 1]:
                        self.right_click()
                    else:
                        self.inventory.holding_r = 0

            # If we are using an item, let it handle the use time
            if self.item_used is not None:
                self.item_used.on_tick()
                # Check if we are done using the item
                if self.use_time <= 0:
                    self.item_used = None
            # Otherwise decrement the use time
            elif self.use_time >= 0:
                self.use_time -= game_vars.dt

            # Check if we can move
            if self.can_move:
                acc = self.stats.get_stat("acceleration")
                if keys[K_a] and not keys[K_d]:
                    self.a[0] = -acc
                elif keys[K_d] and not keys[K_a]:
                    self.a[0] = acc
                if keys[K_SPACE] and self.collisions[1] == 1:
                    self.v[1] = -self.stats.get_stat("jump_speed")
                self.move()

    # Draws pre-ui visuals
    def draw_pre_ui(self, rect):
        pos = pg.mouse.get_pos()
        global_pos = [pos[0] + rect.x, pos[1] + rect.y]

        display = pg.display.get_surface()
        # Draw shadow of placeable item if applicable
        if self.placement_range.collidepoint(*global_pos):
            item = self.inventory.get_current_item()
            if item.is_item and game_vars.items[item.item_id].placeable:
                tile = game_vars.tiles[game_vars.items[item.item_id].block_id]
                img = tile.image.copy().convert_alpha()
                img.fill((255, 255, 255, 128), None, BLEND_RGBA_MULT)
                # Find top left of current block in px
                img_pos = [(int(m / BLOCK_W) * BLOCK_W) - p for m, p in zip(global_pos, rect.topleft)]
                display.blit(img, img_pos)

        # Draw player
        display.blit(self.surface, (self.pos[0] - rect.x, self.pos[1] - rect.y))

        # Draw item being used
        if self.item_used is not None:
            center = [self.rect.centerx - rect.x, self.rect.centery - rect.y]
            self.item_used.use_anim(self.use_time, self.arm, self.used_left, center, rect)

    # Draws ui
    def draw_ui(self, rect):
        display = pg.display.get_surface()
        pos = pg.mouse.get_pos()

        # Draw inventory
        self.inventory.draw(pos)

        # Draw block ui
        if self.active_ui is not None:
            self.active_ui.draw()

        # Draw other UI
        life_text = "{} / {} HP".format(self.stats.hp, self.stats.get_stat("hp"))
        # Draw stats
        text = c.ui_font.render(life_text, 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.right = rect.w
        display.blit(text, text_rect)
        # TODO: Stats

        # Get minimap
        self.map.set_center([p / BLOCK_W for p in self.rect.center])
        self.map.draw_map(pg.Rect(c.screen_w - c.MAP_W, text_rect.h, c.MAP_W, c.MAP_W))

        # Draw selected item under cursor if there is one
        item = self.inventory.get_held_item()
        if item.is_item:
            img_rect = pg.Rect(0, 0, c.INV_IMG_W, c.INV_IMG_W)
            img_rect.center = pos
            img = game_vars.items[item.item_id].inv_img
            display.blit(img, img.get_rect(center=img_rect.center))
            text = c.inv_font.render(str(item.amnt), 1, (255, 255, 255))
            display.blit(text, text.get_rect(bottomright=img_rect.bottomright))

        # Draw 'You Died' text
        if self.respawn_counter > 0:
            font = c.get_scaled_font(c.MIN_W // 2, -1, "You Died")
            text = font.render("You Died", 1, (0, 0, 0))
            display.blit(text, text.get_rect(center=(c.screen_w // 2, c.screen_h // 2)))

    # Interprets events when the world map is open
    def run_map(self, events):
        pos = pg.mouse.get_pos()

        for e in events:
            if e.type == MOUSEBUTTONUP:
                # Spawn player at clicked location
                if e.button == BUTTON_RIGHT:
                    # Get screen center
                    center = (c.screen_w / 2, c.screen_h / 2)
                    # Get vector from screen center to mouse position in blocks
                    delta = [(pos[i] - center[i]) / self.map.zoom for i in (0, 1)]
                    # Calculate block position of the map position under the map
                    new_pos = [self.map.center[i] + delta[i] for i in (0, 1)]
                    world_dim = game_vars.world_dim()
                    for i in (0, 1):
                        if new_pos[i] < 0:
                            new_pos[i] = 0
                        elif new_pos[i] >= world_dim[i]:
                            new_pos[i] = world_dim[i] - 1
                        new_pos[i] *= BLOCK_W
                    self.set_pos(new_pos)
                    self.map_open = False
                # Zoom in on map
                elif e.button == BUTTON_WHEELUP:
                    if self.map.zoom < 10:
                        self.map.zoom += .5
                # Zoom out on map
                elif e.button == BUTTON_WHEELDOWN:
                    if self.map.zoom > 1:
                        self.map.zoom -= .5
            elif e.type == KEYUP:
                # Leave map
                if e.key == K_ESCAPE or e.key == K_m:
                    self.map.set_center([p / BLOCK_W for p in self.rect.center])
                    self.map_open = False

        # Move the map, drawing the map automatically puts center in world bounds
        move = game_vars.dt * 100
        keys = pg.key.get_pressed()
        if keys[K_a]:
            self.map.center[0] -= move
        if keys[K_d]:
            self.map.center[0] += move
        if keys[K_w]:
            self.map.center[1] -= move
        if keys[K_s]:
            self.map.center[1] += move

        self.move()

    # Draws ui when the world map is open
    def draw_map(self):
        self.map.draw_map(pg.display.get_surface().get_rect())

    def on_resize(self):
        if self.active_ui:
            self.active_ui.on_resize()
            if self.active_ui.can_drag:
                self.active_ui.rect.centerx = self.active_ui_pos[0] * c.screen_w
                self.active_ui.rect.centery = self.active_ui_pos[1] * c.screen_h

    def set_active_ui(self, ui):
        self.active_ui = ui
        if ui:
            self.active_ui_pos = [ui.rect.centerx / c.screen_w, ui.rect.centery / c.screen_h]

    def move(self):
        if game_vars.dt == 0:
            return

        self.immunity -= game_vars.dt

        # Do movement
        d = [0., 0.]
        # For each direction
        for i in range(2):
            # Calculate displacement
            d[i] = BLOCK_W * game_vars.dt * (self.v[i] + self.a[i] * game_vars.dt / 2)
            # Calculate velocity
            self.v[i] += self.a[i] * game_vars.dt
            spd = self.stats.get_stat("max_speed" + ("x" if i == 0 else "y"))
            if abs(self.v[i]) > spd:
                self.v[i] = copysign(spd, self.v[i])

        # Try to add a drag force, if something is manually setting force, this will have no effect
        if self.v[0] != 0:
            self.a[0] = -8 * self.v[0]

        prev_d, prev_pos = d.copy(), self.pos.copy()
        # Check for collisions and set new position
        game_vars.check_collisions(self.pos, self.dim, d)
        self.set_pos(self.pos)

        # Get actual change in position
        d = [self.pos[0] - prev_pos[0], self.pos[1] - prev_pos[1]]
        # Check collisions in x and y, a collision occurred if we should have moved but didn't
        self.collisions = [0, 0]
        for i in range(2):
            # If we didn't move the full distance, we hit something
            if abs(d[i] - prev_d[i]) > c.ROUND_ERR:
                self.collisions[i] = int(copysign(1, prev_d[i] - d[i]))
            # If we didn't move, check collision based on acceleration
            elif d[i] == prev_d[i] == 0 and self.a[i] != 0:
                truth = self.a[i] < 0
                if i == 0:
                    result = game_vars.touching_blocks_x(self.pos, self.dim, truth)
                else:
                    result = game_vars.touching_blocks_y(self.pos, self.dim, truth)
                self.collisions[i] = copysign(1, self.a[i]) if result else 0
            # Update velocity
            if self.collisions[i] != 0:
                self.v[i] = 0

        # Check if we are touching the ground
        if self.collisions[1] == 0:
            # If we are falling, add to our fall distance
            if self.v[1] > 0:
                self.fall_dist += d[1]
            else:
                self.fall_dist = 0
        elif self.collisions[1] == 1:
            # If our fall distance was great enough, do fall damage
            if self.fall_dist > 10 * BLOCK_W:
                self.hit(int(self.fall_dist / BLOCK_W) - 10, None)
            self.fall_dist = 0

    def set_pos(self, topleft):
        self.pos = list(topleft)
        self.rect.topleft = topleft
        self.placement_range.center = self.rect.center
        self.collection_range.center = self.rect.center

    def left_click(self):
        pos = pg.mouse.get_pos()
        if not self.inventory.left_click(pos):
            item = self.inventory.get_current_item()
            if item.is_item:
                item_obj = game_vars.items[item.item_id]
                self.used_left = game_vars.global_mouse_pos()[0] < self.rect.centerx
                if item_obj.left_click and (self.first_swing or item_obj.auto_use):
                    self.first_swing = False
                    # Use item
                    item_obj.on_left_click()
                    self.item_used = item_obj
                    self.use_time = item_obj.use_time
            else:
                self.break_block(*game_vars.global_mouse_pos(blocks=True))
                self.use_time = .5

    def right_click(self):
        pos = pg.mouse.get_pos()
        global_pos = game_vars.global_mouse_pos()
        if not self.inventory.right_click(pos):
            block_x, block_y = game_vars.get_topleft(*[p // BLOCK_W for p in global_pos])
            tile = game_vars.tiles[game_vars.get_block_at(block_x, block_y)]
            # First attempt to activate the tile
            # Make sure we didn't click the same block more than once
            if tile.clickable and self.placement_range.collidepoint(*global_pos) and \
                    (not tile.has_ui or self.active_ui is None or self.active_ui.block_pos != [block_x, block_y]):
                if tile.activate((block_x, block_y)):
                    return
            # Then try to drop the cursor item
            if self.inventory.selected_item.is_item:
                # Check if we dropped an item
                drop = self.inventory.drop_item()
                if drop is not None:
                    # This determines if we clicked to the left or right of the player
                    left = global_pos[0] < self.rect.centerx
                    game_vars.drop_item(drop, left)
            # If there is no cursor item, use the current hotbar item
            else:
                item = self.inventory.get_current_item()
                if item.is_item:
                    item_obj = game_vars.items[item.item_id]
                    if item_obj.right_click and (self.first_swing or item_obj.auto_use):
                        self.first_swing = False
                        # Use item
                        item_obj.on_right_click()
                        self.item_used = item_obj
                        self.use_time = item_obj.use_time

    def break_block(self, block_x, block_y):
        # Make sure we aren't hitting air
        block_x, block_y = game_vars.get_topleft(block_x, block_y)
        block = game_vars.get_block_at(block_x, block_y)
        if block == AIR:
            return
        tile = game_vars.tiles[block]
        # Make sure this block does not have a ui open
        if self.active_ui is not None and self.active_ui.block_pos == [block_x, block_y]:
            return False
        # Make sure the block is in range and check if we destroyed the block
        power = self.stats.get_stat("power")
        block_rect = Rect(block_x * BLOCK_W, block_y * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
        if self.placement_range.collidepoint(*block_rect.center) and tile.hit(block_x, block_y, power):
            return game_vars.break_block(block_x, block_y)
        return False

    def place_block(self, block_x, block_y, idx):
        # Check if we can place the block
        if self.placement_range.collidepoint(*game_vars.global_mouse_pos()):
            return game_vars.place_block(block_x, block_y, idx)
        return False

    def pick_up(self, item):
        if self.collection_range.colliderect(item.rect):
            space = self.inventory.room_for_item(item.info)
            if len(space) != 0:
                item.attract(self.rect.center)
                if abs(self.rect.centerx - item.rect.centerx) <= 1 and \
                        abs(self.rect.centery - item.rect.centery) <= 1:
                    return self.inventory.pick_up_item(item.info, space)
        else:
            item.pulled_in = False
        return False

    # Get current damage
    @property
    def damage(self):
        return self.stats.get_stat("damage")

    # Check if we hit the desired target
    def hit_target(self, rect):
        if self.item_used is None or self.item_used.polygon is None:
            return False
        else:
            return self.item_used.polygon.collides_polygon(rect)

    # Deals damage and knockback to the player
    def hit(self, dmg, centerx):
        defense = self.stats.get_stat("defense")
        dmg = max(0, dmg - defense)
        self.stats.hp -= dmg
        game_vars.add_damage_text(dmg, self.rect.center)
        if self.stats.hp <= 0:
            self.respawn_counter = 5
            self.map_open = False
        else:
            self.immunity = 1
            if centerx is not None:
                self.v = [copysign(3, self.rect.centerx - centerx), -3]

    def spawn(self):
        spawn = game_vars.world.spawn
        self.set_pos((spawn[0] * BLOCK_W, spawn[1] * BLOCK_W))
        for x in range(spawn[0], ceil(spawn[0] + self.dim[0])):
            for y in range(spawn[1], ceil(spawn[1] + self.dim[1])):
                if game_vars.get_block_at(x, y) not in game_vars.non_solid:
                    self.break_block(x, y)

    def respawn(self):
        self.stats.hp = self.stats.get_stat("hp")
        self.immunity = 5
        self.v = [0, 0]
        self.spawn()


def create_new_player(player_file):
    with open(player_file.full_file, "wb+") as file:
        file.write(new_inventory())
