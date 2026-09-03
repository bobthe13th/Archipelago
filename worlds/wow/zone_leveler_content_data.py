"""Hand-curated per-zone registry for the zone_leveler game mode (M4.11.1,
revised M4.11.3.3). Only "barrens" (BarrensBeater) is curated this
milestone -- adding a zone here is pure curation against this shape, no new
engineering."""
from __future__ import annotations

from dataclasses import dataclass

from . import instance_entrance_data, quest_rewards_content_data


@dataclass(frozen=True)
class ZoneLevelerZoneData:
    area_tags: frozenset[str]
    display_name: str
    min_level: int
    max_level: int
    hub_spawn_map: int
    hub_spawn_position: tuple[float, float, float, float]  # x, y, z, orientation
    instance_keys: tuple[str, ...]
    treasure_item_name: str
    quest_reward_location_names: tuple[str, ...]


def _instance_keys_reachable_from(area_tags: frozenset[str]) -> tuple[str, ...]:
    """M4.11.3.3: replaces a hand-curated instance list with a real,
    computed one -- an instance counts if ANY of its real entrances
    (M4.11.3.2's instance_entrance_data, itself computed from the real
    areatrigger/areatrigger_teleport world-DB tables) resolves into this
    zone's own area_tags. Stays correct if an instance's entrance is ever
    relocated (a future door-shuffle feature would only need to change
    areatrigger_teleport's own real data -- nothing here)."""
    return tuple(sorted(
        name for name, entrance_tags in instance_entrance_data.INSTANCE_ENTRANCE_AREA_TAGS.items()
        if entrance_tags & area_tags
    ))


def _quest_names_for_zone(area_tags: frozenset[str]) -> tuple[str, ...]:
    """M4.11.3.3: reads quest_rewards_content_data.TAGS (M4.11.3.1's own
    migrated shape) instead of the old scalar TRIGGERS[...]['zone_id']."""
    return tuple(
        name for name, tags in quest_rewards_content_data.TAGS.items()
        if tags.get("area", frozenset()) & area_tags
    )


ZONES: dict[str, ZoneLevelerZoneData] = {
    "barrens": ZoneLevelerZoneData(
        area_tags=frozenset({"barrens"}),
        display_name="BarrensBeater",
        min_level=10,
        max_level=30,
        hub_spawn_map=1,  # Kalimdor
        hub_spawn_position=(-410.0, -2643.0, 96.3063, 3.4383),  # Crossroads inn, unchanged
        instance_keys=_instance_keys_reachable_from(frozenset({"barrens"})),
        treasure_item_name="Golden Boar Statue",
        quest_reward_location_names=_quest_names_for_zone(frozenset({"barrens"})),
    ),
}


def resolve_core_loop_track(world) -> tuple[str, str | None]:
    """Resolve which core_loop_content_data track key
    (LEVEL_LOCATIONS_BY_TRACK / LEVEL_CAP_TOTAL_BY_TRACK /
    STARTING_LEVEL_CAP_BY_TRACK) this world's own options resolve to, plus
    the zone_leveler_starting_zone key (or None on the standard/death_knight
    branch). Final whole-branch review Finding 10 (2026-09-01): items.py,
    locations.py, and rules.py each independently duplicated this exact
    branch -- factored out here so the three call sites can never drift
    apart on what "the connected slot's track" means. getattr (not direct
    attribute access) on game_mode since items.py's
    _trap_baseline_location_count is also called directly by
    test_basic.py's TestFillerPoolCoversWorstCaseGatesTrapsAndHolidaysanity
    with a bare `types.SimpleNamespace(options=...)` fake world that has no
    game_mode attribute at all -- that fake world must keep resolving to the
    standard/death_knight branch exactly as before."""
    if getattr(world.options, "game_mode", None) == "zone_leveler":
        zone_key = world.options.zone_leveler_starting_zone.current_key
        return f"zone_leveler_{zone_key}", zone_key
    is_dk_slot = bool(world.options.death_knight_slot)
    return ("death_knight" if is_dk_slot else "standard"), None
