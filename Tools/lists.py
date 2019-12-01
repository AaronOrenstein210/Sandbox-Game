# Created on 2 November 2019
# This file contains various groupings of items, mobs, etc.

from Objects.Items import items as i_
from Objects.Item import Item

items = {}
for var in vars(i_).values():
    if isinstance(var, Item):
        items[var.idx] = var
