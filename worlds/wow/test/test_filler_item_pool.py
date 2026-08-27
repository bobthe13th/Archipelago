# Archipelago/worlds/wow/test/test_filler_item_pool.py
import unittest
from unittest.mock import MagicMock

from .. import filler_reward_items_content_data, filler_reward_effects_content_data
from ..items import create_filler_item_pool, _EFFECT_TO_CATEGORY, FILLER_PER_CATEGORY_CAP


class TestEffectToCategoryMapping(unittest.TestCase):
    def test_every_real_effect_maps_to_a_real_category(self) -> None:
        for effect in filler_reward_effects_content_data.EFFECT_BY_ITEM_NAME.values():
            self.assertIn(effect, _EFFECT_TO_CATEGORY)


class TestCreateFillerItemPool(unittest.TestCase):
    def _make_world(self, selected_categories: set) -> MagicMock:
        world = MagicMock()
        world.options.filler_category_pools.value = selected_categories
        world.player = 1
        world.random.sample = lambda population, k: list(population)[:k]
        world.random.shuffle = lambda x: None
        return world

    def test_returns_exactly_the_requested_count(self) -> None:
        world = self._make_world(set(filler_reward_effects_content_data.EFFECT_BY_ITEM_NAME.values())
                                  | {"badge_currency", "consumable"})
        pool = create_filler_item_pool(world, 10)
        self.assertEqual(len(pool), 10)

    def test_only_selected_categories_are_eligible(self) -> None:
        world = self._make_world({"badge_currency"})
        pool = create_filler_item_pool(world, 5)
        self.assertEqual(len(pool), 5)
        badge_names = {
            name for name, tags in filler_reward_items_content_data.TAGS.items()
            if tags["category"] == frozenset({"badge_currency"})
        }
        for item in pool:
            self.assertIn(item.name, badge_names)

    def test_items_are_classified_filler(self) -> None:
        from BaseClasses import ItemClassification
        world = self._make_world({"badge_currency"})
        pool = create_filler_item_pool(world, 3)
        for item in pool:
            self.assertEqual(item.classification, ItemClassification.filler)

    def test_zero_count_returns_empty_list(self) -> None:
        world = self._make_world({"badge_currency"})
        self.assertEqual(create_filler_item_pool(world, 0), [])


if __name__ == "__main__":
    unittest.main()
