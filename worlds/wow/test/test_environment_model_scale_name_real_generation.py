import random

from .. import environment_model_scale_name, creature_appearance_content_data
from .. import world_seed
from .bases import WoWTestBase


class TestEnvironmentModelScaleNameRealGeneration(WoWTestBase):
    options = {
        "environment_randomizer_name_mode": "shuffle",
        "environment_randomizer_model_mode": "shuffle",
        "environment_randomizer_scale_mode": "shuffle",
    }

    def test_produces_real_mutation_rows_when_enabled(self):
        self.assertTrue(
            creature_appearance_content_data.CREATURE_NAMES,
            "creature_appearance_content_data.CREATURE_NAMES is empty -- run "
            "`python tools/extract_creature_appearance_snapshot.py` against a live, "
            "populated acore_world DB (see docs/testing/m5.6.2-manual-verification-checklist.md) "
            "before this test can prove real end-to-end mutation behavior.",
        )
        candidates = environment_model_scale_name.candidate_rows(self.world)
        self.assertTrue(candidates)
        seed = world_seed.derive_world_seed("12345", "Alice")
        rng = random.Random(world_seed.derive_sub_seed(seed, "environment_model_scale_name", 0))
        result = environment_model_scale_name.mutate(candidates, rng)
        self.assertTrue(result)
