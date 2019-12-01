# Created on 31 October 2019
# Contains basic items that don't have any custom functionality
# Mobs for spawners must be defined in NPCs/Mobs.py

from Tools.constants import AIR_ID
from Objects.Tool import Tool
from Objects.Block import Block
from Objects.SpawnBlock import SpawnBlock
from Objects.Items import INV, USE
from Objects.Items.DimensionHopper import DimensionHopper
from NPCs.Mobs import *

AIR = Block(AIR_ID, name="Air")
DIRT = Block(1, name="Dirt", hardness=1, inv_img=INV + "dirt.png")
STONE = Block(2, name="Stone", hardness=2, inv_img=INV + "stone.png")
TEST_SWORD = Tool(3, name="Test Sword", damage=15, damage_type=0, use_time=.7,
                  inv_img=INV + "test_sword.png", use_img=USE + "test_sword.png")
TEST_PICKAXE = Tool(4, name="Test Pickaxe", damage=5, damage_type=0, break_blocks=True,
                    inv_img=INV + "test_pickaxe.png", use_img=USE + "test_pickaxe.png")
CAT = SpawnBlock(5, Cat)
ZOMBIE = SpawnBlock(6, Zombie)
DIMENSION_HOPPER = DimensionHopper(7)
