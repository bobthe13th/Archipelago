"""M5.0 Sec6: writes the companion <slot_name>_mutations.json file into
generate_output's own output_directory -- the same mechanism every other
AP world already uses for its own per-slot output artifact, so AP WebHost
and any automated hosting script that already consumes the seed's output
archive picks this file up for free."""
from __future__ import annotations

import json
import os


def build_mutation_file_contents(world_seed: str, pipeline_result: dict[str, list]) -> dict:
    return {
        "world_seed": world_seed,
        "categories": {key: [list(row) for row in rows] for key, rows in pipeline_result.items()},
    }


def write_mutation_file(world, output_directory: str, world_seed: str, pipeline_result: dict[str, list]) -> None:
    contents = build_mutation_file_contents(world_seed, pipeline_result)
    path = os.path.join(output_directory, f"{world.player_name}_mutations.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2, sort_keys=True)
