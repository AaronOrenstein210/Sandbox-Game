# Created on 23 November 2019
# All mobs need to be defined here to create spawners for them

from NPCs.Entity import *
from NPCs.conditions import *
from Objects import MOB, PROJ
from Objects.Animation import OscillateAnimation
from Player.Stats import Stats, ENEMY_STATS, DEF_MOB
from Tools import game_vars
from Tools import item_ids as items
from Tools.constants import BLOCK_W, scale_to_fit


class Cat(Entity):
    def __init__(self):
        super().__init__(name="Cat", w=3, img=MOB + "cat.png", rarity=1,
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=15, max_speedx=2, jump_speed=9))

    def can_spawn(self, conditions):
        return conditions[SURFACE]


class Birdie(Entity):
    def __init__(self):
        super().__init__(name="Birdie", w=.75, aggressive=False, img=MOB + "birdie.png",
                         rarity=1,
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=5, max_speedx=5, max_speedy=5, acceleration=5,
                                     jump_speed=10))

    def ai(self):
        fly_random(self)

    def can_spawn(self, conditions):
        return True


class Zombie(Entity):
    def __init__(self):
        super().__init__(name="Zombie", w=1.5, aggressive=True, img=MOB + "zombie.png",
                         rarity=2, stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=50, damage=40, defense=5, max_speedx=5))

    def ai(self):
        follow_player(self)

    def can_spawn(self, conditions):
        return conditions[NIGHT]


class DoomBunny(Entity):
    def __init__(self):
        super().__init__(name="Doom Bunny", w=1, aggressive=True, img=MOB + "doom_bunny.png",
                         rarity=3,
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=5, damage=100, defense=1, jump_speed=15))

    def ai(self):
        jump(self, abs(game_vars.player_pos()[0] - self.rect.centerx) // BLOCK_W <= 10)

    def can_spawn(self, conditions):
        return True


class Helicopter(Entity):
    def __init__(self):
        super().__init__(name="Helicopter", w=1.5, aggressive=True, img=MOB + "helicopter.png",
                         rarity=1, stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=5, damage=25, defense=1, max_speedx=7,
                                               max_speedy=7, acceleration=5))

    def ai(self):
        fly_follow(self)

    def can_spawn(self, conditions):
        return True

    def get_drops(self):
        drops = [[items.LEAVES, randint(1, 5)]]
        if randint(1, 10) <= 7:
            drops.append([items.WOOD, randint(1, 5)])
        return drops


class Dragon(Boss):
    def __init__(self):
        super().__init__(name="Dragon", aggressive=True, w=5, rarity=3,
                         img=MOB + "dragon/dragon_0.png", sprite=MOB + "dragon/dragon_0.png",
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=100, damage=65, defense=10, max_speedx=15,
                                     max_speed_y=15))
        self.rising_anim = OscillateAnimation(folder=MOB + "dragon/", dim=self.img.get_size(), delay=.1)
        self.attacking_img = scale_to_fit(pg.image.load(MOB + "dragon_attack.png"), w=5 * BLOCK_W)
        self.zero_gravity = True
        self.hits_blocks = False
        self.no_knockback = True
        self.stage = 0

    def ai(self):
        pos = game_vars.player_pos()
        if self.stage == 0:
            self.v[1] = -15
            dx = self.rect.centerx - pos[0]
            if abs(dx) > 10 * BLOCK_W:
                self.v[0] = math.copysign(15, -dx)
            else:
                self.v[0] = 0
            # When we get high enough and close enough, switch modes
            if self.pos[1] < pos[1] - 10 * BLOCK_W:
                # 60% chance to go to stage one (diving)
                if randint(1, 5) > 2:
                    self.start_diving()
                # 40% chance to go to stage two (shoot fireballs)
                else:
                    self.time = 0
                    self.stage = 2
        # If we get too far away, switch modes
        elif self.stage == 1:
            dx = self.pos[0] - pos[0]
            dy = self.pos[1] - pos[1]
            if dy > 10 * BLOCK_W or (dy >= 0 and abs(dx) > 10 * BLOCK_W):
                self.set_image(self.rising_anim.get_frame())
                self.stage = 0
        elif self.stage == 2:
            num_shot_i = int(self.time)
            self.time += game_vars.dt
            num_shot_f = int(self.time)
            # Shoot fire balls!
            for i in range(num_shot_f - num_shot_i):
                game_vars.shoot_projectile(self.FireBall(self.rect.center, game_vars.player_pos(False)))
            if num_shot_f >= 9:
                self.start_diving()
            else:
                # Get distance to 8 blocks above and to the side of the player
                dy = pos[1] - BLOCK_W * 8 - self.rect.centery
                dx = pos[0] - self.rect.centerx
                dx -= math.copysign(BLOCK_W * 8, dx)
                self.v[0] = math.copysign(7, dx) if dx != 0 else 0
                self.v[1] = math.copysign(7, dy) if dy != 0 else 0
        # Update animation
        if self.stage == 0 or self.stage == 2:
            i = self.rising_anim.idx
            self.rising_anim.update()
            if i != self.rising_anim.idx:
                self.set_image(self.rising_anim.get_frame())

    def start_diving(self):
        self.rising_anim.reset()
        pos = game_vars.player_pos()
        theta = get_angle(self.rect.center, pos)
        self.v = [15 * math.cos(theta), 15 * math.sin(theta)]
        self.set_image(self.attacking_img)
        self.stage = 1

    def get_drops(self):
        drops = [[items.SHINY_STONE_1, randint(5, 15)],
                 [items.SHINY_STONE_2, randint(5, 10)]]
        if randint(0, 5) == 1:
            drops.append([items.SHINY_STONE_3, randint(1, 5)])
        return drops

    class FireBall(Projectile):
        def __init__(self, pos, target):
            super().__init__(pos, target, w=1.25, img=PROJ + "fire_ball.png", speed=15, damage=8)
            self.hurts_mobs = self.gravity = self.hits_blocks = False


class MainBoss(Boss):
    def __init__(self):
        super().__init__(name="Main Boss", aggressive=True, w=3, rarity=3,
                         img=MOB + "main_boss/shadow_dude_0.png", sprite=MOB + "main_boss/shadow_dude_0.png",
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=2, damage=100, defense=25, max_speedy=30))
        self.no_knockback = True
        self.stage = self.jump_count = self.launch_angle = 0
        self.launch_target = [0, 0]
        # Start in launch mode
        self.launch()

    def launch(self):
        self.stage = 0
        self.a = [0, 0]
        self.v[0] = 15 * math.cos(self.launch_angle)
        self.v[1] = 15 * math.sin(self.launch_angle)
        self.hits_blocks = False
        self.launch_target = game_vars.player_pos()
        self.launch_angle = get_angle(self.rect.center, self.launch_target)

    def ai(self):
        pos = game_vars.player_pos()
        if self.stage == 0:
            # If we aren't launching, move normally
            if self.hits_blocks:
                self.time += game_vars.dt
                # Check if we are switching to jump stage
                if self.time >= 7.75:
                    self.a = [0, 20]
                    if self.collisions[1] == 1:
                        self.v = [0, 0]
                        if self.time >= 8:
                            self.time = 0
                            self.stage = 1
                            self.v[1] = -self.stats.get_stat("max_speed")
                            self.hits_blocks = True
                    else:
                        self.time = 7.75
                else:
                    dx = pos[0] - self.rect.centerx
                    if dx != 0:
                        self.a[0] = math.copysign(10, dx)
                    if self.collisions[0] != 0 and self.collisions[1] == 1:
                        self.v[1] = -10
                        self.jump_count += 1
                        if self.jump_count > 2:
                            self.launch()
                    # Reset jumps if we aren't hitting something to the side
                    if self.collisions[0] == 0:
                        self.jump_count = 0
            else:
                # If we are in a block, keep launching
                if game_vars.in_block(self.pos, self.dim):
                    # If we went past out launch target, relaunch
                    angle = get_angle(self.rect.center, self.launch_target)
                    if abs(self.launch_angle - angle) > math.pi // 2:
                        self.launch_target = pos
                        self.launch_angle = get_angle(self.rect.center, pos)
                    self.v[0] = 15 * math.cos(self.launch_angle)
                    self.v[1] = 15 * math.sin(self.launch_angle)
                # Stop launching
                else:
                    self.a[1] = 20
                    self.v[1] = -5
                    self.hits_blocks = True
        elif self.stage == 1:
            if self.v[1] > -3:
                self.v[1] = 25
            if self.collisions[1] == 1:
                self.stage = 0
                self.v[1] = 0
                p = self.GroundP(self.pos, -1)
                p.set_pos(self.rect.centerx - p.dim[0] * BLOCK_W, self.rect.bottom - p.dim[1] * BLOCK_W)
                game_vars.shoot_projectile(p)
                p = self.GroundP(self.pos, 1)
                p.set_pos(self.rect.centerx, self.rect.bottom - p.dim[1] * BLOCK_W)
                game_vars.shoot_projectile(p)

    class GroundP(Projectile):
        def __init__(self, pos, direction):
            super().__init__(pos, [pos[0] + direction, pos[1]], img=PROJ + "dust_cloud.png", w=3, speed=1, damage=10,
                             gravity=False)
            self.hurts_mobs = False
            self.hits_blocks = False
            self.num_hits = -1
            self.duration = 3
