# Archipelago/worlds/wow/items.py
from BaseClasses import Item, ItemClassification
from .content_data import ITEMS


class WoWItem(Item):
    game = "World of Warcraft WotLK"


def create_item_pool(world) -> list:
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, item_id in ITEMS.items()
    ]
