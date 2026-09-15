import random
import unittest

from .. import environment_gameobject_visuals, gameobject_visuals_content_data
from .. import world_seed
from .bases import WoWTestBase


class TestEnvironmentGameObjectVisualsRealGeneration(WoWTestBase):
    options = {
        "environment_randomizer_gameobject_display_mode": "shuffle",
        "environment_randomizer_gameobject_scale_mode": "shuffle",
    }

    def test_produces_real_mutation_rows_when_enabled(self):
        self.assertTrue(
            gameobject_visuals_content_data.GAMEOBJECTS,
            "gameobject_visuals_content_data.GAMEOBJECTS is empty -- run "
            "`python tools/extract_gameobject_visuals_snapshot.py` against a live, "
            "populated acore_world DB (see docs/testing/m5.6.4-manual-verification-checklist.md) "
            "before this test can prove real end-to-end mutation behavior.",
        )
        candidates = environment_gameobject_visuals.candidate_rows(self.world)
        self.assertTrue(candidates)
        seed = world_seed.derive_world_seed("12345", "Alice")
        rng = random.Random(world_seed.derive_sub_seed(seed, "environment_gameobject_visuals", 0))
        result = environment_gameobject_visuals.mutate(candidates, rng)
        self.assertTrue(result)
