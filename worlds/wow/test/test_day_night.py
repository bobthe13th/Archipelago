import unittest
from types import SimpleNamespace

from .. import day_night


def _fake_world(mode: str, speed_percent: int = 100):
    return SimpleNamespace(
        options=SimpleNamespace(
            environment_randomizer_day_night_mode=SimpleNamespace(current_key=mode),
            environment_randomizer_day_night_speed_percent=SimpleNamespace(value=speed_percent),
        )
    )


class TestResolveDayNight(unittest.TestCase):
    def test_vanilla_mode(self):
        world = _fake_world("vanilla")
        self.assertEqual(day_night.resolve_day_night(world), {"mode": "vanilla", "speed_percent": 100.0})

    def test_speed_multiplier_mode_carries_the_configured_percent(self):
        world = _fake_world("speed_multiplier", speed_percent=250)
        result = day_night.resolve_day_night(world)
        self.assertEqual(result["mode"], "speed_multiplier")
        self.assertEqual(result["speed_percent"], 250.0)

    def test_perma_day_mode_ignores_speed_percent(self):
        world = _fake_world("perma_day", speed_percent=250)
        result = day_night.resolve_day_night(world)
        self.assertEqual(result["mode"], "perma_day")

    def test_perma_night_mode(self):
        world = _fake_world("perma_night")
        self.assertEqual(day_night.resolve_day_night(world)["mode"], "perma_night")
