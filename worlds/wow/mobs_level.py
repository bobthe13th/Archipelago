"""M5.1.0: Level mutation -- randomizes creature_template.minlevel/maxlevel.
See design spec Sec3. mutate() is option-agnostic by design: candidate_rows()
(which DOES receive `world`) resolves the active mode into a per-row
`_shift_group` control key (shared across every template in the same group
for zone_scaled, unique per template for individual_spawn), and mutate()
just rolls one shift per distinct group key it sees -- it never reads
world.options directly, since MutationCategory.mutate's fixed signature
(mutation_pipeline.py) has no `world` parameter."""
from __future__ import annotations

import random
from typing import Sequence

from . import mobs_snapshot_content_data
from . import mutation_pipeline

_MIN_SHIFT = -10
_MAX_SHIFT = 10
_MIN_LEVEL = 1
_MAX_LEVEL = 80


def candidate_rows(world) -> list:
    mode = world.options.mob_randomizer_level_mode.current_key
    if mode == "vanilla":
        return []

    rows = []
    for entry, data in mobs_snapshot_content_data.CREATURE_TEMPLATES.items():
        if mode == "zone_scaled":
            zone_tags = data["zone_tags"]
            shift_group = min(zone_tags) if zone_tags else f"__unzoned_{entry}"
        else:  # individual_spawn
            shift_group = f"__entry_{entry}"
        rows.append((
            "creature_template", entry,
            {"minlevel": data["minlevel"], "maxlevel": data["maxlevel"], "_shift_group": shift_group},
        ))
    return rows


def mutate(rows: Sequence, rng: random.Random) -> list:
    shifts: dict[str, int] = {}
    result = []
    for table_name, entry, payload in rows:
        shift_group = payload["_shift_group"]
        if shift_group not in shifts:
            shifts[shift_group] = rng.randint(_MIN_SHIFT, _MAX_SHIFT)
        shift = shifts[shift_group]
        new_min = max(_MIN_LEVEL, min(_MAX_LEVEL, payload["minlevel"] + shift))
        new_max = max(new_min, min(_MAX_LEVEL, payload["maxlevel"] + shift))
        if new_min != payload["minlevel"] or new_max != payload["maxlevel"]:
            result.append((table_name, entry, {"minlevel": new_min, "maxlevel": new_max}))
    return result


mutation_pipeline.register_category(
    mutation_pipeline.MutationCategory(
        key="mobs_level", candidate_rows=candidate_rows, mutate=mutate, invariant_rules=[],
    )
)
