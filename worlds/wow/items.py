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


def _is_gate_item_enabled(world, name: str) -> bool:
    option_name = next((opt for prefix, opt in _OPTIONAL_ITEM_PREFIXES if name.startswith(prefix)), None)
    return option_name is None or bool(getattr(world.options, option_name))


def count_enabled_gates_items(world) -> int:
    """Total gates_content_data item copies that create_gates_item_pool will
    actually pool for this generation's options -- i.e. how many locations
    with no matching AP location of their own (every gates-family item)
    need a filler sink location instead. Used by locations.py to size
    create_filler_locations so item/location parity holds exactly, not just
    in the worst case -- AP's generation pipeline has no generic step that
    tops up a short itempool to match location count (that only happens for
    start_inventory_from_pool item replacement, a fixed-size swap, not
    padding), so every option combination needs len(itempool) ==
    len(locations) to hold by construction, not just <=."""
    return sum(
        count
        for name, (_item_id, count) in gates_content_data.ITEMS.items()
        if _is_gate_item_enabled(world, name)
    )


def create_gates_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in gates_content_data.ITEMS.items():
        if not _is_gate_item_enabled(world, name):
            continue
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool

