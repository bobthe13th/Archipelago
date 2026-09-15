"""M5.6.0: Weather mutation -- randomizes game_weather's 12 per-zone seasonal
precipitation-chance columns. See design spec Sec2. Cosmetic (design spec
Sec2/Sec6.7) -- invariant_rules=[], no reachability implication.

mutate() is option-agnostic by design: candidate_rows() (which DOES receive
`world`) resolves the active mode into a per-row `_mode` control key, and
mutate() just applies that mode -- it never reads world.options directly,
since MutationCategory.mutate's fixed signature (mutation_pipeline.py) has
no `world` parameter."""
from __future__ import annotations

import random
from typing import Sequence

from . import weather_snapshot_content_data
from . import mutation_pipeline

_CHANCE_COLUMNS = (
    "spring_rain_chance", "spring_snow_chance", "spring_storm_chance",
    "summer_rain_chance", "summer_snow_chance", "summer_storm_chance",
    "fall_rain_chance", "fall_snow_chance", "fall_storm_chance",
    "winter_rain_chance", "winter_snow_chance", "winter_storm_chance",
)


def candidate_rows(world) -> list:
    mode = world.options.environment_randomizer_weather_mode.current_key
    if mode == "vanilla":
        return []

    rows = []
    # Sorted explicitly: RNG-determinism reproducibility depends on a stable
    # iteration order, and the generated data module's dict insertion order
    # happens to be sorted but that shouldn't be an implicit load-bearing fact.
    for zone, data in sorted(weather_snapshot_content_data.WEATHER_ZONES.items()):
        payload = {column: data[column] for column in _CHANCE_COLUMNS}
        payload["_mode"] = mode
        rows.append(("game_weather", zone, payload))
    return rows


def mutate(rows: Sequence, rng: random.Random) -> list:
    result = []
    for table_name, zone, payload in rows:
        mode = payload["_mode"]
        if mode == "perma_clear":
            new_values = {column: 0 for column in _CHANCE_COLUMNS}
        elif mode == "perma_storm":
            # game_weather's 12 chance columns are CUMULATIVE thresholds in the
            # real server roll (Weather.cpp): chance1=rain, chance2=chance1+snow,
            # chance3=chance2+storm, rnd<=chance1 -> rain, rnd<=chance2 -> snow,
            # rnd<=chance3 -> storm, else fine. Setting every column to 100
            # would make chance1 (rain) alone always win the roll -- perma-rain,
            # not perma-storm. Zeroing rain/snow and maxing only storm makes
            # chance1=chance2=0, chance3=100, so every roll lands on storm.
            new_values = {
                column: (100 if column.endswith("_storm_chance") else 0)
                for column in _CHANCE_COLUMNS
            }
        else:  # random_per_zone
            new_values = {column: rng.randint(0, 100) for column in _CHANCE_COLUMNS}
        old_values = {column: payload[column] for column in _CHANCE_COLUMNS}
        if new_values != old_values:
            result.append((table_name, zone, new_values))
    return result


mutation_pipeline.register_category(
    mutation_pipeline.MutationCategory(
        key="environment_weather", candidate_rows=candidate_rows, mutate=mutate, invariant_rules=[],
    )
)
