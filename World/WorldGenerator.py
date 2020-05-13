# Created on 22 October 2019
# Generates the world

from random import uniform, choice
from Tools import item_ids as items, tile_ids as tiles, game_vars
from Tools.constants import update_dict
from World.World import World, IdleWorld
from UI.Operations import SaveWorld

WORLD_DIMS = {items.SMALL_WORLD: [500, 250], items.MED_WORLD: [750, 375], items.LARGE_WORLD: [1000, 500]}
NUM_STRUCTURES = {items.SMALL_WORLD: 1, items.MED_WORLD: 1, items.LARGE_WORLD: 2}


# Generates a new world
# Takes in the world object to generate on
# and a list of items that modify the world
def generate_world(world, modifiers=()):
    if isinstance(world, IdleWorld):
        world.new_world([100, 100])
        # Make the floor glass
        world.blocks[50:, :] = tiles.GLASS
        # Add the portal
        world.blocks[47:50, 49:51] = [tiles.PORTAL, -100], [-1, -101], [-2, -202]
        update_dict(49, 47, bytearray(8), world.block_data)
        # Set spawn
        world.spawn = [49, 47]
    elif isinstance(world, World):
        num_structs = 0
        biomes = dict.fromkeys(game_vars.biomes.keys(), 0)
        chance_sum = 0
        # This lets us know if the world size was set
        world.num_blocks = -1
        # Loop through modifier items
        for item in modifiers:
            # Bonus structure in world
            if item == items.BONUS_STRUCTURE:
                num_structs += 1
            # Set world size
            elif item in WORLD_DIMS.keys():
                world.new_world(WORLD_DIMS[item])
                num_structs += NUM_STRUCTURES[item]
            # Add biome
            elif item in game_vars.biomes.keys():
                biomes[item] += 1
                chance_sum += 1
        # Make sure world size was set, default small world
        if world.num_blocks == -1:
            world.new_world(WORLD_DIMS[items.LARGE_WORLD])
            num_structs += NUM_STRUCTURES[items.LARGE_WORLD]
        surface_heights = [-1] * world.dim[0]
        # Make sure biome chances were set, default forest biome
        if chance_sum == 0:
            biomes[items.FOREST] += 1
            chance_sum += 1
        # Spawn random biomes
        biome_list = []
        biome = w = -1
        x = 0
        while x < world.dim[0]:
            num = uniform(0, chance_sum)
            for key in biomes.keys():
                if num > biomes[key]:
                    num -= biomes[key]
                else:
                    # Get random biome width
                    biome_w = int(world.dim[0] * uniform(9, 11) / 100)
                    # If it is close enough to or past the world edge, set it to the edge
                    if x + biome_w >= world.dim[0] * 19 // 20:
                        biome_w = world.dim[0] - x
                    # Generate the biome or add to its length
                    if biome != key:
                        if biome != -1:
                            game_vars.biomes[biome].generate(world, surface_heights, x - w, w)
                        biome = key
                        w = biome_w
                        if biome not in biome_list:
                            biome_list.append(biome)
                    else:
                        w += biome_w
                    x += biome_w
                    break
        game_vars.biomes[biome].generate(world, surface_heights, x - w, w)
        # Generate structures
        structure_list = []
        for key in game_vars.structures:
            if game_vars.structures[key].can_spawn(biome_list):
                structure_list.append(key)
        if len(structure_list) > 0:
            structure_rects = []
            for i in range(num_structs):
                game_vars.structures[choice(structure_list)].generate(world, surface_heights, structure_rects)
        world.spawn = [world.dim[0] // 2, min(surface_heights[world.dim[0] // 2:world.dim[0] // 2 + 2]) - 2]
    # Save world
    SaveWorld(world).run_now()
