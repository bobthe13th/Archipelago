"""M5.6.4: shuffles gameobject_template.displayId/size among a
hand-verified safe subset -- see design spec Sec6 and this plan's Global
Constraints for the exact safety filter (applied entirely in the
extraction SQL, Task 1 -- this module trusts its content-data snapshot as
already-safe and does no further filtering here).

mutate() is option-agnostic by design: candidate_rows() (which DOES
receive `world`) resolves each field's active mode into control keys on
the row's payload, and mutate() just applies them.

CRITICAL: when both display and scale are enabled, candidate_rows() emits
ONE row per gameobject with BOTH fields in its payload -- never two
separate rows for the same (table, row_id). See this plan's Global
Constraints (and M5.6.2/M5.6.3's identical reasoning) for why."""
from __future__ import annotations

import random
from typing import Sequence

from . import gameobject_visuals_content_data
from . import mutation_pipeline


def candidate_rows(world) -> list:
    display_mode = world.options.environment_randomizer_gameobject_display_mode.current_key
    scale_mode = world.options.environment_randomizer_gameobject_scale_mode.current_key

    if display_mode == "vanilla" and scale_mode == "vanilla":
        return []

    rows = []
    for entry, data in gameobject_visuals_content_data.GAMEOBJECTS.items():
        payload = {}
        if display_mode != "vanilla":
            payload["displayId"] = data["displayId"]
            payload["_display_mode"] = display_mode
        if scale_mode != "vanilla":
            payload["size"] = data["size"]
            payload["_scale_mode"] = scale_mode
        rows.append(("gameobject_template", entry, payload))
    return rows


def mutate(rows: Sequence, rng: random.Random) -> list:
    display_ids = [p["displayId"] for _t, _k, p in rows if "displayId" in p]
    shuffled_display_ids = list(display_ids)
    rng.shuffle(shuffled_display_ids)

    result = []
    display_idx = 0
    for table, entry, payload in rows:
        new_payload = {}
        if "displayId" in payload:
            new_display_id = shuffled_display_ids[display_idx]
            display_idx += 1
            if new_display_id != payload["displayId"]:
                new_payload["displayId"] = new_display_id
        if "size" in payload:
            new_size = round(rng.uniform(0.5, 2.0), 2)
            if new_size != payload["size"]:
                new_payload["size"] = new_size
        if new_payload:
            result.append((table, entry, new_payload))
    return result


mutation_pipeline.register_category(
    mutation_pipeline.MutationCategory(
        key="environment_gameobject_visuals", candidate_rows=candidate_rows, mutate=mutate, invariant_rules=[],
    )
)
