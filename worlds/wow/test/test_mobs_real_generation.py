import random
import unittest

from .. import mobs_level, mobs_spawns, mobs_snapshot_content_data
from .. import world_seed
from .bases import WoWTestBase


class TestMobsLevelRealGeneration(WoWTestBase):
    options = {"mob_randomizer_level_mode": "zone_scaled"}

    def test_produces_real_mutation_rows_when_enabled(self):
        self.assertTrue(
            mobs_snapshot_content_data.CREATURE_TEMPLATES,
            "mobs_snapshot_content_data.CREATURE_TEMPLATES is empty -- run "
            "`python tools/extract_mobs_snapshot.py` against a live, populated "
            "acore_world DB (see docs/testing/m5.1.0-manual-verification-checklist.md) "
            "before this test can prove real end-to-end mutation behavior.",
        )
        candidates = mobs_level.candidate_rows(self.world)
        self.assertTrue(candidates)
        seed = world_seed.derive_world_seed("12345", "Alice")
        rng = random.Random(world_seed.derive_sub_seed(seed, "mobs_level", 0))
        result = mobs_level.mutate(candidates, rng)
        # Not every row is guaranteed to change (a shift can legitimately
        # roll to 0), but SOME row changing across a real, large candidate
        # set is a near-certainty -- this is the real "did it work at all"
        # end-to-end signal.
        self.assertTrue(result)


class TestMobsSpawnsRealGeneration(WoWTestBase):
    options = {"mob_randomizer_spawn_mode": "shuffle_all"}

    def test_produces_real_mutation_rows_when_enabled(self):
        self.assertTrue(
            mobs_snapshot_content_data.CREATURE_SPAWNS,
            "mobs_snapshot_content_data.CREATURE_SPAWNS is empty -- run "
            "`python tools/extract_mobs_snapshot.py` against a live, populated "
            "acore_world DB before this test can prove real end-to-end mutation behavior.",
        )
        candidates = mobs_spawns.candidate_rows(self.world)
        self.assertTrue(candidates)
        seed = world_seed.derive_world_seed("12345", "Alice")
        rng = random.Random(world_seed.derive_sub_seed(seed, "mobs_spawns", 0))
        result = mobs_spawns.mutate(candidates, rng)
        self.assertTrue(result)
