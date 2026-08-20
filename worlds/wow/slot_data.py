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
    return data


def _add_instance_clear_mode(world, data: dict) -> None:
    # Task 23: mirrors the resolved InstanceClearMode choice so a connected
    # worldserver COULD read it from the AP session in the future -- as of
    # this task, the module still has no slot_data parsing at all (the same
    # known gap Finding #10 documents for every other option), so an
    # operator must still mirror this by hand via
    # Archipelago.InstanceClearMode until that gap is closed.
    data["instance_clear_mode"] = world.options.instance_clear_mode.current_key
