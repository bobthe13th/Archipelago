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
from . import zone_leveler_content_data

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
#
# M4.10.2 final whole-branch review (C1) -- SECOND OCCURRENCE of the exact
# same bug, in the exact same frozenset: "gathersanity" was likewise omitted,
# making all 2,302 Gathersanity locations a complete runtime no-op
# (skinning_loot_template/disenchant_loot_template/gameobject_loot_template
# .Item never rewritten, archipelago_lootslot_original_items never populated,
# no check ever firing) despite all 7 implementation tasks being individually
# reviewed and passed. The root cause of the recurrence is that this frozenset
# is the ONLY place a new loot-slot family has to be registered, and nothing
# in the test suite failed when it wasn't. Safeguards added by that fix, so a
# third occurrence is caught mechanically:
#   * test_slot_data.py::TestAddApItemDisplayData::test_includes_gathersanity_locations
#     -- a direct positive case per family key, mirroring
#     test_includes_containersanity_locations.
#   * test_gathersanity.py::TestGathersanityRealGenerationDisenchantOnly::
#     test_gathersanity_locations_appear_in_ap_item_display -- a REAL seed
#     generation (no fakes) that asserts a real Gathersanity location id
#     reaches build_slot_data's emitted ap_item_display map. This is the
#     level at which both occurrences would have been caught: the fake-module
#     unit tests can only ever prove the keys they were told about.
# ANY new family whose locations the C++ trigger-lookup maps can resolve MUST
# be given both of those tests.
#
# M4.11.4.2 final review fix wave 2 (Fix 3): eligibility is now keyed by each
# location's OWN trigger KIND, not by its family. The family-keyed frozenset
# this replaced was correct only while "family" and "resolvable by
# SynthesizeAndRewireLocations" meant the same thing -- M4.11.4's abstracted
# zone pool broke that equivalence:
#   * containersanity is now 100% zone_pool_credit (1,435 rows, M4.11.4.1) --
#     it has NO resolvable locations left at all.
#   * gathersanity is now MIXED: its gathering_node sub-family is
#     zone_pool_credit (M4.11.4.2), while its skinning_loot (1,895) and
#     disenchant_loot (123) rows still are, and still need, real synthesis.
# A zone_pool_credit location is an ABSTRACT pool slot -- there is no backing
# quest_template/npc_vendor/loot_template row anywhere for it, by construction
# -- so SynthesizeAndRewireLocations can never resolve one. Under the old
# family filter it nonetheless synthesized a permanent orphan item_template row
# AND logged one "...no matching quest_reward, vendor_purchase, gameobject_loot,
# skinning_loot, or disenchant_loot trigger -- skipped, no row to rewrite"
# LOG_ERROR per such location, on every server boot: 22,519 of them at this
# checkout's real scale (1,435 + 21,084) -- the exact log-spam/orphan-row
# failure mode Finding I3 originally introduced this filter to prevent,
# reintroduced through a different door.
#
# These are the real trigger kinds SynthesizeAndRewireLocations
# (APItemDisplay.cpp) actually dispatches on, in its own order. Note
# "gameobject_loot" is NOT among them: its last real consumer was retired in
# M4.11.4.2 (Task 5) along with BuildLocationIdToGameobjectLootSlot itself, so
# no generated content emits that kind at all any more.
_AP_ITEM_DISPLAY_TRIGGER_KINDS = frozenset(
    {"quest_reward", "vendor_purchase", "skinning_loot", "disenchant_loot"}
)


def build_slot_data(world) -> dict:
    data: dict = {}
    _add_instance_clear_mode(world, data)
    _add_ap_item_display_data(world, data)
    _add_vendor_check_repeat_behavior(world, data)
    _add_loot_slot_check_repeat_behavior(world, data)
    _add_holidaysanity_stacking(world, data)
    _add_zone_leveler_data(world, data)
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
    """Finding I3 (M4.7 final review) + M4.10.1 Task 8 + M4.11.4.2 final
    review fix wave 2: the set of location NAMES whose OWN trigger kind the
    C++ side's SynthesizeAndRewireLocations can actually resolve back to a
    real quest_template/npc_vendor/skinning_loot_template/
    disenchant_loot_template row. Originally _add_ap_item_display_data
    included EVERY location in the whole world unconditionally ("extra
    entries are harmless" -- see the superseded docstring this replaced), but
    that was wrong in practice: it made the C++ side issue a wasted
    item_template INSERT per non-resolvable location (permanent orphan rows),
    made SynthesizeAndRewireLocations's "no matching trigger" branch LOG_ERROR
    once per such location (thousands of misleading lines on every server
    boot), and bloated slot_data (sent to every connecting client) with
    entries no C++ code ever looks up.

    Reads each family's own generated TRIGGERS table -- the single source of
    truth for what kind of real backing row (if any) a location has -- via
    locations.py's _OPTIONAL_CATEGORIES registry, rather than hardcoding
    either a family list or a name list here. That keeps this correct
    automatically when a family's trigger kinds change shape, which is
    exactly what M4.11.4 did to both Containersanity and Gathersanity.

    A content module with no TRIGGERS table at all (families whose locations
    are fired by a hook rather than by rewriting a real DB row -- e.g.
    achievements, rares) contributes nothing here, same as before."""
    names: set[str] = set()
    for category in locations_module._OPTIONAL_CATEGORIES:
        triggers = getattr(category.locations_module, "TRIGGERS", None)
        if not triggers:
            continue
        for name, trigger in triggers.items():
            if trigger.get("kind") in _AP_ITEM_DISPLAY_TRIGGER_KINDS:
                names.add(name)
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


def _add_holidaysanity_stacking(world, data: dict) -> None:
    data["holidaysanity_stacking"] = bool(world.options.holidaysanity_stacking)


def _add_zone_leveler_data(world, data: dict) -> None:
    """M4.11.1 Task 15: ArchipelagoGoals.cpp's IsZoneLevelerComplete has no
    rules-evaluation engine of its own and cannot derive "which goals are
    selected, and how much of each is required" from anything else the AP
    server sends -- these keys are its only source of truth.
    zone_leveler_zone_key additionally lets that C++ side resolve its own
    Archipelago::CoreLoop::LEVEL_CAP_TOTAL_BY_TRACK lookup
    ("zone_leveler_<zone_key>") without hardcoding "barrens" literally,
    which would silently stop matching the moment a second zone is curated
    (M4.11.2). No-op (keys simply absent) for every other game_mode,
    matching every other game-mode-gated slot_data helper's own guard
    convention (see e.g. _add_instance_clear_mode's sibling helpers).

    M4.11.3.3 Task 3: drops zone_leveler_zone_id/
    zone_leveler_allowed_hub_zone_ids/zone_leveler_allow_hub_zone -- Task 1
    already removed the zone_id/allowed_hub_zone_ids fields these read from
    ZoneLevelerZoneData, and Task 3 removes the zone_leveler_allow_hub_zone
    option itself, so this helper would already be broken (AttributeError)
    without this change. Confirmed via direct source inspection of both the
    C++ side (ArchipelagoRealmState.h/ArchipelagoWorldScript.cpp/
    ArchipelagoZoneLevelerScript.cpp) that the ONLY consumer of these three
    keys was ArchipelagoZoneLevelerScript.cpp's OnPlayerUpdateZone hub-zone
    /zone-lock enforcement -- exactly the widening mechanism this milestone
    removes -- not any other feature (display, logging, ...); that C++-side
    removal/rework is M4.11.3.3 Task 4's own job, not this file's."""
    if world.options.game_mode != "zone_leveler":
        return
    zone_key = world.options.zone_leveler_starting_zone.current_key
    zone_data = zone_leveler_content_data.ZONES[zone_key]
    data["zone_leveler_zone_key"] = zone_key
    data["zone_leveler_goals"] = sorted(world.options.zone_leveler_goals.value)
    data["zone_leveler_statues_required"] = world.options.zone_leveler_statues_required.value
    data["zone_leveler_instances_required"] = world.options.zone_leveler_instances_required.value
    # Final whole-branch review fix (Minor #6, M4.11.3 milestone final
    # review): emit the curated subset (zone_leveler_content_data.
    # curated_instance_keys), not the raw, wider zone_data.instance_keys --
    # matching every other real consumer of this distinction (goals.py's
    # instance_clears goal, items.py's _trap_baseline_location_count,
    # locations.py's create_core_loop_locations, all switched onto
    # curated_instance_keys by Task 2). The C++ side that reads this field
    # only ever counts instances with a real "Instance Unlock: <name>" item
    # (which don't exist for the non-curated, merely-reachable instances),
    # so this narrows a list the C++ side already effectively treats as its
    # own ceiling -- no interface change on either side of the wire.
    data["zone_leveler_instance_keys"] = list(zone_leveler_content_data.curated_instance_keys(zone_data))
