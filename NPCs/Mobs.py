# Created on 23 November 2019
# All mobs need to be defined here to create spawners for them

from NPCs.Entity import *
from NPCs.conditions import *
from Objects import MOB, PROJ
from Objects.Animation import OscillateAnimation
from Objects.ItemTypes import ItemInfo
from Player.Stats import Stats, ENEMY_STATS, DEF_MOB
from Tools import game_vars
from Tools import item_ids as items, tile_ids as tiles
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
                         rarity=2,
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=50, damage=40, defense=5))

    def ai(self):
        follow_player(self)

    def can_spawn(self, conditions):
        return conditions[NIGHT]


class DoomBunny(Entity):
    def __init__(self):
        super().__init__(name="Doom Bunny", w=1, aggressive=True, img=MOB + "doom_bunny.png",
                         rarity=3,
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=5, damage=100, defense=1, jump_speed=15,
                                     maxspeedx=7))

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
        drops = [ItemInfo(items.LEAVES, randint(1, 5))]
        if randint(1, 10) <= 7:
            drops.append(ItemInfo(items.WOOD, randint(1, 5)))
        return drops


class Mage(Entity):
    MAX_DX = 5 * BLOCK_W

    def __init__(self, element=MagicContainer.NONE, level=1):
        element_name = MagicContainer.ELEMENT_NAMES[element]
        super().__init__(name="%s Mage" % element_name, w=1.5, img="%s%s_mage.png" % (MOB, element_name),
                         stats=Stats(ENEMY_STATS, defaults=DEF_MOB, hp=100, max_speedx=1))
        self.element = element
        self.level = level
        self.magic = 0
        self.target = (-1, -1)
        self.transfer_cooldown = 0

    @property
    def magic_bytes(self):
        return math.ceil(math.log2(self.capacity) / 8)

    @property
    def capacity(self):
        return int(100 * 2.5 ** (self.level - 1))

    @property
    def production(self):
        return 3 ** (self.level - 1)

    @property
    def bound(self):
        return self.target != (-1, -1)

    def set_target(self, pos):
        self.target = pos

    def ai(self):
        self.time -= game_vars.dt
        # Check if we are standing on the ground
        if self.collisions[1] == 1:
            too_far = self.bound and not self.drag and abs(
                self.rect.centerx - self.target[0] * BLOCK_W) >= self.MAX_DX
            # Check if we are ready to start/stop moving
            if self.time <= 0 or too_far:
                # We were stopped
                if self.drag:
                    if self.bound:
                        self.a[0] = math.copysign(self.stats.get_stat("acceleration"),
                                                  self.target[0] * BLOCK_W - self.rect.centerx)
                    else:
                        self.a[0] = self.stats.get_stat("acceleration") * random_sign()
                    self.drag = False
                    max_t = self.MAX_DX / self.stats.get_stat("max_speedx")
                    self.time = uniform(max_t / 3, max_t * .9)
                # We were moving
                else:
                    self.a[0] = 0
                    self.drag = True
                    self.time = uniform(1, 3)
            # Check if we need to jump
            if self.collisions[0] != 0:
                self.v[1] = -self.stats.get_stat("jump_speed")
                self.time = uniform(1, 3)
        # Increment magic
        self.magic = min(self.capacity, self.magic + self.production * game_vars.dt)
        if self.magic >= 5 and self.bound and self.transfer_cooldown <= 0:
            x, y = game_vars.get_topleft(*self.target)
            tile_id = game_vars.get_block_at(x, y)
            if tile_id != tiles.PEDESTAL:
                self.target = (-1, -1)
            else:
                tile = game_vars.tiles[tile_id]
                transfer = min(self.production, self.magic, tile.get_space(x, y))
                if transfer > 0:
                    game_vars.shoot_projectile(self.P1(transfer, self.rect.center, (x, y)))
                    self.transfer_cooldown = 1
        elif self.transfer_cooldown > 0:
            self.transfer_cooldown -= game_vars.dt

    # Format(#bytes): num_bytes(1) element(1) level(1) magic(magic_bytes) is_bound(1) bound_coords(2+2)
    def write(self):
        data = self.element.to_bytes(1, byteorder) + self.level.to_bytes(1, byteorder)
        data += int(self.magic).to_bytes(self.magic_bytes, byteorder)
        data += self.bound.to_bytes(1, byteorder)
        if self.bound:
            for p in self.target:
                data += p.to_bytes(2, byteorder)
        data = len(data).to_bytes(1, byteorder) + data
        return data

    class P1(Projectile):
        HIT_RAD = BLOCK_W / 2

        def __init__(self, magic, pos, target_block):
            super().__init__(pos, [t * BLOCK_W for t in target_block], img=PROJ + "fire_ball.png", w=.5, gravity=False,
                             damage=0, speed=3)
            self.hits_blocks = False
            self.type = NEUTRAL
            self.target = target_block
            self.magic = magic

        # Check if we hit our target
        def move(self):
            if super().move():
                return True
            x, y = game_vars.get_topleft(*self.target)
            tile_id = game_vars.get_block_at(x, y)
            if tile_id != tiles.PEDESTAL:
                return True
            else:
                tile = game_vars.tiles[tile_id]
                rect = pg.Rect((x * BLOCK_W, y * BLOCK_W), [i * BLOCK_W for i in tile.dim])
                if abs(self.rect.centerx - rect.centerx) < self.HIT_RAD and abs(
                        self.rect.centery - rect.centery) < self.HIT_RAD:
                    tile.add_magic(x, y, self.magic)
                    return True
            return False


def load_mage(data):
    if not data or len(data) < 2:
        print("Missing mage element and level")
        return Mage()
    element = int.from_bytes(data[:1], byteorder)
    level = int.from_bytes(data[1:2], byteorder)
    data = data[2:]

    # Initialize object
    mage = Mage(element, level)

    if len(data) < mage.magic_bytes:
        print("Missing mage magic amount")
        return mage
    mage.magic = int.from_bytes(data[:mage.magic_bytes], byteorder)
    data = data[mage.magic_bytes:]

    if len(data) < 1:
        print("Missing if the mage is bound")
    else:
        is_bound = bool.from_bytes(data[:1], byteorder)
        data = data[1:]
        if is_bound:
            if len(data) < 4:
                print("Missing mage target")
            else:
                mage.target = (int.from_bytes(data[:2], byteorder), int.from_bytes(data[2:4], byteorder))
                # TODO: Find open space
                mage.pos = (mage.target[0] * BLOCK_W + uniform(-mage.MAX_DX, mage.MAX_DX),
                            (mage.target[1] - mage.dim[1]) * BLOCK_W)

    return mage


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
            self.rising_anim.update(game_vars.dt)
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
        drops = [ItemInfo(items.SHINY_STONE_1, randint(5, 15)),
                 ItemInfo(items.SHINY_STONE_2, randint(5, 10))]
        if randint(0, 5) == 1:
            drops.append([items.SHINY_STONE_3, randint(1, 5)])
        return drops

    class FireBall(Projectile):
        def __init__(self, pos, target):
            super().__init__(pos, target, w=1.25, img=PROJ + "fire_ball.png", speed=15, damage=8, gravity=False)
            self.hurts_mobs = self.hits_blocks = False
            self.type = MOB


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
            self.type = MOB
