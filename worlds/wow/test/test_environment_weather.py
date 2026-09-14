import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import environment_weather


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
