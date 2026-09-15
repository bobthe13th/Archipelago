"""M5.6.2 (moved from retired M5.1.4): shuffles creature_template.name/
subname and creature_template_model.CreatureDisplayID/DisplayScale, each
independently toggleable. See design spec Sec4 and this plan's Global
Constraints for the composite-PK restriction on the model/scale pool.

mutate() is option-agnostic by design: candidate_rows() (which DOES receive
`world`) resolves each field's active mode into control keys
(_name_mode/_model_mode/_scale_mode) on the row's payload -- but mutate()
currently branches purely on which real columns are present in a given
payload dict, it never actually reads those control keys' string values.
That's harmless today since every mode is binary (vanilla/shuffle --
absence of the column already means "don't touch this field", making the
control key redundant), but if a third mode is ever added to any of these
fields, mutate() will need to be updated to actually inspect the relevant
control key, or it will silently keep applying shuffle-only behavior
regardless of which mode string was requested. mutate() never reads
world.options directly either way, since MutationCategory.mutate's fixed
signature has no `world` parameter.

CRITICAL: when both model and scale are enabled, candidate_rows() emits
ONE row per creature_template_model candidate with BOTH fields in its
payload -- never two separate rows for the same (table, row_id). See this
plan's Global Constraints for why (APWorldState's INSERT IGNORE snapshot
step would silently lose whichever field's original value wasn't captured
by the first row processed)."""
from __future__ import annotations

import random
from typing import Sequence

from . import creature_appearance_content_data
from . import mutation_pipeline


def candidate_rows(world) -> list:
    name_mode = world.options.environment_randomizer_name_mode.current_key
    model_mode = world.options.environment_randomizer_model_mode.current_key
    scale_mode = world.options.environment_randomizer_scale_mode.current_key

    rows = []

    if name_mode != "vanilla":
        for entry, data in creature_appearance_content_data.CREATURE_NAMES.items():
            rows.append(("creature_template", entry, {
                "name": data["name"], "subname": data["subname"], "_name_mode": name_mode,
            }))

    if model_mode != "vanilla" or scale_mode != "vanilla":
        for creature_id, data in creature_appearance_content_data.CREATURE_MODELS.items():
            payload = {}
            if model_mode != "vanilla":
                payload["CreatureDisplayID"] = data["CreatureDisplayID"]
                payload["_model_mode"] = model_mode
            if scale_mode != "vanilla":
                payload["DisplayScale"] = data["DisplayScale"]
                payload["_scale_mode"] = scale_mode
            rows.append(("creature_template_model", creature_id, payload))

    return rows


def mutate(rows: Sequence, rng: random.Random) -> list:
    # Payload keys throughout this function are the REAL creature_template/
    # creature_template_model column names (name, subname, CreatureDisplayID,
    # DisplayScale) -- APWorldState::Apply writes every returned payload key
    # as a literal SQL column name via `UPDATE <table> SET <key> = <value>`.
    name_rows = [(table, key, payload) for table, key, payload in rows if table == "creature_template"]
    model_rows = [(table, key, payload) for table, key, payload in rows if table == "creature_template_model"]

    result = []

    if name_rows:
        shuffled = [(p["name"], p["subname"]) for _t, _k, p in name_rows]
        rng.shuffle(shuffled)
        for (table, key, payload), (new_name, new_subname) in zip(name_rows, shuffled):
            if new_name != payload["name"] or new_subname != payload["subname"]:
                result.append((table, key, {"name": new_name, "subname": new_subname}))

    if model_rows:
        display_ids = [p["CreatureDisplayID"] for _t, _k, p in model_rows if "CreatureDisplayID" in p]
        shuffled_display_ids = list(display_ids)
        rng.shuffle(shuffled_display_ids)
        display_idx = 0
        for table, key, payload in model_rows:
            new_payload = {}
            if "CreatureDisplayID" in payload:
                new_display_id = shuffled_display_ids[display_idx]
                display_idx += 1
                if new_display_id != payload["CreatureDisplayID"]:
                    new_payload["CreatureDisplayID"] = new_display_id
            if "DisplayScale" in payload:
                new_scale = round(rng.uniform(0.5, 2.0), 2)
                if new_scale != payload["DisplayScale"]:
                    new_payload["DisplayScale"] = new_scale
            if new_payload:
                result.append((table, key, new_payload))

    return result


mutation_pipeline.register_category(
    mutation_pipeline.MutationCategory(
        key="environment_model_scale_name", candidate_rows=candidate_rows, mutate=mutate, invariant_rules=[],
    )
)
