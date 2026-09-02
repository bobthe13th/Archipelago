"""Real WoW zone id -> its vanilla leveling band (min_level, max_level).
Curated the same way MAP_ID_TO_EXPANSION (M4.8) is. Both zone-id constants
below were independently verified (M4.11.1 Task 13) against this checkout's
real `AreaTable.dbc` (var/extractors/dbc/AreaTable.dbc, read via
modules/archipelago_wow/tools/dbc_reader.py's generic WDBC reader): each
record's name field is field index 11 of the file's 36-field layout,
located by cross-checking two independently known-correct area ids (14 ->
"Durotar", 1637 -> "Orgrimmar"). ZONE_ID_BARRENS's recalled value (17)
decoded to "The Barrens" and needed no change. ZONE_ID_MOLTEN_CORE's
recalled value (409) was WRONG -- 409 turned out to be an unrelated
AreaTable area id (its own name field decodes to "Island of Doctor
Lapidis", nothing to do with Molten Core), confirmed via direct DBC decode.
The real Molten Core area id, found by searching the DBC's string block for
the exact string "Molten Core", is 2717, and the constant below was
corrected to match.

Final whole-branch review correction (M4.11.1, 2026-09-01): despite this
module's original docstring claiming otherwise, neither Zone Leveler's
whole_game_scaled content scope (Task 12) nor Key Hunt's zone-restriction
option (Task 5) actually consumes ZONE_ID_TO_LEVEL_RANGE/
level_range_for_zone/zones_in_level_range in real production code.
zone_leveler_content_data.py imports this module only for the bare
ZONE_ID_BARRENS constant (used as a zone_id tag, not a level range);
Task 12's own min_level/max_level filtering reads
zone_leveler_content_data.ZONES["barrens"].min_level/.max_level directly,
a separate, hand-curated source of truth. Key Hunt's key_hunt_zone_pools
(Task 5) restricts by rares_content_data's own per-row `zone` tags
(resolved via a WorldMapArea.dbc position resolver), never by this module.
As of this review, ZONE_ID_TO_LEVEL_RANGE/level_range_for_zone/
zones_in_level_range are exercised only by this module's own test file
(test/test_zone_level_data.py) -- real, verified scaffolding for a future
milestone (a possible M4.11.2 generalization), but not currently wired
into any consuming code path. Left in place rather than deleted for that
reason; do not assume it is load-bearing anywhere today.
"""
from __future__ import annotations

ZONE_ID_BARRENS = 17  # verified vs. this checkout's real AreaTable.dbc (M4.11.1 Task 13): "The Barrens"
ZONE_ID_MOLTEN_CORE = 2717  # corrected from a wrong 409 vs. real AreaTable.dbc (M4.11.1 Task 13): "Molten Core"

ZONE_ID_TO_LEVEL_RANGE: dict[int, tuple[int, int]] = {
    ZONE_ID_BARRENS: (10, 30),
    ZONE_ID_MOLTEN_CORE: (60, 63),
}


def level_range_for_zone(zone_id: int) -> tuple[int, int] | None:
    return ZONE_ID_TO_LEVEL_RANGE.get(zone_id)


def zones_in_level_range(min_level: int, max_level: int) -> set[int]:
    """Zones whose own band overlaps [min_level, max_level] at all (not
    fully-contained-within) -- a zone spanning 1-20 is included in a 10-30
    query, matching how a possession-triggered item's own req level, not a
    zone's full span, is what Task 12's filter actually keys on."""
    return {
        zone_id for zone_id, (zone_min, zone_max) in ZONE_ID_TO_LEVEL_RANGE.items()
        if zone_min <= max_level and zone_max >= min_level
    }


# M4.11.3.1: hand-curated raw-zone-id -> canonical area-tag-name lookup, the
# same kind of hand-curated constant ZONE_ID_BARRENS/ZONE_ID_MOLTEN_CORE
# already are (not a live DBC read -- the apworld has no DBC access at
# generation time, all DBC parsing is compile-time-only tooling work under
# modules/archipelago_wow, per this project's established architecture).
# Only the 3 real zone ids _zone_leveler_trainer_spell_zone_matches
# (locations.py) ever compares against (zone_data.zone_id/
# allowed_hub_zone_ids for the one currently-curated Zone Leveler zone,
# Barrens) need an entry here, not a full project-wide table.
ZONE_ID_TO_AREA_NAME: dict[int, str] = {
    ZONE_ID_BARRENS: "barrens",
    14: "durotar",     # Durotar -- verified against real AreaTable.dbc (M4.11.3.1 Task 2)
    1637: "orgrimmar",  # Orgrimmar -- verified against real AreaTable.dbc (M4.11.1 Task 13)
}


def area_name_for_zone_id(zone_id: int) -> str | None:
    return ZONE_ID_TO_AREA_NAME.get(zone_id)
