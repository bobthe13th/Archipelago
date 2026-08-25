# Archipelago/worlds/wow/slot_data.py
"""Builds this world's fill_slot_data() payload. First introduced by Task 23
(docs/m4-plan.md Group 6) -- earlier tasks flagged that whichever of
Task 21/23/28 landed first should create this as a small, extensible
dict-building function, since several later tasks (Task 21's
starting_choice, Task 28's autobalance settings, Task 23/24's per-mode
config) each need to add their own key without fighting over one growing
inline dict literal. Add a new _add_x_to_slot_data(world, data) helper per
concern and call it from build_slot_data below."""
from __future__ import annotations

from . import locations as locations_module

# Finding I3 (M4.7 final review): the only two families whose locations the
# C++ side's trigger-lookup maps (QUEST_ID_TO_LOCATION_ID /
# VENDOR_SLOT_TO_LOCATION_ID, Task 1) can ever resolve -- see
# _ap_item_display_eligible_location_names below.
_AP_ITEM_DISPLAY_FAMILY_KEYS = frozenset({"quest_rewards", "vendor_stock"})


def build_slot_data(world) -> dict:
    data: dict = {}
    _add_instance_clear_mode(world, data)
    _add_ap_item_display_data(world, data)
    _add_vendor_check_repeat_behavior(world, data)
    return data


def _add_instance_clear_mode(world, data: dict) -> None:
    # Task 23: mirrors the resolved InstanceClearMode choice so a connected
    # worldserver COULD read it from the AP session in the future -- as of
    # this task, the module still has no slot_data parsing at all (the same
    # known gap Finding #10 documents for every other option), so an
    # operator must still mirror this by hand via
    # Archipelago.InstanceClearMode until that gap is closed.
    data["instance_clear_mode"] = world.options.instance_clear_mode.current_key


def _ap_item_display_eligible_location_names() -> frozenset[str]:
    """Finding I3 (M4.7 final review): the set of location NAMES belonging
    to a family whose C++ trigger-lookup map (QUEST_ID_TO_LOCATION_ID /
    VENDOR_SLOT_TO_LOCATION_ID, Task 1) can actually resolve a synthesized
    item back to a real quest_template/npc_vendor row. Originally
    _add_ap_item_display_data included EVERY location in the whole world
    unconditionally ("extra entries are harmless" -- see the superseded
    docstring this replaced), but that was wrong in practice: it made the
    C++ side issue a wasted item_template INSERT per non-family location
    (permanent orphan rows), made SynthesizeAndRewireLocations's "no
    matching trigger" branch LOG_ERROR once per such location (hundreds of
    misleading lines on every server boot), and bloated slot_data (sent to
    every connecting client) with entries no C++ code ever looks up. Reads
    locations.py's own _OPTIONAL_CATEGORIES registry -- the single source of
    truth for which family owns which location names -- rather than
    hardcoding a duplicate list here, so this stays correct automatically if
    a family's content table changes shape."""
    names: set[str] = set()
    for category in locations_module._OPTIONAL_CATEGORIES:
        if category.key in _AP_ITEM_DISPLAY_FAMILY_KEYS:
            names.update(category.locations_module.LOCATIONS.keys())
    return frozenset(names)


def _add_ap_item_display_data(world, data: dict) -> None:
    """M4.7: for every one of this world's OWN locations that belongs to
    the Quest Rewards or Vendor Inventories family (the only two families
    the C++ side's trigger-lookup maps can resolve -- see
    _ap_item_display_eligible_location_names) and has a real item placed
    (location.item is set once fill runs, which it always is by the time
    fill_slot_data() is called), record the real owning player's name, the
    real item's name, and its classification flags. This is the
    generation-time equivalent of "ship a patch file" for a game whose
    client stays completely stock (docs/guides/player-guide.md) -- the
    C++ module reads this back out of the Connected message's slot_data at
    connect time (Task 5) rather than rediscovering it over the network."""
    eligible_names = _ap_item_display_eligible_location_names()
    display: dict[int, dict] = {}
    for location in world.multiworld.get_locations(world.player):
        if location.address is None or location.item is None:
            continue
        if location.name not in eligible_names:
            continue
        item = location.item
        player_name = world.multiworld.get_player_name(item.player)
        display[location.address] = {
            "name": f"{player_name}'s {item.name}",
            "flags": int(item.classification),
        }
    data["ap_item_display"] = display


def _add_vendor_check_repeat_behavior(world, data: dict) -> None:
    data["vendor_check_repeat_behavior"] = world.options.vendor_check_repeat_behavior.current_key
