# Created on 31 October 2019
# Defines functions and variables for the Entity class

from os.path import isfile
from sys import byteorder
import math
from random import randint, uniform
import pygame as pg
from Tools.constants import BLOCK_W, SPRITE_W, scale_to_fit, random_sign, get_angle, ROUND_ERR
from Tools import game_vars
from Player.Stats import Stats, ENEMY_STATS
from Objects.DroppedItem import DroppedItem
from Objects.ItemTypes import MagicContainer


# AI functions, takes an entity object as its input
def random_movement(entity):
    entity.time -= game_vars.dt
    # Check if we are standing on the ground
    if entity.collisions[1] == 1:
        # Check if we are ready to start/stop moving
        if entity.time <= 0:
            # We were stopped
            if entity.drag:
                entity.a[0] = entity.stats.get_stat("acceleration") * random_sign()
                entity.drag = False
                entity.time = uniform(2.5, 5)
            # We were moving
            else:
                entity.a[0] = 0
                entity.drag = True
                entity.time = uniform(1, 3)
        # Check if we need to jump
        if entity.collisions[0] != 0:
            entity.v[1] = -entity.stats.get_stat("jump_speed")
            entity.time = uniform(1, 3)


def follow_player(entity):
    # Check if we are standing on the ground
    if entity.collisions[1]:
        entity.a[0] = math.copysign(entity.stats.get_stat("acceleration"),
                                    game_vars.player_pos()[0] - entity.rect.centerx)
        # Check if we need to jump
        if entity.collisions[0] != 0:
            entity.v[1] = -entity.stats.get_stat("jump_speed")


def jump(entity, follow):
    # If we are on the ground, progress our timer and make sure we aren't moving
    if entity.collisions[1] == 1:
        entity.a[0], entity.v[0] = 0, 0
        entity.time -= game_vars.dt
        # If we are done waiting, jump
        if entity.time <= 0:
            if follow:
                entity.a[0] = math.copysign(entity.stats.get_stat("acceleration"),
                                            game_vars.player_pos()[0] - entity.rect.centerx)
            else:
                entity.a[0] = entity.stats.get_stat("acceleration") * random_sign()
            entity.v[0] = math.copysign(entity.stats.get_stat("max_speedx"), entity.a[0])
            entity.v[1] = -randint(5, entity.stats.get_stat("jump_speed"))
            entity.time = uniform(1, 2)


def fly_random(entity):
    if entity.collisions[1] == 1:
        # Launch off
        entity.a = [0, 0]
        entity.v[1] = -entity.stats.get_stat("jump_speed")
        entity.time = .5
    else:
        if entity.time > 0:
            entity.time -= game_vars.dt
        if entity.time <= 0:
            # Random y acceleration, more likely to go down
            entity.a[1] = entity.stats.get_stat("acceleration") * (-1 if randint(1, 5) >= 4 else 1)
            # Random x acceleration
            entity.a[0] = entity.stats.get_stat("acceleration") * random_sign()
            entity.time = uniform(.7, 1.4)


def fly_follow(entity):
    # Move towards player when we get to far away from the player
    pos = game_vars.player_pos()
    if entity.a[0] == 0 or abs(entity.rect.centerx - pos[0]) >= 5 * BLOCK_W:
        entity.a[0] = math.copysign(entity.stats.get_stat("acceleration"), pos[0] - entity.rect.centerx)
    if entity.a[1] == 0 or abs(entity.rect.centery - pos[1]) >= 2 * BLOCK_W:
        entity.a[1] = math.copysign(entity.stats.get_stat("acceleration"), pos[1] - entity.rect.centery)


# Draw all images with the entity going left!!!!
class Entity:
    def __init__(self, name="No Name", w=1, aggressive=False, rarity=1, img="", sprite="",
                 stats=Stats(ENEMY_STATS)):
        self.rarity = rarity
        # Stores entity info
        self.name = name
        self.stats = stats
        self.aggressive = aggressive
        # Toggles gravity's affect on this entity
        self.zero_gravity = False
        # Toggles if this entity interacts with blocks
        self.hits_blocks = True
        # Toggles knockback immunity
        self.no_knockback = False
        # Is a boss
        self.boss = False

        # Is there drag
        self.drag = False

        # Movement variables
        self.pos = [0., 0.]
        self.v = [0., 0.]
        self.a = [0., 20.]
        # Direction of image
        self.direction = math.copysign(1, self.v[0])
        self.time = 0
        self.immunity = 0
        self.collisions = [0, 0]

        # Load image
        if isfile(img):
            self.set_image(scale_to_fit(pg.image.load(img), w=w * BLOCK_W))
        else:
            self.img = pg.Surface((int(w * BLOCK_W), int(w * BLOCK_W)))
        self.dim = (w, self.img.get_size()[1] / BLOCK_W)
        # Load map sprite
        if sprite == "":
            self.sprite = None
        elif isfile(sprite) and (sprite.endswith(".png") or sprite.endswith(".jpg")):
            self.sprite = scale_to_fit(pg.image.load(sprite), w=SPRITE_W, h=SPRITE_W)
        else:
            self.sprite = pg.Surface((SPRITE_W, SPRITE_W))
        # Hit box
        self.rect = pg.Rect((0, 0), self.img.get_size())

    def get_block_pos(self):
        return [p / BLOCK_W for p in self.rect.center]

    def set_pos(self, x, y):
        self.pos = [x, y]
        self.rect.topleft = self.pos

    def move(self):
        if self.immunity > 0:
            self.immunity -= game_vars.dt

        # Figure out change in position
        d = [0, 0]
        dt = game_vars.dt
        for i in range(2):
            if not self.zero_gravity:
                d[i] = (self.v[i] + self.a[i] * dt / 2) * dt * BLOCK_W
                # Calculate velocity
                self.v[i] += self.a[i] * dt
                spd = self.stats.get_stat("max_speed" + ("x" if i == 0 else "y"))
                if abs(self.v[i]) > spd:
                    self.v[i] = math.copysign(spd, self.v[i])
            else:
                d[i] = self.v[i] * dt * BLOCK_W
        if self.direction * self.v[0] < 0:
            self.img = pg.transform.flip(self.img, True, False)
            self.direction *= -1

        # Try to add a drag force
        if self.drag and self.v[0] != 0:
            self.a[0] = -8 * self.v[0]

        self.collisions = [0, 0]
        # Update position
        if self.hits_blocks:
            prev_pos = self.pos.copy()
            prev_d = d.copy()
            # Check for collisions
            game_vars.check_collisions(self.pos, self.dim, d)
            self.set_pos(*self.pos)
            # Get actual change in position
            d = [self.pos[0] - prev_pos[0], self.pos[1] - prev_pos[1]]
            # Check collisions in x and y, a collision occurred if we should have moved but didn't
            for i in range(2):
                # If we didn't move the full distance, we hit something
                if abs(d[i] - prev_d[i]) > ROUND_ERR:
                    self.collisions[i] = math.copysign(1, prev_d[i] - d[i])
                # If we didn't move, check collision based on acceleration
                elif d[i] == prev_d[i] == 0 and self.a[i] != 0:
                    truth = self.a[i] < 0
                    if i == 0:
                        result = game_vars.touching_blocks_x(self.pos, self.dim, truth)
                    else:
                        result = game_vars.touching_blocks_y(self.pos, self.dim, truth)
                    self.collisions[i] = math.copysign(1, self.a[i]) if result else 0
                # Update velocity
                if self.collisions[i] != 0:
                    self.v[i] = 0
        else:
            self.set_pos(self.pos[0] + d[0], self.pos[1] + d[1])

        # Run ai, ai affects acceleration and velocity
        self.ai()

    # Code the ai here, either using combinations of preexisting
    # ones, ore making a new one
    def ai(self):
        random_movement(self)

    def set_image(self, new_img):
        if self.direction == -1:
            self.img = new_img
        else:
            self.img = pg.transform.flip(new_img, True, False)

    # Take damage, return if we are dead or not
    def hit(self, damage, centerx):
        self.stats.hp -= damage
        game_vars.add_damage_text(damage, self.rect.center)
        self.immunity = .5
        if not self.no_knockback:
            self.v = [math.copysign(5, self.rect.centerx - centerx), -5]
        if self.stats.hp < 0:
            # Get random drops and drop them
            items = self.get_drops()
            for item in items:
                game_vars.drop_item(DroppedItem(item), randint(0, 1) == 0, pos_=self.rect.center)
            return True
        return False

    def get_drops(self):
        return []

    def can_spawn(self, conditions):
        return True


class Boss(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.boss = True


# Projectile types
MOB, PLAYER, NEUTRAL = range(3)


class Projectile:
    def __init__(self, pos, target, w=1, img="", speed=5, damage=1, gravity=True):
        angle = get_angle(pos, target)

        self.type = PLAYER

        self.pos = list(pos)
        self.max_speed = speed
        self.v = [speed * math.cos(angle), speed * math.sin(angle)]
        self.a = [0, 20] if gravity else [0, 0]

        self.dmg = damage

        if isfile(img) and (img.endswith(".png") or img.endswith(".jpg")):
            self.img = scale_to_fit(pg.image.load(img), w=w * BLOCK_W)
        else:
            self.img = pg.Surface((w * BLOCK_W, w * BLOCK_W))
        self.dim = (w, self.img.get_size()[1] / BLOCK_W)
        self.rect = pg.Rect(pos, self.img.get_size())

        # Seeks out enemies
        self.homing = False
        # Is affected by gravity
        self.gravity = gravity
        # Can go through blocks
        self.hits_blocks = True
        # Bounces when hitting the ground
        self.bounce = False

        self.direction = -1

        # Number of times the projectile can hit an object
        self.num_hits = 1
        # Number of bounces until the projectile is destroyed
        self.max_bounces = 1
        # Length of time until the projectile is destroyed
        self.duration = -1
        self.time = 0

    # Returns true if the projectile is dead, false otherwise
    def move(self):
        if game_vars.dt == 0:
            return False

        # Check time
        if self.duration != -1:
            self.time += game_vars.dt
            if self.time >= self.duration:
                return True

        if self.homing:
            print("Recalculate v")

        # Calculate displacement
        dt = game_vars.dt
        d = [(self.v[i] + self.a[i] * dt / 2) * dt * BLOCK_W for i in range(2)]

        # Update velocity
        self.v = [v + a * dt for v, a in zip(self.v, self.a)]
        factor = self.max_speed / math.sqrt(self.v[0] ** 2 + self.v[1] ** 2)
        if factor < 1:
            self.v = [v * factor for v in self.v]

        if self.direction * self.v[0] < 0:
            self.direction *= -1
            self.img = pg.transform.flip(self.img, True, False)

        # If we can hit blocks, check for collisions
        if self.hits_blocks:
            prev_pos = self.pos.copy()
            prev_d = d.copy()
            game_vars.check_collisions(self.pos, self.dim, d)
            # Check if we hit a surface and if we should bounce
            self.set_pos(*self.pos)
            # Get actual change in position
            d = [self.pos[0] - prev_pos[0], self.pos[1] - prev_pos[1]]
            # Check collisions in x and y, a collision occurred if we should have moved but didn't
            for i in range(2):
                collision = 0
                # If we didn't move the full distance, we hit something
                if abs(d[i] - prev_d[i]) > ROUND_ERR:
                    collision = math.copysign(1, prev_d[i] - d[i])
                # If we didn't move, check collision based on acceleration
                elif d[i] == prev_d[i] == 0 and self.a[i] != 0:
                    truth = self.a[i] < 0
                    if i == 0:
                        result = game_vars.touching_blocks_x(self.pos, self.dim, truth)
                    else:
                        result = game_vars.touching_blocks_y(self.pos, self.dim, truth)
                    collision = math.copysign(1, self.a[i]) if result else 0
                # Update velocity
                if collision != 0:
                    if self.bounce:
                        self.v[i] *= -1
                        self.max_bounces -= 1
                        if self.max_bounces <= 0:
                            return True
                    else:
                        return True
        else:
            self.set_pos(self.pos[0] + d[0], self.pos[1] + d[1])

        return False

    # Returns true if the projectile hit its last time, false otherwise
    def hit(self):
        if self.num_hits == -1:
            return False
        else:
            self.num_hits -= 1
            return self.num_hits <= 0

    def set_pos(self, x, y):
        self.pos = [x, y]
        self.rect.topleft = self.pos
