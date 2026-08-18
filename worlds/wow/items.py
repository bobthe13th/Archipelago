# Archipelago/worlds/wow/items.py
from BaseClasses import Item, ItemClassification
from .content_data import ITEMS
from . import core_loop_content_data
from . import gates_content_data


class WoWItem(Item):
    game = "World of Warcraft WotLK"


def create_item_pool(world) -> list:
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, item_id in ITEMS.items()
    ]


def create_core_loop_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in core_loop_content_data.ITEMS.items():
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool


def create_gates_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in gates_content_data.ITEMS.items():
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool

