"""Hand-curated per-zone registry for the zone_leveler game mode (M4.11.1).
Only "barrens" (BarrensBeater) is curated this milestone -- adding a zone here
is pure curation against this shape, no new engineering (see the design spec's
§2/M4.11.2 note)."""
from __future__ import annotations

from dataclasses import dataclass

from . import quest_rewards_content_data, zone_level_data


@dataclass(frozen=True)
class ZoneLevelerZoneData:
    zone_id: int
    display_name: str
    min_level: int
    max_level: int
    hub_spawn_map: int
    hub_spawn_position: tuple[float, float, float, float]  # x, y, z, orientation
    allowed_hub_zone_ids: frozenset[int]
    instance_keys: tuple[str, ...]
    treasure_item_name: str
    quest_reward_location_names: tuple[str, ...]


def _quest_names_for_zone(zone_id: int) -> tuple[str, ...]:
    return tuple(
        name for name, trigger in quest_rewards_content_data.TRIGGERS.items()
        if trigger.get("zone_id") == zone_id
    )


# Crossroads inn coordinates and Durotar/Orgrimmar zone ids: verified
# (M4.11.1 Task 13) against this checkout's real live `acore_world` DB and
# `AreaTable.dbc`. ZONE_ID_DUROTAR (14) and ZONE_ID_ORGRIMMAR (1637) were
# confirmed by directly decoding this checkout's real AreaTable.dbc string
# data (14 -> "Durotar", 1637 -> "Orgrimmar") -- no change from their
# recalled values. hub_spawn_position below was confirmed/updated in the
# same task; see the SQL migration's own header comment
# (data/sql/updates/pending_db_world/2026_09_01_00_zone_leveler_barrens_playercreateinfo.sql
# in the azerothcore-wotlk repo) for the full citation.
ZONE_ID_DUROTAR = 14
ZONE_ID_ORGRIMMAR = 1637

ZONES: dict[str, ZoneLevelerZoneData] = {
    "barrens": ZoneLevelerZoneData(
        zone_id=zone_level_data.ZONE_ID_BARRENS,
        display_name="BarrensBeater",
        min_level=10,
        max_level=30,
        hub_spawn_map=1,  # Kalimdor
        hub_spawn_position=(-410.0, -2643.0, 96.3063, 3.4383),  # Crossroads inn, verified live (Task 13)
        allowed_hub_zone_ids=frozenset({ZONE_ID_DUROTAR, ZONE_ID_ORGRIMMAR}),
        instance_keys=("wailing_caverns", "razorfen_kraul", "razorfen_downs"),
        treasure_item_name="Golden Boar Statue",
        quest_reward_location_names=_quest_names_for_zone(zone_level_data.ZONE_ID_BARRENS),
    ),
}
