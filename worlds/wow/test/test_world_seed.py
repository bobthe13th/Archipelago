import unittest

from ..world_seed import derive_world_seed, derive_sub_seed


class TestDeriveWorldSeed(unittest.TestCase):
    def test_deterministic_for_same_inputs(self):
        self.assertEqual(
            derive_world_seed("12345", "Alice"),
            derive_world_seed("12345", "Alice"),
        )

    def test_differs_by_slot_name_within_same_multiworld(self):
        self.assertNotEqual(
            derive_world_seed("12345", "Alice"),
            derive_world_seed("12345", "Bob"),
        )

    def test_differs_by_multiworld_seed(self):
        self.assertNotEqual(
            derive_world_seed("12345", "Alice"),
            derive_world_seed("67890", "Alice"),
        )

    def test_returns_hex_sha256(self):
        result = derive_world_seed("12345", "Alice")
        self.assertEqual(len(result), 64)
        int(result, 16)  # raises ValueError if not valid hex


class TestDeriveSubSeed(unittest.TestCase):
    def test_deterministic_for_same_inputs(self):
        world_seed = derive_world_seed("12345", "Alice")
        self.assertEqual(
            derive_sub_seed(world_seed, "mobs", 0),
            derive_sub_seed(world_seed, "mobs", 0),
        )

    def test_differs_by_attempt(self):
        world_seed = derive_world_seed("12345", "Alice")
        self.assertNotEqual(
            derive_sub_seed(world_seed, "mobs", 0),
            derive_sub_seed(world_seed, "mobs", 1),
        )

    def test_differs_by_category_key(self):
        world_seed = derive_world_seed("12345", "Alice")
        self.assertNotEqual(
            derive_sub_seed(world_seed, "mobs", 0),
            derive_sub_seed(world_seed, "faction", 0),
        )
