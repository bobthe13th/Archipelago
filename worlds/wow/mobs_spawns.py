"""M5.1.0: Spawns mutation -- randomizes which creature_template occupies a
given spawn point (creature.id). See design spec Sec3.

Level band is a 5-level floor-division bucket (minlevel // 5), a
DELIBERATE approximation of "±5 levels": a true "within 5 of any other"
relation isn't transitive (10 and 14 are within 5, 14 and 18 are within 5,
but 10 and 18 are not) and so can't be a valid partition key -- only a
similarity GRAPH, which CountingInvariantRule's group_key mechanism has no
way to express. A fixed-width bucket is the closest simple approximation
that stays a real partition; width 5 keeps the maximum spread within one
bucket to 4 levels, safely under the stated ±5.

M5.1.1 (design spec docs/superpowers/specs/2026-09-11-archipelago-wow-m5.1.1-mob-randomizer-exclusions-design.md):
`shuffle_excluded` on every CREATURE_TEMPLATES/CREATURE_SPAWNS row (computed
once at extraction time from real DB queries -- extract_mobs_snapshot.py's
own docstring has the full category list) is checked TWO-SIDED here: a
spawn whose own guid or current template is excluded never gets a
candidate row at all (never touched, source or destination -- see
candidate_rows), and an excluded entry is never added to any replacement
pool (never chosen as a new value -- see mutate). This replaces the
crash-3-hotfix's narrower `_UNSPAWNABLE_CREATURE_TYPES` local constant,
whose type values are now folded into extraction's own SQL-level
exclusion (type 8/Critter included this time, which that hotfix missed)."""
from __future__ import annotations

import random
from typing import Sequence

from . import mobs_snapshot_content_data
from . import mutation_pipeline
from .mutation_invariants import InvariantRule, InvariantViolation

_LEVEL_BAND_WIDTH = 5


def _classification_for_rank(rank: int) -> str:
    if rank == 0:
        return "normal"
    if rank in (1, 2):
        return "elite"
    return "boss"  # 3 (WorldBoss), 4 (Rare)


def _level_band(minlevel: int) -> int:
    return minlevel // _LEVEL_BAND_WIDTH


def candidate_rows(world) -> list:
    mode = world.options.mob_randomizer_spawn_mode.current_key
    if mode == "vanilla":
        return []

    templates = mobs_snapshot_content_data.CREATURE_TEMPLATES
    rows = []
    for guid, spawn in mobs_snapshot_content_data.CREATURE_SPAWNS.items():
        if spawn.get("shuffle_excluded"):
            continue
        template = templates.get(spawn["template_entry"])
        if template is None or template.get("shuffle_excluded"):
            continue
        rows.append((
            "creature", guid,
            {"id": spawn["template_entry"], "_shuffle_mode": mode, "_home_map": spawn["map"]},
        ))
    return rows


def mutate(rows: Sequence, rng: random.Random) -> list:
    if not rows:
        return []
    mode = rows[0][2]["_shuffle_mode"]
    templates = mobs_snapshot_content_data.CREATURE_TEMPLATES

    if mode == "shuffle_groups":
        pools: dict[tuple[int, str], list[int]] = {}
        for entry, data in templates.items():
            if data.get("shuffle_excluded"):
                continue
            group = (_level_band(data["minlevel"]), _classification_for_rank(data["rank"]))
            pools.setdefault(group, []).append(entry)

        result = []
        for table_name, guid, payload in rows:
            original_entry = payload["id"]
            original_data = templates.get(original_entry)
            if original_data is None:
                continue
            group = (_level_band(original_data["minlevel"]), _classification_for_rank(original_data["rank"]))
            pool = pools.get(group, [])
            if not pool:
                continue
            new_entry = rng.choice(pool)
            if new_entry != original_entry:
                result.append((table_name, guid, {"id": new_entry}))
        return result

    if mode == "shuffle_all":
        clean_templates = [
            entry for entry, data in templates.items()
            if not data["ai_name"] and not data["script_name"]
            and not data.get("shuffle_excluded")
        ]
        scripted_by_map: dict[int, list[int]] = {}
        for entry, data in templates.items():
            if data.get("shuffle_excluded"):
                continue
            if data["ai_name"] or data["script_name"]:
                for map_id in data["home_maps"]:
                    scripted_by_map.setdefault(map_id, []).append(entry)

        result = []
        for table_name, guid, payload in rows:
            home_map = payload["_home_map"]
            pool = clean_templates + scripted_by_map.get(home_map, [])
            if not pool:
                continue
            new_entry = rng.choice(pool)
            if new_entry != payload["id"]:
                result.append((table_name, guid, {"id": new_entry}))
        return result

    return []


def _group_key_for_spawn_row(row) -> tuple[int, int, str] | None:
    _table_name, guid, payload = row
    spawn = mobs_snapshot_content_data.CREATURE_SPAWNS.get(guid)
    if spawn is None:
        return None
    template_data = mobs_snapshot_content_data.CREATURE_TEMPLATES.get(payload["id"])
    if template_data is None:
        return None
    return (spawn["map"], _level_band(template_data["minlevel"]), _classification_for_rank(template_data["rank"]))


class SpawnGroupInvariantRule(InvariantRule):
    """A map that had >=1 creature in a given (level_band, classification)
    group before shuffle_groups mode still has >=1 after -- prevents a
    zone's own low-level roster shuffling away entirely to other maps
    sharing the same band, which would depopulate its early questing.
    Deliberately a no-op for shuffle_all (free redistribution is that
    mode's own point -- this claim isn't meant to hold there) and for
    vanilla/empty input, detected via candidate_rows' own `_shuffle_mode`
    control key rather than a separate mode parameter (InvariantRule.check
    has no world/options access, matching mutate()'s own constraint)."""
    name = "spawn_level_band_classification_per_map"

    def check(self, candidate_rows: Sequence, mutation_rows: Sequence) -> None:
        if not candidate_rows:
            return
        mode = candidate_rows[0][2].get("_shuffle_mode")
        if mode != "shuffle_groups":
            return
        before = {key for row in candidate_rows if (key := _group_key_for_spawn_row(row)) is not None}
        after = {key for row in mutation_rows if (key := _group_key_for_spawn_row(row)) is not None}
        lost = before - after
        if lost:
            raise InvariantViolation(
                f"{self.name}: {len(lost)} (map, level_band, classification) group(s) present "
                f"before shuffle_groups have zero matching spawns after: {sorted(map(str, lost))[:5]}"
            )


mutation_pipeline.register_category(
    mutation_pipeline.MutationCategory(
        key="mobs_spawns", candidate_rows=candidate_rows, mutate=mutate,
        invariant_rules=[SpawnGroupInvariantRule()],
    )
)
