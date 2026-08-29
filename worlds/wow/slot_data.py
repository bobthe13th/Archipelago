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

# Finding I3 (M4.7 final review) + M4.10.1 final regression pass (Task 8): the
# families whose locations the C++ side's trigger-lookup maps
# (QUEST_ID_TO_LOCATION_ID / VENDOR_SLOT_TO_LOCATION_ID, Task 1;
# BuildLocationIdToGameobjectLootSlot, M4.10.1 Task 5) can ever resolve -- see
# _ap_item_display_eligible_location_names below. SynthesizeAndRewireLocations
# (APItemDisplay.cpp) is driven ENTIRELY by iterating this slot_data map --
# BuildLocationIdToGameobjectLootSlot's own map is only ever consulted for a
# locationId that already showed up as a key here, never iterated
# independently. Omitting "containersanity" left the entire family a
# no-op at runtime: gameobject_loot_template.Item was never rewritten to a
# synthesized entry, archipelago_lootslot_original_items was never
# populated, and no synthesized item_template row ever existed -- looting a
# Containersanity chest silently granted the real vanilla item with no AP
# check ever firing, despite every individual piece (extraction, compiler,
# C++ synthesis branch, ArchipelagoLootSlotScript hook) being independently
# correct and unit-tested. Caught here because no test at any level actually
# drove SynthesizeAndRewireLocations's dispatch with a location present in
# BuildLocationIdToGameobjectLootSlot's map but absent from this frozenset:
# the Python unit tests mock a hand-picked eligible-names set that never
# included containersanity as a positive case, and the C++ tests
# (test_APItemDisplay.cpp) only exercise SynthesizedEntryFor's pure-function
# idempotency, never the full family-dispatch loop.
_AP_ITEM_DISPLAY_FAMILY_KEYS = frozenset({"quest_rewards", "vendor_stock", "containersanity"})


def build_slot_data(world) -> dict:
    data: dict = {}
    _add_instance_clear_mode(world, data)
    _add_ap_item_display_data(world, data)
    _add_vendor_check_repeat_behavior(world, data)
    _add_loot_slot_check_repeat_behavior(world, data)
    return data


def _add_instance_clear_mode(world, data: dict) -> None:
    # Task 23 (M2) added this write; M4.9 closes the other half of the gap --
    # ArchipelagoWorldScript.cpp now parses this key out of Connected's
    # slot_data (APProtocol::ParseInstanceClearModeFromSlotData, mirroring
    # vendor_check_repeat_behavior's exact M4.7 shape) instead of requiring
    # an operator to mirror it by hand via Archipelago.InstanceClearMode --
    # that manual conf key no longer exists (M4.9 removed it outright).
    data["instance_clear_mode"] = world.options.instance_clear_mode.current_key


def _ap_item_display_eligible_location_names() -> frozenset[str]:
    """Finding I3 (M4.7 final review) + M4.10.1 Task 8: the set of location
    NAMES belonging to a family whose C++ trigger-lookup map
    (QUEST_ID_TO_LOCATION_ID / VENDOR_SLOT_TO_LOCATION_ID, Task 1;
    BuildLocationIdToGameobjectLootSlot, M4.10.1) can actually resolve a
    synthesized item back to a real quest_template/npc_vendor/
    gameobject_loot_template row. Originally
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


def _add_loot_slot_check_repeat_behavior(world, data: dict) -> None:
    data["loot_slot_check_repeat_behavior"] = world.options.loot_slot_check_repeat_behavior.current_key
