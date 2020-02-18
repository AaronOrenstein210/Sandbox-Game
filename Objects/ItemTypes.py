# Created on 4 December 2019
# Defines specific types of items

from os.path import isfile
import math
import pygame as pg
from Tools.constants import ITEM_W, INV_IMG_W, scale_to_fit
from Tools.collision import Polygon
from Tools import objects as o
from Tools.tile_ids import AIR


class Item:
    def __init__(self, idx, img="", name=""):
        self.idx, self.name = idx, name
        self.max_stack = 999
        self.use_time = 300

        # Item use booleans
        # Is consumable (will decrease item amount)
        self.consumable = False
        # Will automatically start using again
        self.auto_use = False
        # Show a ui on interaction/usage
        self.has_ui = False
        # Can attack an enemy
        self.is_weapon = False
        # Should swing when used
        self.swing = False
        # Places a block on use
        self.placeable = False
        # Breaks a block on use
        self.breaks_blocks = False
        # Left or right click
        self.left_click, self.right_click = True, False

        if isfile(img):
            s = pg.image.load(img)
            self.inv_img = scale_to_fit(s, INV_IMG_W, INV_IMG_W)
            self.image = scale_to_fit(s, w=ITEM_W)
        else:
            self.inv_img = pg.Surface((INV_IMG_W, INV_IMG_W))
            self.image = pg.Surface((ITEM_W, ITEM_W))
        # Used for blocks
        self.block_id = AIR
        # Attack box, if applicable
        self.polygon = None

        o.items[self.idx] = self

    def use_anim(self, time_used, arm, left, player_center, rect):
        if self.swing:
            theta = 120 - (time_used * 165 / self.use_time)
            theta *= 1 if left else -1
        else:
            theta = 45 if left else -45
        # Calculate radius
        r = arm.get_size()[1] / 2
        # Arm bottom starts at 270 degrees, offset by theta
        arm_theta = math.radians(270 + theta)
        # Calculate difference from center to bottom of arm
        delta = [r * math.cos(arm_theta), -r * math.sin(arm_theta)]
        # Arm center of player center offset to the bottom of the arm
        arm_c = [player_center[0] - delta[0], player_center[1] - delta[1]]
        # Top of the arm is on the exact opposite side of the center
        arm_top = [arm_c[0] - delta[0], arm_c[1] - delta[1]]

        # Draw arm
        arm = pg.transform.rotate(arm, theta)
        pg.display.get_surface().blit(arm, arm.get_rect(center=arm_c))

        if not self.swing:
            # Draw item
            pg.display.get_surface().blit(self.image, self.image.get_rect(center=arm_top))
        else:
            img_dim = self.image.get_size()
            # Calculate center point and initial points of interest
            half_w, half_h = img_dim[0] / 2, img_dim[1] / 2
            # The tool center is the top of the arm offset by the bottom of the tool
            tool_bot = [0, -half_h]
            rotate_point(tool_bot, theta)
            tool_c = [arm_top[0] - tool_bot[0], arm_top[1] - tool_bot[1]]
            # Draw item
            img = pg.transform.rotate(self.image, theta)
            pg.display.get_surface().blit(img, img.get_rect(center=tool_c))
            if self.is_weapon:
                # A-D form the tool hit box
                a, b, c, d = [-half_w, half_h], [half_w, half_h], [half_w, -half_h], [-half_w, -half_h]
                for p in (a, b, c, d):
                    # Rotate the points
                    rotate_point(p, theta)
                    # Offset them by the center
                    p[0] += tool_c[0] + rect.x
                    p[1] += tool_c[1] + rect.y
                self.polygon = Polygon([a, b, c, d])

    # Override this for special functionality and custom item consumption
    def on_left_click(self):
        if self.consumable:
            o.player.inventory.use_item()

    def on_right_click(self):
        pass

    def on_tick(self):
        o.player.use_time -= o.dt


class Block(Item):
    def __init__(self, idx, block_id, **kwargs):
        Item.__init__(self, idx, **kwargs)
        self.block_id = block_id
        self.consumable = True
        self.auto_use = True
        self.swing = True
        self.placeable = True

    def on_left_click(self):
        if o.player.place_block(*o.player.get_cursor_block_pos(), self.block_id) and self.consumable:
            o.player.inventory.use_item()


class Weapon(Item):
    def __init__(self, idx, damage=1, damage_type=0, projectiles=(), **kwargs):
        Item.__init__(self, idx, **kwargs)
        self.swing = True
        self.is_weapon = True
        self.damage = damage
        self.damage_type = damage_type
        self.projectiles = projectiles
        self.max_stack = 1
        # Get inventory image
        from pygame.transform import scale, rotate
        from Tools.constants import INV_IMG_W
        self.inv_img = scale(rotate(self.image, 45), (INV_IMG_W, INV_IMG_W))

    def on_left_click(self):
        # Break blocks if necessary
        if self.breaks_blocks:
            if o.player.break_block(*o.player.get_cursor_block_pos()) and self.consumable:
                o.player.inventory.use_item()
        elif self.consumable:
            o.player.inventory.use_item()

    def use_anim(self, time_used, arm, left, player_center, rect):
        Item.use_anim(self, time_used, arm, left, player_center, rect)
        o.player.attack(self.damage, self.polygon)


def rotate_point(p, d_theta):
    r = math.sqrt(pow(p[0], 2) + pow(p[1], 2))
    theta_i = math.asin(p[1] / r)
    # Arcsin can't tell what the sign of the x is so we have to check
    if p[0] < 0:
        theta_i = math.pi - theta_i
    theta_i += math.radians(d_theta)
    p[0], p[1] = r * math.cos(theta_i), -r * math.sin(theta_i)


def create_block_from_zip(idx, block_idx, name, file_name):
    import os
    if file_name.endswith(".zip") and os.path.isfile(file_name):
        from zipfile import ZipFile
        with ZipFile(file_name) as file:
            img_name = file.namelist()[0]
            file.extract(img_name)
            Block(idx, block_idx, name=name, img=img_name)
            os.remove(img_name)
