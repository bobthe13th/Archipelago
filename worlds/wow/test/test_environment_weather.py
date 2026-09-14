import json
import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import environment_weather
from .. import mutation_output
from .. import mutation_pipeline


def _fake_world(mode: str):
    return SimpleNamespace(
        options=SimpleNamespace(environment_randomizer_weather_mode=SimpleNamespace(current_key=mode))
    )


_FAKE_ZONES = {
    1: {
        "spring_rain_chance": 10, "spring_snow_chance": 0, "spring_storm_chance": 5,
        "summer_rain_chance": 20, "summer_snow_chance": 0, "summer_storm_chance": 10,
        "fall_rain_chance": 15, "fall_snow_chance": 0, "fall_storm_chance": 5,
        "winter_rain_chance": 30, "winter_snow_chance": 40, "winter_storm_chance": 25,
    },
    2: {
        "spring_rain_chance": 0, "spring_snow_chance": 0, "spring_storm_chance": 0,
        "summer_rain_chance": 0, "summer_snow_chance": 0, "summer_storm_chance": 0,
        "fall_rain_chance": 0, "fall_snow_chance": 0, "fall_storm_chance": 0,
        "winter_rain_chance": 0, "winter_snow_chance": 0, "winter_storm_chance": 0,
    },
}


class TestCandidateRows(unittest.TestCase):
    def test_vanilla_mode_returns_no_candidates(self):
        world = _fake_world("vanilla")
        with patch.object(environment_weather, "weather_snapshot_content_data", SimpleNamespace(WEATHER_ZONES=_FAKE_ZONES)):
            self.assertEqual(environment_weather.candidate_rows(world), [])

    def test_non_vanilla_mode_returns_one_row_per_zone(self):
        world = _fake_world("perma_clear")
        with patch.object(environment_weather, "weather_snapshot_content_data", SimpleNamespace(WEATHER_ZONES=_FAKE_ZONES)):
            rows = environment_weather.candidate_rows(world)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row[0] for row in rows}, {"game_weather"})
        self.assertEqual({row[1] for row in rows}, {1, 2})


class TestMutate(unittest.TestCase):
    def test_perma_clear_zeroes_every_column(self):
        rows = [("game_weather", 1, dict(_FAKE_ZONES[1], _mode="perma_clear"))]
        rng = random.Random("fixed-seed")
        result = environment_weather.mutate(rows, rng)
        self.assertEqual(len(result), 1)
        _table, _zone, payload = result[0]
        self.assertTrue(all(v == 0 for v in payload.values()))

    def test_perma_storm_zeroes_rain_and_snow_maxes_storm(self):
        # game_weather's chance columns are cumulative thresholds in the real
        # server roll (chance1=rain, chance2=chance1+snow, chance3=chance2+storm),
        # so perma_storm must zero rain/snow and max only storm -- maxing every
        # column would make every roll resolve to rain (see Weather.cpp).
        rows = [("game_weather", 1, dict(_FAKE_ZONES[1], _mode="perma_storm"))]
        rng = random.Random("fixed-seed")
        result = environment_weather.mutate(rows, rng)
        _table, _zone, payload = result[0]
        for column, value in payload.items():
            if column.endswith("_storm_chance"):
                self.assertEqual(value, 100, column)
            else:
                self.assertEqual(value, 0, column)

    def test_random_per_zone_stays_within_0_and_100(self):
        rows = [("game_weather", 1, dict(_FAKE_ZONES[1], _mode="random_per_zone"))]
        rng = random.Random("fixed-seed")
        for _ in range(20):
            result = environment_weather.mutate(rows, rng)
            if result:
                _table, _zone, payload = result[0]
                self.assertTrue(all(0 <= v <= 100 for v in payload.values()))

    def test_no_mode_key_leaks_into_returned_payload(self):
        rows = [("game_weather", 1, dict(_FAKE_ZONES[1], _mode="perma_clear"))]
        rng = random.Random("fixed-seed")
        result = environment_weather.mutate(rows, rng)
        _table, _zone, payload = result[0]
        self.assertNotIn("_mode", payload)

    def test_unchanged_zone_is_not_returned(self):
        # zone 2 is already all-zero -- perma_clear should be a no-op diff.
        rows = [("game_weather", 2, dict(_FAKE_ZONES[2], _mode="perma_clear"))]
        rng = random.Random("fixed-seed")
        result = environment_weather.mutate(rows, rng)
        self.assertEqual(result, [])

    def test_empty_rows_returns_empty(self):
        rng = random.Random("fixed-seed")
        self.assertEqual(environment_weather.mutate([], rng), [])

    def test_random_per_zone_mutate_is_deterministic_per_seed(self):
        # Plan's Testing section promise: "random_per_zone stays within
        # [0,100] and is deterministic per world_seed" -- range coverage
        # already existed (test_random_per_zone_stays_within_0_and_100)
        # but nothing proved determinism until now: two FRESH RNGs seeded
        # identically must produce identical mutation output.
        rows = [("game_weather", 1, dict(_FAKE_ZONES[1], _mode="random_per_zone"))]
        result_a = environment_weather.mutate(rows, random.Random("same-seed-value"))
        result_b = environment_weather.mutate(rows, random.Random("same-seed-value"))
        self.assertEqual(result_a, result_b)


class TestComposedPipeline(unittest.TestCase):
    """Plan's Testing section also promised 'excluded-row coverage against
    Pipeline A's claimed rows' -- prior tests only ever drove candidate_rows/
    mutate directly, bypassing mutation_pipeline.run_category's claimed-row
    filtering and mutation_output's JSON serialization entirely. These tests
    drive environment_weather through the real composed path, following the
    pattern established in test_mutation_pipeline.py."""

    def test_claimed_zone_excluded_and_survives_json_round_trip(self):
        world = _fake_world("perma_storm")
        # environment_weather.py registers this exact shape into
        # mutation_pipeline's module-level registry at import time (no
        # standalone module-level variable to reference), so an equivalent
        # inline MutationCategory built from its own candidate_rows/mutate
        # is the composed-path entry point available to a test.
        category = mutation_pipeline.MutationCategory(
            key="environment_weather",
            candidate_rows=environment_weather.candidate_rows,
            mutate=environment_weather.mutate,
            invariant_rules=[],
        )
        with patch.object(environment_weather, "weather_snapshot_content_data", SimpleNamespace(WEATHER_ZONES=_FAKE_ZONES)):
            result = mutation_pipeline.run_category(
                category, world, "some-seed", claimed={("game_weather", 1)}
            )

        result_zones = {row[1] for row in result}
        self.assertNotIn(1, result_zones)  # claimed -> excluded before mutate ever ran
        self.assertIn(2, result_zones)  # zone 2's all-zero baseline changes under perma_storm

        contents = mutation_output.build_mutation_file_contents("some-seed", {"environment_weather": result})
        round_tripped = json.loads(json.dumps(contents))
        zone_2_row = next(
            row for row in round_tripped["categories"]["environment_weather"]
            if row[0] == "game_weather" and row[1] == 2
        )
        self.assertIsInstance(zone_2_row[1], int)
        self.assertNotIn("_mode", zone_2_row[2])
