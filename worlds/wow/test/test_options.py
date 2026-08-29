# Archipelago/worlds/wow/test/test_options.py
import unittest


class TestContainersanityExpansionPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import ContainersanityExpansionPools
        self.assertEqual(ContainersanityExpansionPools.default, ContainersanityExpansionPools.valid_keys)

    def test_valid_keys_match_the_project_s_three_expansion_tiers(self) -> None:
        from ..options import ContainersanityExpansionPools
        self.assertEqual(set(ContainersanityExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})


class TestLootSlotCheckRepeatBehavior(unittest.TestCase):
    def test_default_is_suppress_entirely(self) -> None:
        from ..options import LootSlotCheckRepeatBehavior
        self.assertEqual(LootSlotCheckRepeatBehavior.default, LootSlotCheckRepeatBehavior.option_suppress_entirely)

    def test_all_four_modes_present(self) -> None:
        from ..options import LootSlotCheckRepeatBehavior
        for mode in ("suppress_entirely", "vanilla_item", "gold_conversion", "filler_consumable"):
            self.assertTrue(hasattr(LootSlotCheckRepeatBehavior, f"option_{mode}"))


if __name__ == "__main__":
    unittest.main()
