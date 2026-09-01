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
corrected to match. Consumed by Zone Leveler's whole_game_scaled content scope
(M4.11.1 Task 12) and Key Hunt's zone-restriction option (Task 5) -- NOT
wired into the generic tag_options/OptionSet system (that's M4.11.2's
full-breadth follow-up).
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
