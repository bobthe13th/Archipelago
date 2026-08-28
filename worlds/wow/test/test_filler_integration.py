# Archipelago/worlds/wow/test/test_filler_integration.py
import unittest

from Options import OptionError

from .bases import WoWTestBase
from .. import filler_reward_items_content_data, filler_reward_effects_content_data


class TestFillerRowAlignment(unittest.TestCase):
    def test_every_filler_item_has_exactly_one_category(self) -> None:
        for name, tags in filler_reward_items_content_data.TAGS.items():
            self.assertEqual(len(tags["category"]), 1)

    def test_filler_reward_effects_cover_all_five_effects(self) -> None:
        effects = set(filler_reward_effects_content_data.EFFECT_BY_ITEM_NAME.values())
        self.assertEqual(effects, {"cast_spell", "grant_money", "grant_xp_percent", "grant_title", "portable_service"})


class TestCoreLoopParityWithFillerActive(WoWTestBase):
    # Full defaults: check_density=100, every filler category selected --
    # the exact real-generation proof that create_core_loop_item_pool's new
    # deficit-closing call actually holds item=location parity.
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": set(), "trainer_spell_class_pools": set(),
        "filler_category_pools": {
            "random_buff", "gold_reward", "xp_reward", "title", "portable_service",
            "badge_currency", "consumable", "bag", "gear_enhancement",
            "equipment", "openable", "toy", "seasonal", "mount", "pet", "tabard", "reagent",
        },
    }

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))

    def test_at_least_one_filler_item_was_actually_pooled(self) -> None:
        filler_names = set(filler_reward_items_content_data.ITEMS) | set(filler_reward_effects_content_data.ITEMS)
        pooled_names = {i.name for i in self.multiworld.itempool}
        self.assertTrue(pooled_names & filler_names)


class TestCoreLoopParityDeathKnightTrack(WoWTestBase):
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": set(), "trainer_spell_class_pools": set(),
        "death_knight_slot": True,
        "filler_category_pools": {
            "random_buff", "gold_reward", "xp_reward", "title", "portable_service",
            "badge_currency", "consumable", "bag", "gear_enhancement",
            "equipment", "openable", "toy", "seasonal", "mount", "pet", "tabard", "reagent",
        },
    }

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestFillerCategoryPoolNarrowingReducesSampledSet(WoWTestBase):
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": set(), "trainer_spell_class_pools": set(),
        "filler_category_pools": {"badge_currency"},
    }

    def test_only_badge_currency_filler_items_are_pooled(self) -> None:
        badge_names = {
            name for name, tags in filler_reward_items_content_data.TAGS.items()
            if tags["category"] == frozenset({"badge_currency"})
        }
        pooled_filler_names = {
            i.name for i in self.multiworld.itempool
            if i.name in filler_reward_items_content_data.ITEMS or i.name in filler_reward_effects_content_data.ITEMS
        }
        self.assertTrue(pooled_filler_names)
        self.assertTrue(pooled_filler_names.issubset(badge_names))


class TestEmptyFillerCategoryPoolsFailsValidation(WoWTestBase):
    """core_loop's every-level item pool has a real, unconditional
    dependency on Filler to close its own item/location deficit (up to 64
    items on the standard track, 10 on death_knight) in every game_mode,
    not just Sprint -- unchecking every FillerCategoryPools box leaves zero
    eligible items to draw from, which must fail generation loudly here
    (goals._validate_filler_category_pools_nonempty) with a clear message,
    the same way TestKeyHuntZeroDensityFailsValidation (test_goals.py)
    proves the analogous Key Hunt density check fires before generation
    reaches Fill and raises a confusing raw FillError instead."""
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "sprint", "filler_category_pools": set()}

    def test_empty_filler_category_pools_fails_generation(self) -> None:
        with self.assertRaises(OptionError) as ctx:
            self.world_setup()
        message = str(ctx.exception).lower()
        self.assertIn("filler", message)
        self.assertIn("categor", message)


if __name__ == "__main__":
    unittest.main()
