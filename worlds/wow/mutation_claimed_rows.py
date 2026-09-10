"""M5.0 Sec4: AP-claimed-row exclusion. Computes, for a generated WoWWorld
(post-fill -- called from mutation_pipeline.py's driver at the pre_output
lifecycle stage, per Sec4's own execution-order ruling), the set of real DB
rows Pipeline A's SynthesizeAndRewireLocations (APItemDisplay.cpp) will
rewrite for this seed. A Pipeline B category's mutate() candidate pool must
never include one of these -- see mutation_pipeline.py's driver."""
from __future__ import annotations

from . import locations as locations_module
from .slot_data import _AP_ITEM_DISPLAY_TRIGGER_KINDS

# row_key's shape varies by table: an int for a single-PK table
# (quest_template.entry), a tuple for a composite-keyed one (npc_vendor,
# skinning_loot_template, disenchant_loot_template). Mirrors exactly the
# fields Pipeline A's own TRIGGERS dict uses for each kind, since that is
# the only shape guaranteed to line up without a live DB connection --
# M5.3+'s own candidate_rows() must key its npc_vendor/loot candidates
# identically for set-difference exclusion to actually match.
ClaimedRow = tuple


def _claimed_row_for_trigger(trigger: dict) -> ClaimedRow | None:
    kind = trigger.get("kind")
    if kind == "quest_reward":
        return ("quest_template", trigger["quest_id"])
    if kind == "vendor_purchase":
        return ("npc_vendor", (trigger["npc_entry"], trigger.get("item_slot")))
    if kind == "skinning_loot":
        return ("skinning_loot_template", (trigger["loot_id"], trigger["item_entry"]))
    if kind == "disenchant_loot":
        return ("disenchant_loot_template", (trigger["loot_id"], trigger["item_entry"]))
    return None


def _trigger_for_location_name(name: str) -> dict | None:
    for category in locations_module._OPTIONAL_CATEGORIES:
        triggers = getattr(category.locations_module, "TRIGGERS", None)
        if triggers and name in triggers:
            return triggers[name]
    return None


def claimed_rows(world) -> set[ClaimedRow]:
    """world: a generated WoWWorld instance, post-fill. Only locations
    actually instantiated for THIS seed (world.multiworld.get_locations(
    world.player)) are consulted, never every row in a family's full
    static TRIGGERS table -- matching Sec4's "varies by the connected
    slot's options/game-mode" ruling."""
    claimed: set[ClaimedRow] = set()
    for location in world.multiworld.get_locations(world.player):
        trigger = _trigger_for_location_name(location.name)
        if trigger is None or trigger.get("kind") not in _AP_ITEM_DISPLAY_TRIGGER_KINDS:
            continue
        row = _claimed_row_for_trigger(trigger)
        if row is not None:
            claimed.add(row)
    return claimed
