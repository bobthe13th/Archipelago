# Archipelago/worlds/wow/test/test_filler_options.py
import dataclasses
import unittest

from ..options import FillerCategoryPools, WoWOptions


class TestFillerCategoryPools(unittest.TestCase):
    def test_default_selects_every_value(self) -> None:
        self.assertEqual(set(FillerCategoryPools.default), set(FillerCategoryPools.valid_keys))

    def test_covers_all_eighteen_categories(self) -> None:
        self.assertEqual(
            set(FillerCategoryPools.valid_keys),
            {
                "random_buff", "gold_reward", "xp_reward", "title", "portable_service",
                "badge_currency", "consumable", "recipe", "bag", "gear_enhancement",
                "equipment", "openable", "toy", "seasonal", "mount", "pet", "tabard", "reagent",
            },
        )

    def test_wowoptions_declares_the_field(self) -> None:
        field_names = {f.name for f in dataclasses.fields(WoWOptions)}
        self.assertIn("filler_category_pools", field_names)


if __name__ == "__main__":
    unittest.main()
