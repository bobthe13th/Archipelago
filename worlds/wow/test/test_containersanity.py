# Archipelago/worlds/wow/test/test_containersanity.py
import unittest

from .bases import WoWTestBase
from .. import containersanity_content_data


class TestContainersanityRowAlignment(unittest.TestCase):
    def test_locations_and_items_are_row_order_aligned(self) -> None:
        location_names = list(containersanity_content_data.LOCATIONS)
        item_names = list(containersanity_content_data.ITEMS)
        self.assertEqual(len(location_names), len(item_names))
        for location_name, item_name in zip(location_names, item_names):
            self.assertTrue(location_name.startswith("Container: "))
            self.assertTrue(item_name.startswith("Container Item: "))


class TestContainersanityRealGenerationWotlkOnly(WoWTestBase):
    """Final whole-branch review fix (I4): no existing test exercised a real
    seed generation with the Containersanity family actually live -- every
    other coverage either unit-tests the extraction/compiler tooling in
    isolation or uses fake location/item modules (see test_slot_data.py).
    Mirrors TestRecipesAndTrainerSpellsFullGeneration's real-generation
    pattern (test_recipes_trainer_spells.py), narrowed to the `wotlk` tag
    alone (a small real subset -- ~hundreds of rows, not the full ~16.8k-row
    family) to keep this fast, same spirit as
    TestRecipeProfessionPoolNarrowingReducesSampledSet narrowing recipes to
    just `cooking`. Containersanity has no weight_option to zero out
    (locations.py's OptionalCategory.weight_option is None, same as
    recipes/trainer_spells -- every tag-matched row is included
    unconditionally), so narrowing the tag pool is the only way to keep this
    class's own real-generation run bounded.
    """
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": set(), "trainer_spell_class_pools": set(),
        "containersanity_expansion_pools": {"wotlk"},
    }

    def test_containersanity_locations_exist(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        containersanity_locations = [n for n in names if n in containersanity_content_data.LOCATIONS]
        self.assertTrue(len(containersanity_locations) > 0)

    def test_every_wotlk_tagged_row_is_present_no_sampling(self) -> None:
        # Direct proof of the no-check_density/weight-sampling contract:
        # with the wotlk tag selected, ALL real wotlk-tagged containersanity
        # rows must be present, not just a density-sampled subset.
        wotlk_rows = [
            name for name, tags in containersanity_content_data.TAGS.items()
            if "wotlk" in tags["expansion"]
        ]
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_containersanity = [n for n in names if n in containersanity_content_data.LOCATIONS]
        self.assertEqual(sorted(sampled_containersanity), sorted(wotlk_rows))

    def test_only_wotlk_tagged_rows_are_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_containersanity = {n for n in names if n in containersanity_content_data.LOCATIONS}
        self.assertTrue(len(sampled_containersanity) > 0)
        self.assertLess(len(sampled_containersanity), len(containersanity_content_data.LOCATIONS))
        for name in sampled_containersanity:
            self.assertIn("wotlk", containersanity_content_data.TAGS[name]["expansion"])

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


if __name__ == "__main__":
    unittest.main()
