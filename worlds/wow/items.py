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


# (name prefix, WoWOptions field name) pairs identifying gates.yaml items
# that belong to an optional gate family -- only pooled when the matching
# toggle is on. Riding and Flight Unlock items match no prefix here, so they
# fall through to the "always pooled" branch below (§5.1 treats them as
# mandatory Pipeline A content, not an optional family).
_OPTIONAL_ITEM_PREFIXES = [
    ("Armor Proficiency:", "proficiency_gating"),
    ("Weapon Proficiency:", "proficiency_gating"),
    ("Auction House Access", "access_gating"),
    ("Hearthstone Access", "access_gating"),
    ("Mailbox Access", "access_gating"),
    ("Progressive Bank Bag Slot:", "character_unlock_gating"),
    ("Talent Point Access", "character_unlock_gating"),
    ("Dual Spec Unlock", "character_unlock_gating"),
]


def create_gates_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in gates_content_data.ITEMS.items():
        option_name = next((opt for prefix, opt in _OPTIONAL_ITEM_PREFIXES if name.startswith(prefix)), None)
        if option_name is not None and not getattr(world.options, option_name):
            continue
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool

