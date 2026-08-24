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


def build_slot_data(world) -> dict:
    data: dict = {}
    _add_instance_clear_mode(world, data)
    _add_ap_item_display_data(world, data)
    return data


def _add_instance_clear_mode(world, data: dict) -> None:
    # Task 23: mirrors the resolved InstanceClearMode choice so a connected
    # worldserver COULD read it from the AP session in the future -- as of
    # this task, the module still has no slot_data parsing at all (the same
    # known gap Finding #10 documents for every other option), so an
    # operator must still mirror this by hand via
    # Archipelago.InstanceClearMode until that gap is closed.
    data["instance_clear_mode"] = world.options.instance_clear_mode.current_key


def _add_ap_item_display_data(world, data: dict) -> None:
    """M4.7: for every one of this world's OWN locations that has a real
    item placed (location.item is set once fill runs, which it always is by
    the time fill_slot_data() is called), record the real owning player's
    name, the real item's name, and its classification flags. This is the
    generation-time equivalent of "ship a patch file" for a game whose
    client stays completely stock (docs/guides/player-guide.md) -- the
    C++ module reads this back out of the Connected message's slot_data at
    connect time (Task 5) rather than rediscovering it over the network.
    Every location in this world is included, not just Quest Rewards/Vendor
    Inventories -- the C++ side only ever looks up ids it already knows are
    AP-tagged (its own trigger registry, Task 1), so extra entries here are
    harmless and this stays correct automatically as new families
    (M4.10's sanity categories) start tagging their own locations too."""
    display: dict[int, dict] = {}
    for location in world.multiworld.get_locations(world.player):
        if location.address is None or location.item is None:
            continue
        item = location.item
        player_name = world.multiworld.get_player_name(item.player)
        display[location.address] = {
            "name": f"{player_name}'s {item.name}",
            "flags": int(item.classification),
        }
    data["ap_item_display"] = display
