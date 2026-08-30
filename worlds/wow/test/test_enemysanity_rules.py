# Archipelago/worlds/wow/test/test_enemysanity_rules.py
import unittest

from .bases import WoWTestBase


class TestEnemysanityZoneAccessGate(WoWTestBase):
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "enemysanity_type_pools": {"regular", "boss"},
        "enemysanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
    }

    def test_vanilla_only_species_location_needs_no_gate(self) -> None:
        from .. import enemysanity_content_data, world_state
        tags = world_state.species_expansion_tags(self.world)
        vanilla_only_names = [
            name for name, trig in enemysanity_content_data.TRIGGERS.items()
            if tags.get(trig["creature_entry"]) == frozenset({"vanilla"})
        ]
        self.assertTrue(len(vanilla_only_names) > 0)
        self.assertTrue(self.can_reach_location(vanilla_only_names[0]))

    def test_wotlk_only_species_location_requires_northrend_passage(self) -> None:
        from .. import enemysanity_content_data, world_state
        tags = world_state.species_expansion_tags(self.world)
        wotlk_only_names = [
            name for name, trig in enemysanity_content_data.TRIGGERS.items()
            if tags.get(trig["creature_entry"]) == frozenset({"wotlk"})
        ]
        self.assertTrue(len(wotlk_only_names) > 0)
        self.assertFalse(self.can_reach_location(wotlk_only_names[0]))
        self.collect_by_name("Northrend Passage")
        self.assertTrue(self.can_reach_location(wotlk_only_names[0]))


if __name__ == "__main__":
    unittest.main()
