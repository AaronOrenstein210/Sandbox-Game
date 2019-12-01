# Created 8 November 2019
# Tools are items that are used but not places

from os.path import isfile
from pygame import Surface, SRCALPHA
from pygame.transform import rotate, scale
from pygame.image import load
from math import sqrt, asin, cos, sin, pi, radians
from Objects.Item import Item
from Tools.collision import Polygon
from Tools.constants import BLOCK_W, ITEM_W

MELEE, RANGED, MAGIC, THROWING, SUMMONING = 0, 1, 2, 3, 4


class Tool(Item):
    def __init__(self, idx, name="No Name", damage=0, damage_type=MELEE, use_time=.3,
                 projectiles=(), break_blocks=False, auto_swing=True, inv_img="", use_img=""):
        Item.__init__(self, idx, name, 1, 1, use_time, damage_type == THROWING)
        # Information variables
        self.break_blocks = break_blocks
        self.auto_swing = True if self.break_blocks else auto_swing
        self.damage, self.use_time = damage, use_time
        self.damage_type = damage_type
        self.projectiles = projectiles
        # Load inventory icon if available
        if isfile(inv_img):
            self.icon = load(inv_img)
        # Load image if available
        if isfile(use_img):
            self.image = load(use_img)
            size = self.image.get_size()
            frac = BLOCK_W / min(size)
            self.image = scale(self.image, (int(frac * size[0]), int(frac * size[1])))

    def get_dropped_display(self):
        return scale(self.icon, (ITEM_W, ITEM_W))

    def clone(self, amnt):
        return Tool(self.idx, self.name, self.damage, self.damage_type)

    def use_anim(self, time_used, arm, left, player_center):
        arm_dim = arm.get_size()
        img_dim = self.image.get_size()
        w, h = max(img_dim[0], arm_dim[0]), img_dim[1] + arm_dim[1]
        s = Surface((w, h), SRCALPHA)
        s.blit(arm, (int((w / 2) - (arm_dim[0] / 2)), img_dim[1]))
        s.blit(self.image, (0, 0))

        theta = 120 - (time_used * 165 / self.use_time)
        theta *= 1 if left else -1

        # Calculate center point and initial points of interest
        half_w, half_h = int(w / 2), int(h / 2)
        # A-D form the tool hit box, E is the end of the arm that attaches to the player
        a, b, c, d, e = [-half_w, half_h], [half_w, half_h], [half_w, -half_h], [-half_w, -half_h], [0, -half_h]
        # Rotate the points
        for p in (a, b, c, d, e):
            r = sqrt(pow(p[0], 2) + pow(p[1], 2))
            theta_i = asin(p[1] / r)
            if p[0] < 0:
                theta_i = pi - theta_i
            theta_i += radians(theta)
            p[0], p[1] = int(r * cos(theta_i)), int(-r * sin(theta_i))
        # Calculate center of tool image (player center offset by end of arm)
        e = [player_center[0] - e[0], player_center[1] - e[1]]
        # Offset corners by e (image center)
        for p in (a, b, c, d):
            p[0] += e[0]
            p[1] += e[1]

        self.polygon = Polygon([a, b, c, d])

        return rotate(s, theta), e
