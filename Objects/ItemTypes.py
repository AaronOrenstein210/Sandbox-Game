# Created on 4 December 2019
# Defines specific types of items
from sys import byteorder
from os.path import isfile, isdir
import math
import pygame as pg
from Tools.constants import ITEM_W, INV_IMG_W, scale_to_fit
from Tools.collision import Polygon
from Tools import game_vars, constants as c
from Tools.tile_ids import AIR
from Player.Stats import Stats, TOOL_STATS, WEAPON_STATS


class Item:
    def __init__(self, idx, img="", name=""):
        self.idx, self.name = idx, name
        self.max_stack = 999
        # Use time in seconds
        self.use_time = .3

        # Information booleans
        # Stores extra data
        self.has_data = False
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
        # Has an animation
        self.anim_idx = -1
        # Left or right click
        self.left_click = True
        self.right_click = False

        if isfile(img) and (img.endswith(".png") or img.endswith(".jpg")):
            s = pg.image.load(img)
            self.inv_img = scale_to_fit(s, INV_IMG_W, INV_IMG_W)
            self.image = scale_to_fit(s, w=ITEM_W)
        elif isdir(img):
            print("Animation")
        else:
            self.inv_img = pg.Surface((INV_IMG_W, INV_IMG_W))
            self.image = pg.Surface((ITEM_W, ITEM_W))
        # Used for blocks
        self.block_id = AIR
        # Attack box, if applicable
        self.polygon = None

        game_vars.items[self.idx] = self

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

    # Returns data for a new item
    def new(self):
        pass

    # Override this for special functionality and custom item consumption
    def on_left_click(self):
        if self.consumable:
            game_vars.player.inventory.use_item()

    def on_right_click(self):
        pass

    def on_tick(self):
        game_vars.player.use_time -= game_vars.dt

    # Returns a description of the item, each item class should override this
    def get_description(self, data):
        return ""

    # Returns the full item description, this should only be overridden by
    # items types that add extra information to the description, like damage for weapons
    def get_full_description(self, data):
        # Start with item name
        text = [self.name]
        # Add the description
        desc = self.get_description(data)
        for i in range(desc.count("\n")):
            idx = desc.index("\n")
            text.append(desc[:idx])
            desc = desc[idx + 1:]
        text.append(desc)
        # Add any item characteristics
        if self.placeable:
            text.append("Can be placed")
        return text

    # Returns a surface containing this object's description
    def draw_description(self, data):
        text = [string for string in self.get_full_description(data) if string != ""]
        font = c.ui_font
        # Figure out surface dimensions
        text_h = font.size("|")[1]
        w, h = 0, text_h * len(text)
        for string in text:
            str_w = font.size(string)[0]
            if str_w > w:
                w = str_w
        # Draw text onto the surface
        s = pg.Surface((w, h), pg.SRCALPHA)
        s.fill((0, 0, 0, 64))
        for i, string in enumerate(text):
            text_s = font.render(string, 1, (255, 255, 255))
            text_rect = text_s.get_rect(center=(w // 2, int(text_h * (i + .5))))
            s.blit(text_s, text_rect)
        # Draw the description at the mouse location
        mouse_pos = pg.mouse.get_pos()
        screen_dim = pg.display.get_surface().get_size()
        rect = s.get_rect(topleft=mouse_pos)
        # Make sure it isn't going off the right screen edge
        if rect.right > screen_dim[0]:
            rect.right = mouse_pos[0]
            # Don't move it so much that it goes to the left of the screen
            if rect.left < 0:
                rect.left = 0
        # Make sure it isn't going off the bottom of the screen
        if rect.bottom > screen_dim[1]:
            rect.bottom = screen_dim[1]
            # Don't move it so much that it goes above the screen
            if rect.top < 0:
                rect.top = 0
        pg.display.get_surface().blit(s, rect)


class Block(Item):
    def __init__(self, idx, block_id, **kwargs):
        super().__init__(idx, **kwargs)
        self.block_id = block_id
        self.consumable = True
        self.auto_use = True
        self.swing = True
        self.placeable = True

    def on_left_click(self):
        pos = game_vars.global_mouse_pos()
        pos = [p // c.BLOCK_W for p in pos]
        if game_vars.player.place_block(*pos, self.block_id) and self.consumable:
            game_vars.player.inventory.use_item()


# TODO: Weapon/Tool stats
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
        self.stats = Stats(WEAPON_STATS)

    def on_left_click(self):
        if self.consumable:
            game_vars.player.inventory.use_item()

    def get_full_description(self, data):
        text = super().get_full_description(data)
        # Add damage string
        text.insert(1, "{} Damage".format(self.damage))
        return text


class Tool(Weapon):
    def __init__(self, idx, power=1, **kwargs):
        super().__init__(idx, **kwargs)
        self.power = power
        self.breaks_blocks = True
        self.stats = Stats(TOOL_STATS)

    def on_left_click(self):
        pos = game_vars.global_mouse_pos(blocks=True)
        # Break blocks if necessary
        if self.breaks_blocks:
            if game_vars.player.break_block(*pos, self.power) and self.consumable:
                game_vars.player.inventory.use_item()
        elif self.consumable:
            game_vars.player.inventory.use_item()


class Armor(Item):
    def __init__(self, idx, upgrade_tree, **kwargs):
        super().__init__(idx, **kwargs)
        self.upgrade_tree = upgrade_tree
        self.max_stack = 1
        self.has_data = True

    def load_stats(self, stats, data):
        self.upgrade_tree.load(data)
        self.upgrade_tree.apply(stats)

    def new(self):
        return self.upgrade_tree.new_tree()


def rotate_point(p, d_theta):
    r = math.sqrt(pow(p[0], 2) + pow(p[1], 2))
    theta_i = math.asin(p[1] / r)
    # Arcsin can't tell what the sign of the x is so we have to check
    if p[0] < 0:
        theta_i = math.pi - theta_i
    theta_i += math.radians(d_theta)
    p[0], p[1] = r * math.cos(theta_i), -r * math.sin(theta_i)
