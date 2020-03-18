# Created on 14 March 2020
# Defines classes for upgrade trees and upgrade paths
from sys import byteorder
import math
import pygame as pg
from Tools import constants as c, game_vars

CIRCLE_W = c.INV_IMG_W * 5
CIRCLE_R = c.INV_IMG_W * 2
MARGIN = c.INV_IMG_W
HALF_PI = math.pi / 2


class UpgradeTree:
    def __init__(self, paths):
        self.paths = paths

    def get_surface(self):
        count = len(self.paths)
        for path in self.paths:
            if not path.surface:
                path.draw()
        longest = max(p.surface.get_size()[1] for p in self.paths)
        s = pg.Surface((CIRCLE_W * count + (count - 1) * MARGIN, longest))
        x = 0
        for path in self.paths:
            if path.surface:
                s.blit(path.surface, (x, 0))
            x += CIRCLE_W + MARGIN
        return s

    # Attempt to click an upgrade, returns if anything changed
    def click(self, pos):
        i = 0
        while pos[0] >= 0:
            if pos[0] < CIRCLE_W:
                return self.paths[i].click(pos)
            i += 1
            pos[0] -= CIRCLE_W + MARGIN
        return False

    # Checks if we are hovering over an upgrade
    def check_hover(self, pos):
        i = 0
        while pos[0] >= 0:
            if pos[0] < CIRCLE_W:
                self.paths[i].check_hover(pos)
            i += 1
            pos[0] -= CIRCLE_W + MARGIN

    def apply(self, stats):
        for p in self.paths:
            p.apply(stats)

    def remove(self, stats):
        for p in self.paths:
            p.remove(stats)

    def load(self, data):
        for i in range(len(self.paths)):
            length = int.from_bytes(data[:1], byteorder)
            self.paths[i].load(data[1:length + 1])
            data = data[length + 1:]

    def write(self):
        data = bytearray()
        for p in self.paths:
            d = p.write()
            data += len(d).to_bytes(1, byteorder) + d
        return data

    # Returns a new upgrade tree object with the same upgrades
    def new_tree(self):
        return UpgradeTree([p.new_path() for p in self.paths])


class UpgradePath:
    def __init__(self, upgrades, imgs=()):
        self.upgrades = [arr for arr in upgrades if arr]
        self.level = 0
        # List of unlocked upgrades for current level
        self.unlocked = [False] * len(upgrades[self.level])
        # Requirements for current upgrade
        if self.upgrades and self.upgrades[0]:
            self.current_reqs = self.upgrades[0][0].amnt
        else:
            self.current_reqs = 0
        self.imgs = imgs
        self.surface = None

    # Draws entire upgrade path
    def draw(self):
        count = len(self.upgrades)
        if count > 0:
            self.surface = pg.Surface((CIRCLE_W, count * CIRCLE_W + (count - 1) * MARGIN))
            for lvl in range(len(self.upgrades)):
                self.draw_level(lvl)
        else:
            self.surface = pg.Surface((CIRCLE_W, CIRCLE_W))

    # Draws one specific level of upgrades
    def draw_level(self, lvl):
        if 0 <= lvl < len(self.upgrades):
            arr = self.upgrades[lvl]
            rect = pg.Rect(0, lvl * (CIRCLE_W + MARGIN), CIRCLE_W, CIRCLE_W)
            r = pg.Rect(0, 0, MARGIN, MARGIN)
            theta_incr = 2 * math.pi / len(arr)
            self.surface.fill((64, 0, 64), rect)
            # Draw progress
            if self.level > lvl or all(self.unlocked):
                pg.draw.circle(self.surface, (0, 100, 255), rect.center, CIRCLE_R, 3)
            else:
                num = self.unlocked.count(True)
                arc_r = pg.Rect(0, 0, CIRCLE_R * 2, CIRCLE_R * 2)
                arc_r.center = rect.center
                pg.draw.arc(self.surface, (0, 100, 255), arc_r, HALF_PI - theta_incr * num, HALF_PI, 3)
            for i, u in enumerate(arr):
                theta = HALF_PI - theta_incr * i
                r.center = (rect.centerx + CIRCLE_R * math.cos(theta), rect.centery - CIRCLE_R * math.sin(theta))
                self.surface.fill((255, 255, 255), r)
                # Draw required item
                if self.level < lvl or (self.level == lvl and not self.unlocked[i]):
                    img = game_vars.items[u.item].inv_img.copy()
                    img.fill((100, 100, 100), special_flags=pg.BLEND_RGB_MULT)
                else:
                    img = game_vars.items[u.item].inv_img
                self.surface.blit(img, img.get_rect(center=r.center))
                # Draw border if this is the current upgrade
                if self.level == lvl and not self.unlocked[i] and (i == 0 or self.unlocked[i - 1]):
                    pg.draw.rect(self.surface, (200, 200, 0), r, 2)

    # Checks for clicking an upgrade
    def click(self, pos):
        # Figure out which level we clicked on
        lvl = 0
        x, y = [CIRCLE_W // 2] * 2
        while lvl < len(self.upgrades) and pos[1] >= 0:
            if pos[1] <= CIRCLE_W:
                # Add item to current upgrade
                if lvl == self.level and not all(self.unlocked):
                    idx = sum(1 for u in self.unlocked if u)
                    theta_incr = 2 * math.pi / len(self.unlocked)
                    theta = HALF_PI - theta_incr * idx
                    # Check collision with the items before and after the click
                    r = pg.Rect(0, 0, MARGIN, MARGIN)
                    r.center = (x + CIRCLE_R * math.cos(theta), y - CIRCLE_R * math.sin(theta))
                    if r.collidepoint(*pos):
                        inv = game_vars.player.inventory
                        item, amnt = inv.get_cursor_item()
                        if item == self.upgrades[lvl][idx].item:
                            # Take everything in the player's hand
                            if amnt <= self.current_reqs:
                                inv.set_amnt_at(-1, -1, amnt=0)
                                self.current_reqs -= amnt
                            # Just take enough to upgrade
                            else:
                                inv.set_amnt_at(-1, -1, inv.selected_amnt - self.current_reqs)
                                self.current_reqs = 0
                            # Check if we've moved to the next upgrade
                            if self.current_reqs == 0:
                                self.unlocked[idx] = True
                                if idx < len(self.unlocked) - 1:
                                    self.current_reqs = self.upgrades[lvl][idx + 1].amnt
                                elif lvl < len(self.upgrades) - 1:
                                    self.level += 1
                                    self.current_reqs = self.upgrades[self.level][0].amnt
                                self.draw_level(lvl)
                                return True
                            else:
                                return False
                elif lvl < self.level:
                    print("Toggle image")
                break
            lvl += 1
            pos[1] -= CIRCLE_W + MARGIN
            y += CIRCLE_W + MARGIN
        return False

    # Checks if we are hovering over an upgrade
    def check_hover(self, pos):
        lvl = 0
        x, y = [CIRCLE_W // 2] * 2
        while lvl < len(self.upgrades) and pos[1] >= 0:
            if pos[1] <= CIRCLE_W:
                theta_incr = 2 * math.pi / len(self.upgrades[lvl])
                theta = (HALF_PI - c.get_angle((x, y), pos, pixels=True)) % (2 * math.pi)
                # Get closest upgrade on either side of the mouse
                idx1, idx2 = int(theta / theta_incr), math.ceil(theta / theta_incr) % len(self.upgrades[lvl])
                r = pg.Rect(0, 0, MARGIN, MARGIN)
                for idx in [idx1, idx2]:
                    angle = HALF_PI - theta_incr * idx
                    r.center = (x + CIRCLE_R * math.cos(angle), y - CIRCLE_R * math.sin(angle))
                    if r.collidepoint(*pos):
                        u = self.upgrades[lvl][idx]
                        # Completed level or current level and already upgraded
                        if self.level > lvl or (self.level == lvl and self.unlocked[idx]):
                            u.draw_description(0)
                        # Current level and the last upgrade has been purchased (aka current upgrade)
                        elif self.level == lvl and (idx == 0 or self.unlocked[idx - 1]):
                            u.draw_description(self.current_reqs)
                        # After current upgrade
                        else:
                            u.draw_description(u.amnt)
                        break
                break
            lvl += 1
            pos[1] -= CIRCLE_W + MARGIN
            y += CIRCLE_W + MARGIN

    def apply(self, stats):
        for level in range(self.level):
            for upgrade in self.upgrades[level]:
                upgrade.apply(stats)
        for i, unlocked in enumerate(self.unlocked):
            if not unlocked:
                break
            else:
                self.upgrades[self.level][i].apply(stats)

    def remove(self, stats):
        for level in range(self.level):
            for upgrade in self.upgrades[level]:
                upgrade.remove(stats)
        for i, unlocked in enumerate(self.unlocked):
            if not unlocked:
                break
            else:
                self.upgrades[self.level][i].remove(stats)

    def load(self, data):
        if len(data) < 4:
            print("Missing upgrade data")
            return data
        elif len(self.upgrades) == 0:
            print("No upgrades")
            self.level = 0
            self.unlocked = []
            self.current_reqs = 0
        else:
            self.level = int.from_bytes(data[:1], byteorder)
            upgrade_no = int.from_bytes(data[1:2], byteorder)
            self.unlocked = [False] * len(self.upgrades[self.level])
            self.unlocked[:upgrade_no] = [True] * upgrade_no
            self.current_reqs = int.from_bytes(data[2:4], byteorder)
        self.draw()
        return data[4:]

    def write(self):
        data = bytearray()
        # Current level of upgrade
        data += self.level.to_bytes(1, byteorder)
        # Current upgrade in that level
        data += sum(1 for u in self.unlocked if u).to_bytes(1, byteorder)
        # Requirements for current upgrade
        data += self.current_reqs.to_bytes(2, byteorder)
        return data

    # Returns a new upgrade path object with the same upgrades
    def new_path(self):
        return UpgradePath(self.upgrades, imgs=self.imgs)


class Upgrade:
    def __init__(self, item, amnt):
        self.item = item
        self.amnt = amnt

    @property
    def reqs(self):
        return [self.item, self.amnt]

    def get_description(self):
        return "No Description"

    def get_full_description(self, amnt_req):
        text = []
        # Get the description
        desc = self.get_description()
        for i in range(desc.count("\n")):
            idx = desc.index("\n")
            text.append(desc[:idx])
            desc = desc[idx + 1:]
        if amnt_req == 0:
            text.append("Upgraded!")
        else:
            text.append("Requires: {} {}".format(amnt_req, game_vars.items[self.item].name))
        return [line for line in text if line != ""]

    # Draws the description given number of items still required
    def draw_description(self, amnt_req):
        text = self.get_full_description(amnt_req)
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
        rect = s.get_rect(topleft=mouse_pos)
        # Make sure it isn't going off the right screen edge
        if rect.right > c.screen_w:
            rect.right = mouse_pos[0]
            # Don't move it so much that it goes to the left of the screen
            if rect.left < 0:
                rect.left = 0
        # Make sure it isn't going off the bottom of the screen
        if rect.bottom > c.screen_h:
            rect.bottom = mouse_pos[1]
            # Don't move it so much that it goes above the screen
            if rect.top < 0:
                rect.top = 0
        pg.display.get_surface().blit(s, rect)

    def apply(self, stats):
        pass

    def remove(self, stats):
        pass


class BaseUpgrade(Upgrade):
    def __init__(self, item, amnt, effect, stat):
        super().__init__(item, amnt)
        self.effect = effect
        self.stat = stat

    def get_full_description(self, amnt_in):
        text = super().get_full_description(amnt_in)
        text.insert(-1, "Effect: {0:+d} base ".format(self.effect) + self.stat)
        return text

    def apply(self, stats):
        if self.stat in stats.base.keys():
            stats.base[self.stat] += self.effect

    def remove(self, stats):
        if self.stat in stats.base.keys():
            stats.base[self.stat] -= self.effect


class AddUpgrade(Upgrade):
    def __init__(self, item, amnt, effect, stat):
        super().__init__(item, amnt)
        self.effect = effect
        self.stat = stat

    def get_full_description(self, amnt_in):
        text = super().get_full_description(amnt_in)
        text.insert(-1, "Effect: {0:+d} ".format(self.effect) + self.stat)
        return text

    def apply(self, stats):
        if self.stat in stats.add.keys():
            stats.add[self.stat] += self.effect

    def remove(self, stats):
        if self.stat in stats.add.keys():
            stats.add[self.stat] -= self.effect


class MultiUpgrade(Upgrade):
    def __init__(self, item, amnt, effect, stat):
        super().__init__(item, amnt)
        self.effect = effect
        self.stat = stat

    def get_full_description(self, amnt_in):
        text = super().get_full_description(amnt_in)
        text.insert(-1, "Effect: {0:+d}% ".format(int(self.effect * 100)) + self.stat)
        return text

    def apply(self, stats):
        if self.stat in stats.multi.keys():
            stats.multi[self.stat] += self.effect

    def remove(self, stats):
        if self.stat in stats.multi.keys():
            stats.multi[self.stat] -= self.effect
