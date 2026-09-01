"""Real WoW zone id -> its vanilla leveling band (min_level, max_level).
Curated the same way MAP_ID_TO_EXPANSION (M4.8) is: real, cited, verified
against this checkout's AreaTable.dbc, not derived from a live query every
generation. Consumed by Zone Leveler's whole_game_scaled content scope (M4.11.1
Task 12) and Key Hunt's zone-restriction option (Task 5) -- NOT wired into the
generic tag_options/OptionSet system (that's M4.11.2's full-breadth follow-up).
"""
from __future__ import annotations

ZONE_ID_BARRENS = 17
ZONE_ID_MOLTEN_CORE = 409  # Blackrock Depths/Mountain's own instance zone id -- verify exact value

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
