import random
import unittest

from .. import environment_creature_flavor, creature_flavor_content_data
from .. import world_seed
from .bases import WoWTestBase


class TestEnvironmentCreatureFlavorRealGeneration(WoWTestBase):
    options = {
        "environment_randomizer_equipment_enabled": True,
        "environment_randomizer_posture_enabled": True,
        "environment_randomizer_mount_enabled": True,
    }

    @unittest.skipUnless(
        creature_flavor_content_data.CREATURE_EQUIPMENT,
        "creature_flavor_content_data.CREATURE_EQUIPMENT is empty -- run "
        "`python tools/extract_creature_flavor_snapshot.py` against a live, "
        "populated acore_world DB (see docs/testing/m5.6.3-manual-verification-checklist.md) "
        "before this test can prove real end-to-end mutation behavior.",
    )
    def test_produces_real_mutation_rows_when_enabled(self):
        candidates = environment_creature_flavor.candidate_rows(self.world)
        self.assertTrue(candidates)
        seed = world_seed.derive_world_seed("12345", "Alice")
        rng = random.Random(world_seed.derive_sub_seed(seed, "environment_creature_flavor", 0))
        result = environment_creature_flavor.mutate(candidates, rng)
        self.assertTrue(result)
