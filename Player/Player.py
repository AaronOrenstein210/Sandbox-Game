# Created on 22 October 2019
# Defines methods and variables for the player

import pygame as pg
from pygame.locals import *
from math import copysign, ceil
from Tools.constants import BLOCK_W, resize
from Tools import constants as c
from Tools import objects as o
from Tools.tile_ids import AIR
from Player.PlayerInventory import PlayerInventory
from Player.CraftingUI import CraftingUI
from Player.Stats import Stats
from NPCs.Entity import check_collisions, touching_blocks_y, touching_blocks_x
from NPCs.EntityHandler import EntityHandler
from Objects.DroppedItem import DroppedItem

# Mouse pos relative to the screen and to the world and viewing rect, updated every frame
pos, global_pos, rect = [0, 0], [0, 0], pg.Rect(0, 0, 0, 0)


class Player:
    def __init__(self, name):
        self.name = name
        # Drivers
        self.handler = EntityHandler()
        # Stats
        self.stats = Stats(hp=100, max_speed=[15, 20])
        # Inventory
        self.inventory = PlayerInventory()
        self.item_used, self.use_time = None, 0
        self.used_left = True
        self.first_swing = True
        # Sprite
        self.surface = pg.image.load("res/player/player_pig.png")
        dim = self.surface.get_size()
        self.dim = [1.5, 1.5 * dim[1] / dim[0]]
        w = c.MAP_W // 15
        self.sprite = pg.transform.scale(self.surface, [w, w * dim[1] // dim[0]])
        # Hit box
        self.rect = Rect(0, 0, BLOCK_W * self.dim[0], BLOCK_W * self.dim[1])
        self.surface = pg.transform.scale(self.surface, self.rect.size)
        self.arm = pg.Surface((int(self.rect.w / 4), int(self.rect.h / 3)), SRCALPHA)
        pg.draw.rect(self.arm, (200, 128, 0), (0, 0, self.arm.get_size()[0], self.arm.get_size()[1]))
        # This determines the area in which items are collected
        self.collection_range = Rect(0, 0, 6 * BLOCK_W, 6 * BLOCK_W)
        self.collection_range.center = self.rect.center
        # This determines the area that you can place blocks
        self.placement_range = Rect(0, 0, 7 * BLOCK_W, 7 * BLOCK_W)
        self.placement_range.center = self.rect.center
        # Physics variables
        self.pos = [0, 0]
        self.v = [0., 0.]
        self.a = [0, 1]
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
        # List of damage text boxes [[surface, center, duration], ...]
        self.dmg_text = []
        # If the world map is open or not
        self.map_open = False
        # Crafting UI
        self.crafting_ui = CraftingUI(self)

    def load(self):
        with open("saves/players/" + self.name + ".plr", "rb+") as data_file:
            data = data_file.read()
            self.inventory.load(data)

    def write(self):
        # See load() for info order
        with open("saves/players/" + self.name + ".plr", "wb+") as file:
            file.write(self.inventory.write())

    def get_cursor_block_pos(self):
        return [(p + r) // BLOCK_W for p, r in zip(pos, rect.topleft)]

    def run(self, events):
        # Check for quitting and resizing
        for e in events:
            if e.type == QUIT:
                return False
            elif e.type == VIDEORESIZE:
                resize(e.w, e.h)
                if self.active_ui is not None:
                    self.active_ui.on_resize()
                events.remove(e)
        # If wer are dead, decrement respawn counter
        if self.respawn_counter > 0:
            self.respawn_counter -= o.dt
            if self.respawn_counter <= 0:
                self.respawn()
        # Otherwise interperet events
        else:
            mouse = list(pg.mouse.get_pressed())
            keys = list(pg.key.get_pressed())

            global pos, global_pos, rect
            rect = o.world.get_view_rect(self.rect.center)
            pos = pg.mouse.get_pos()
            global_pos = (pos[0] + rect.x, pos[1] + rect.y)

            if self.map_open:
                for e in events:
                    if e.type == MOUSEBUTTONUP:
                        if e.button == BUTTON_RIGHT:
                            dim = pg.display.get_surface().get_size()
                            center = (dim[0] / 2, dim[1] / 2)
                            delta = [(pos[i] - center[i]) / o.world.map_zoom for i in (0, 1)]
                            new_pos = [o.world.map_off[i] + delta[i] for i in (0, 1)]
                            for i in (0, 1):
                                if new_pos[i] < 0:
                                    new_pos[i] = 0
                                elif new_pos[i] >= o.world.dim[i]:
                                    new_pos[i] = o.world.dim[i] - 1
                                new_pos[i] *= BLOCK_W
                            self.set_pos(new_pos)
                            self.map_open = False
                        elif e.button == BUTTON_WHEELUP or e.button == BUTTON_WHEELDOWN:
                            up = e.button == BUTTON_WHEELUP
                            if up and o.world.map_zoom < 10:
                                o.world.map_zoom += .5
                            elif not up and o.world.map_zoom > 1:
                                o.world.map_zoom -= .5
                    elif e.type == KEYUP:
                        if e.key == K_ESCAPE:
                            self.map_open = False
                o.world.move_map(keys)
            else:
                # Check if we need to open or close the crafting menu
                if self.inventory.open:
                    if self.active_ui is None:
                        self.active_ui = self.crafting_ui
                else:
                    if self.active_ui is self.crafting_ui:
                        self.active_ui = None
                # Send the events to the current active UI
                if self.active_ui is not None:
                    self.active_ui.process_events(events, mouse, keys)

                for e in events:
                    if self.use_time <= 0 and e.type == MOUSEBUTTONUP and \
                            (e.button == BUTTON_WHEELUP or e.button == BUTTON_WHEELDOWN):
                        up = e.button == BUTTON_WHEELUP
                        self.inventory.scroll(up)
                        if up and o.world.minimap_zoom < 5:
                            o.world.minimap_zoom += .5
                        elif not up and o.world.minimap_zoom > 1:
                            o.world.minimap_zoom -= .5
                    elif e.type == KEYUP or e.type == KEYDOWN:
                        up = e.type == KEYUP
                        # Try to jump
                        if e.key == K_SPACE and self.can_move:
                            if up:
                                self.a[1] = 1
                            else:
                                if touching_blocks_y(self.pos, self.dim, False):
                                    self.v[1] = -15
                        elif up and e.key == K_m:
                            self.map_open = True
                            o.world.map_off = [p / BLOCK_W for p in self.rect.center]
                        elif self.use_time <= 0 or e.key in [K_ESCAPE]:
                            self.inventory.key_pressed(e.key, up)

                # Item not in use and not touching tile ui
                if self.use_time <= 0 and \
                        (self.active_ui is None or not self.active_ui.rect.collidepoint(*pos)):
                    # Mouse click events
                    if mouse[BUTTON_LEFT - 1]:
                        self.left_click()
                    else:
                        self.first_swing = True
                        if mouse[BUTTON_RIGHT - 1]:
                            self.right_click()
                        else:
                            self.inventory.holding_r = 0

                # Key pressed events
                if self.can_move:
                    self.a[0] = 0 if not keys[K_a] ^ keys[K_d] else -1 if keys[K_a] \
                        else 1
                    if keys[K_SPACE]:
                        self.v[1] = -15

            # If we are using an item, let it handle the use time
            if self.item_used is not None:
                self.item_used.on_tick()
                # Check if we are done using the item
                if self.use_time <= 0:
                    self.item_used = None
            # Otherwise decrement the use time
            elif self.use_time >= 0:
                self.use_time -= o.dt

            # Update player and all entities/items/projectiles
            if self.can_move:
                self.move()

        # Update enitities
        self.handler.spawn()
        self.handler.move()
        # Check if anything hit the player
        if self.immunity <= 0 and self.respawn_counter <= 0:
            dmg, entity_x = self.handler.check_hit_player(self.rect)
            if dmg > 0:
                self.hit(dmg, entity_x)

        # Redraw the screen
        if self.map_open:
            display = pg.display.get_surface()
            display.fill(c.BACKGROUND)
            sprites = {(i / BLOCK_W for i in self.rect.center): self.sprite}
            map_ = o.world.get_map(display.get_size(), sprites=sprites)
            map_rect = map_.get_rect(center=display.get_rect().center)
            display.blit(map_, map_rect)
        else:
            self.draw_ui()
        return True

    def spawn(self):
        self.set_pos((o.world.spawn[0] * BLOCK_W, o.world.spawn[1] * BLOCK_W))
        for x in range(o.world.spawn[0], ceil(o.world.spawn[0] + self.dim[0])):
            for y in range(o.world.spawn[1], ceil(o.world.spawn[1] + self.dim[1])):
                self.break_block(x, y)

    def move(self):
        if o.dt == 0:
            return

        self.immunity -= o.dt

        dt = o.dt / 1000

        # Do movement
        d = [0., 0.]
        # For each direction
        for i in range(2):
            # Update the position and constrain it within our bounds
            d[i] = (BLOCK_W * 2 / 3) * (self.v[i] * dt)
            if self.a[i] == 0:
                if self.v[i] != 0:
                    self.v[i] += copysign(min(self.v[0] + (dt * 1), abs(self.v[i])), -self.v[i])
            else:
                self.v[i] += copysign(dt * 20, self.a[i])
                self.v[i] = copysign(min(abs(self.v[i]), self.stats.spd[i]), self.v[i])

        # Check for collisions and set new position
        temp = self.pos.copy()
        check_collisions(self.pos, self.dim, d)
        self.set_pos(self.pos)
        d = [self.pos[0] - temp[0], self.pos[1] - temp[1]]

        # Check if we are touching the ground
        if not touching_blocks_y(self.pos, self.dim, False):
            # If we are falling, add to our fall distance
            if self.v[1] > 0:
                self.fall_dist += d[1]
            else:
                self.fall_dist = 0
        else:
            # If we are touching the gruond and had a fall distance, do fall damage
            if self.fall_dist > 7 * BLOCK_W:
                self.hit(int(self.fall_dist / BLOCK_W) - 7, None)
            self.fall_dist = 0

        # Check if we hit a block above use and stop our upwards movement
        if touching_blocks_y(self.pos, self.dim, True):
            self.v[1] = 1

    def set_pos(self, topleft):
        self.pos = list(topleft)
        self.rect.topleft = topleft
        self.placement_range.center = self.rect.center
        self.collection_range.center = self.rect.center

    def left_click(self):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.inventory.left_click(pos)
        else:
            idx = self.inventory.get_held_item()
            if idx != -1:
                item = o.items[idx]
                self.used_left = global_pos[0] < self.rect.centerx
                if item.left_click and (self.first_swing or item.auto_use):
                    self.first_swing = False
                    # Use item
                    item.on_left_click()
                    self.item_used = item
                    self.use_time = item.use_time
                    if item.has_ui:
                        self.active_ui = item.UI()

    def right_click(self):
        if self.inventory.rect.collidepoint(pos[0], pos[1]):
            self.inventory.right_click(pos)
        else:
            block_x, block_y = o.world.get_topleft(*[p // BLOCK_W for p in global_pos])
            tile = o.tiles[o.world.blocks[block_y][block_x]]
            # Make sure we didn't click the same block more than once
            if tile.clickable and self.placement_range.collidepoint(*global_pos) and \
                    (self.active_ui is None or self.active_ui.block_pos != [block_x, block_y]):
                tile.activate((block_x, block_y))
            elif self.inventory.selected_item != -1:
                # Check if we dropped an item
                drop = self.inventory.drop_item()
                if drop is not None:
                    # This determines if we clicked to the left or right of the player
                    left = global_pos[0] < self.rect.centerx
                    self.drop_item(DroppedItem(*drop), left)
            else:
                item = self.inventory.get_held_item()
                if item != -1:
                    item = o.items[item]
                    if item.right_click and (self.first_swing or item.auto_use):
                        self.first_swing = False
                        # Use item
                        item.on_right_click()
                        self.item_used = item
                        self.use_time = item.use_time

    def break_block(self, block_x, block_y):
        # Make sure we aren't hitting air
        block_x, block_y = o.world.get_topleft(block_x, block_y)
        block = o.world.blocks[block_y][block_x]
        if block == AIR:
            return False
        tile = o.tiles[block]
        # Make sure this block does not have a ui open
        if self.active_ui is not None and self.active_ui.block_pos == [block_x, block_y]:
            return False
        block_rect = Rect(block_x * BLOCK_W, block_y * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[1])
        # Check if we can break the block
        if self.placement_range.collidepoint(*block_rect.center) and tile.on_break((block_x, block_y)):
            o.world.destroy_block(block_x, block_y)
            drops = tile.get_drops()
            for drop in drops:
                if drop[1] > 0:
                    # Drop an item
                    self.drop_item(DroppedItem(*drop), None, pos_=block_rect.center)
            return True
        return False

    def place_block(self, block_x, block_y, idx):
        tile = o.tiles[idx]
        # Calculate block rectangle
        block_rect = Rect(block_x * BLOCK_W, block_y * BLOCK_W, BLOCK_W * tile.dim[0], BLOCK_W * tile.dim[0])
        # Check if we can place the block
        if self.placement_range.collidepoint(*global_pos):
            if not self.rect.colliderect(block_rect) and \
                    not self.handler.collides_with_entity(block_rect) and \
                    tile.can_place((block_x, block_y)):
                o.world.place_block(block_x, block_y, idx)
                tile.on_place((block_x, block_y))
                return True
        return False

    # pos in pixels
    def drop_item(self, item_obj, left, pos_=None):
        if pos_ is None:
            pos_ = self.rect.center
        item_obj.drop(pos_, left)
        self.handler.items.append(item_obj)

    def pick_up(self, item):
        if self.collection_range.colliderect(item.rect):
            space = self.inventory.room_for_item(item)
            if len(space) != 0:
                item.attract(self.rect.center)
                if abs(self.rect.centerx - item.rect.centerx) <= 1 and \
                        abs(self.rect.centery - item.rect.centery) <= 1:
                    return self.inventory.pick_up_item(item, space)
        else:
            item.pulled_in = False
        return False

    def draw_ui(self):
        global rect
        rect = o.world.get_view_rect(self.rect.center)
        display = pg.display.get_surface()
        display.fill(o.get_sky_color())
        dim = display.get_size()
        # Draw blocks
        o.world.update_anim(rect)
        display.blit(o.world.surface, (0, 0), area=rect)
        # Draw shadow of placeable item if applicable
        if self.placement_range.collidepoint(*global_pos):
            item = self.inventory.get_held_item()
            if item != -1 and o.items[item].placeable:
                tile = o.tiles[o.items[item].block_id]
                img = tile.image.copy().convert_alpha()
                img.fill((255, 255, 255, 128), None, BLEND_RGBA_MULT)
                # Find top left of current block in px
                img_pos = [(int(m / BLOCK_W) * BLOCK_W) - p for m, p in zip(global_pos, rect.topleft)]
                display.blit(img, img_pos)
        # Draw all entities/projectiles/items, in that order
        self.handler.draw_display(rect)

        # Draw player
        display.blit(self.surface, (self.pos[0] - rect.x, self.pos[1] - rect.y))

        # Draw damage text
        i = 0
        for arr in self.dmg_text:
            # Decrement the duration
            arr[2] -= o.dt
            # Check if the text is finished
            if arr[2] <= 0:
                del self.dmg_text[i]
            else:
                # Move the text up
                arr[1][1] -= BLOCK_W * 1.5 * o.dt / 1000
                # Check if we need to blit it
                r = arr[0].get_rect(center=arr[1])
                if r.colliderect(rect):
                    display.blit(arr[0], (r.x - rect.x, r.y - rect.y))
                i += 1

        # Draw inventory
        display.blit(self.inventory.surface, (0, 0), area=self.inventory.rect)
        if self.inventory.rect.collidepoint(*pos):
            pos_ = [pos[0] - self.inventory.rect.x, pos[1] - self.inventory.rect.y]
            self.inventory.draw_hover_item(pos_)

        # Draw item being used
        if self.item_used is not None:
            center = [self.rect.centerx - rect.x, self.rect.centery - rect.y]
            self.item_used.use_anim(self.use_time, self.arm, self.used_left, center, rect)

        # Draw block ui
        if self.active_ui is not None:
            self.active_ui.draw()

        # Draw other UI
        life_text = str(self.stats.hp) + " / " + str(self.stats.max_hp) + " HP"
        # Draw stats
        text = c.ui_font.render(life_text, 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.right = rect.w
        display.blit(text, text_rect)

        # Get minimap
        player_c = [i / BLOCK_W for i in self.rect.center]
        minimap = o.world.get_minimap(player_c, sprites={tuple(player_c): self.sprite})
        display.blit(minimap, (dim[0] - c.MAP_W, text_rect.h))

        # Draw selected item under cursor if there is one
        cursor = self.inventory.get_cursor_display()
        if cursor is not None:
            display.blit(cursor, pos)

        # Draw 'You Died' text
        if self.respawn_counter > 0:
            font = c.get_scaled_font(c.MIN_W // 2, -1, "You Died")
            text = font.render("You Died", 1, (0, 0, 0))
            display.blit(text, text.get_rect(center=(dim[0] // 2, dim[1] // 2)))

    def hit(self, dmg, centerx):
        self.stats.hp -= dmg
        text = c.ui_font.render(str(dmg), 1, (255, 0, 128))
        self.dmg_text.append([text, list(self.rect.center), 1000])
        if self.stats.hp <= 0:
            self.respawn_counter = 5000
            self.map_open = False
        else:
            self.immunity = 1000
            if centerx is not None:
                self.v = [copysign(3, self.rect.centerx - centerx), -3]

    def attack(self, damage, polygon):
        # Change damage based on stats
        self.handler.check_hit_entities(self.rect.centerx, polygon, damage)

    def respawn(self):
        self.stats.hp = self.stats.max_hp
        self.immunity = 5000
        self.v = [0, 0]
        self.spawn()


def create_new_player(file_name):
    with open("saves/players/" + file_name + ".plr", "wb+") as file:
        file.write(PlayerInventory().new_inventory())
