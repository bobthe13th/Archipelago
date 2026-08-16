# Archipelago/worlds/wow/test/test_basic.py
from .bases import WoWTestBase


class TestDefault(WoWTestBase):
    options = {}


class TestNorthshireGeneration(WoWTestBase):
    def test_all_locations_reachable(self) -> None:
        """M2: all 19 curated locations must be reachable with no items required
        (matches rules.py's no-op access rules for this milestone)."""
        self.assertTrue(len(self.multiworld.get_reachable_locations()) >= 19)

    def test_item_pool_matches_location_count(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), 19)
