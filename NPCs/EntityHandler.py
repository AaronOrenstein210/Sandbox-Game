# Created on 22 October 2019
# Handles all entities, including loose items

from random import randint
from pygame.display import get_surface
from NPCs.SpawnConditions import SpawnConditions
from NPCs.Entity import MOB, PLAYER, NEUTRAL
from Tools.constants import BLOCK_W
from Tools.tile_ids import AIR
from Tools import game_vars

# Keys must fit within 2 bytes
MAX_KEY = 256 ** 2 - 1


class EntityHandler:
    def __init__(self):
        self.entities = {}
        self.items = []
        # One list for each type of projectile
        self.projectiles = [[], [], []]

    def reset(self):
        self.entities.clear()
        self.items.clear()
        for arr in self.projectiles:
            arr.clear()

    def move(self, player):
        for item in self.items:
            item.move()
            if item.pick_up_immunity <= 0 and player.pick_up(item):
                self.items.remove(item)
        for key, entity in self.entities.items():
            # Check if a player projectile hit the entity
            for p in self.projectiles[PLAYER]:
                # If the projectile hit the enemy, delete it
                if entity.rect.colliderect(p.rect):
                    if p.hit():
                        self.projectiles[PLAYER].remove(p)
                    # If the enemy died, delete it
                    if entity.hit(p.dmg, p.rect.centerx):
                        self.entities.pop(key)
                        continue
            # Check if the player is swinging a weapon and it hit the entity
            if entity.immunity <= 0 and player.hit_target(entity.rect):
                # Check if we killed the entity
                if entity.hit(player.damage, player.rect.centerx):
                    self.entities.pop(key)
                    continue
            # If the player is not immune, check if the entity hit the player
            if not player.immune and entity.aggressive:
                if player.rect.colliderect(entity.rect):
                    player.hit(entity.stats.get_stat("damage"), entity.rect.centerx)
            # If the entity is still alive, move it
            entity.move()
        for projectile in self.projectiles[MOB]:
            # Move the projectile and check if it is still active
            if projectile.move():
                self.projectiles[MOB].remove(projectile)
            # Check if the player is swinging a weapon and it hit the projectile
            elif player.hit_target(projectile.rect) and projectile.hit():
                self.projectiles[MOB].remove(projectile)
            # Check if the projectile hit the player
            elif not player.immune and player.rect.colliderect(projectile.rect):
                player.hit(projectile.dmg, projectile.rect.centerx)
                if projectile.hit():
                    self.projectiles[MOB].remove(projectile)
        for p_type in [PLAYER, NEUTRAL]:
            arr = self.projectiles[p_type]
            for projectile in arr:
                # Move the projectile and check if it is still active
                if projectile.move():
                    arr.remove(projectile)

    def draw_display(self, rect):
        display = get_surface()
        for entity in self.entities.values():
            if rect.colliderect(entity.rect):
                display.blit(entity.img, (entity.pos[0] - rect.x, entity.pos[1] - rect.y))
        for item in self.items:
            if rect.colliderect(item.rect):
                display.blit(item.item.image, (item.pos[0] - rect.x, item.pos[1] - rect.y))
        for arr in self.projectiles:
            for p in arr:
                if rect.colliderect(p.rect):
                    display.blit(p.img, (p.pos[0] - rect.x, p.pos[1] - rect.y))

    def collides_with_entity(self, rect):
        for entity in self.entities.values():
            if entity.rect.colliderect(rect):
                return True
        return False

    def add_entity(self, entity):
        key = randint(0, MAX_KEY)
        while key in self.entities.keys():
            key = randint(0, MAX_KEY)
        self.entities[key] = entity

    def spawn(self):
        conditions = SpawnConditions()
        conditions.check_world()
        player_pos = [i // BLOCK_W for i in game_vars.player_pos()]
        spawners = game_vars.world.spawners
        world_dim = game_vars.world_dim()
        for x in range(max(0, player_pos[0] - 50), min(world_dim[0], player_pos[0] + 50)):
            if x in spawners.keys():
                for y in range(max(0, player_pos[1] - 50, min(world_dim[1], player_pos[1] + 50))):
                    if y in spawners[x].keys():
                        if randint(1, 10000) == 1:
                            entity = game_vars.tiles[spawners[x][y]].spawn((x, y), conditions)
                            if entity is not None:
                                self.add_entity(entity)


# Maybe used in future
def get_spawn_spaces_with_hole(center, r_inner, r_outer, walking):
    # X range
    v1_min, v1_max = max(0, center[0] - r_outer), min(game_vars.world_dim()[0], center[0] + r_outer)
    # Y bounds
    v2_min1, v2_max1 = max(0, center[1] - r_outer), max(0, center[1] - r_inner)
    v2_min2 = min(game_vars.world_dim()[1], center[1] + r_inner)
    v2_max2 = min(game_vars.world_dim()[1], center[1] + r_outer)

    v2_range_full = (range(v2_min1, v2_max2))
    v2_range_parts = (range(v2_min1, v2_max1), range(v2_min2, v2_max2))
    air = {}

    def add_val(v1_, v2_, val):
        if v1_ not in air.keys():
            air[v1_] = {}
        air[v1_][v2_] = val

    for v1 in range(v1_min, v1_max):
        for v2_range in v2_range_full if abs(v1 - center[1]) <= r_inner else \
                v2_range_parts:
            air_count = 0
            hit_block = False
            v2 = 0
            for v2 in v2_range:
                block = game_vars.get_block_at(*(v1, v2) if walking else (v2, v1))
                if block != AIR:
                    hit_block = True
                    if air_count > 0:
                        add_val(v1, v2 - air_count, air_count)
                    air_count = 0
                elif hit_block:
                    air_count += 1
            if air_count > 0:
                add_val(v1, v2 - air_count, air_count)
    return air
