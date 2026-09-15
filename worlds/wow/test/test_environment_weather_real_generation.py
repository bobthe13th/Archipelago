import random
import unittest

from .. import environment_weather, weather_snapshot_content_data
from .. import world_seed
from .bases import WoWTestBase


class TestEnvironmentWeatherRealGeneration(WoWTestBase):
    options = {"environment_randomizer_weather_mode": "random_per_zone"}

    @unittest.skipUnless(
        weather_snapshot_content_data.WEATHER_ZONES,
        "weather_snapshot_content_data.WEATHER_ZONES is empty -- run "
        "`python tools/extract_weather_snapshot.py` against a live, populated "
        "acore_world DB (see docs/testing/m5.6.0-manual-verification-checklist.md) "
        "before this test can prove real end-to-end mutation behavior.",
    )
    def test_produces_real_mutation_rows_when_enabled(self):
        candidates = environment_weather.candidate_rows(self.world)
        self.assertTrue(candidates)
        seed = world_seed.derive_world_seed("12345", "Alice")
        rng = random.Random(world_seed.derive_sub_seed(seed, "environment_weather", 0))
        result = environment_weather.mutate(candidates, rng)
        # Not every zone is guaranteed to change (a reroll can legitimately
        # match the original), but SOME zone changing across a real, large
        # candidate set is a near-certainty -- this is the real "did it work
        # at all" end-to-end signal.
        self.assertTrue(result)
