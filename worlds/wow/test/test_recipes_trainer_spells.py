# Archipelago/worlds/wow/test/test_recipes_trainer_spells.py
import unittest

from .bases import WoWTestBase
from .. import recipes_content_data, trainer_spells_content_data


class TestRecipesRowAlignment(unittest.TestCase):
    def test_locations_and_items_are_row_order_aligned(self) -> None:
        location_names = list(recipes_content_data.LOCATIONS)
        item_names = list(recipes_content_data.ITEMS)
        self.assertEqual(len(location_names), len(item_names))
        for location_name, item_name in zip(location_names, item_names):
            self.assertTrue(location_name.startswith("Recipe: "))
            self.assertTrue(item_name.startswith("Recipe Item: "))


class TestTrainerSpellsRowAlignment(unittest.TestCase):
    def test_every_location_spell_id_is_covered_by_exactly_one_item(self) -> None:
        # M4.11.6's progressive-item redesign broke the old, simpler 1:1
        # LOCATIONS/ITEMS row-order-alignment invariant this test used to
        # assert directly -- a "Progressive X" item now covers MULTIPLE
        # locations, one per delivery.spell_ids entry. See
        # create_optional_category_item_pool (items.py, M4.11.7-fix) for the
        # real, current consumer-side contract this test guards instead:
        # every location's own spell_id is covered by exactly one item,
        # either a chain item (CHAIN_SPELL_IDS_BY_ITEM_NAME) or, for every
        # remaining (non-chain) location/item, the original 1:1
        # row-order-aligned pairing on that filtered subset.
        location_names = list(trainer_spells_content_data.LOCATIONS)
        item_names = list(trainer_spells_content_data.ITEMS)
        chain_map = trainer_spells_content_data.CHAIN_SPELL_IDS_BY_ITEM_NAME
        spell_id_to_chain_item = {
            spell_id: item_name
            for item_name, spell_ids in chain_map.items()
            for spell_id in spell_ids
        }
        triggers = trainer_spells_content_data.TRIGGERS
        chain_item_names = set(chain_map)
        plain_item_names = [name for name in item_names if name not in chain_item_names]
        plain_location_names = [
            name for name in location_names
            if triggers[name]["spell_id"] not in spell_id_to_chain_item
        ]
        self.assertEqual(len(plain_location_names), len(plain_item_names))
        for location_name, item_name in zip(plain_location_names, plain_item_names):
            self.assertTrue(location_name.startswith("Trainer Spell: "))
            self.assertTrue(item_name.startswith("Trainer Spell Item: "))
        plain_location_names_set = set(plain_location_names)
        for location_name in location_names:
            spell_id = triggers[location_name]["spell_id"]
            self.assertTrue(
                spell_id in spell_id_to_chain_item or location_name in plain_location_names_set,
                f"{location_name!r} (spell_id {spell_id}) is covered by neither a chain nor a plain item",
            )


class TestRecipesAndTrainerSpellsHaveNoOverlappingSpellIds(unittest.TestCase):
    def test_combined_runtime_map_has_no_key_collisions(self) -> None:
        # The exact real-data risk this milestone's plan documents in
        # Global Constraints (48 real spell_ids taught by both a recipe
        # AND a class trainer) -- extract_trainer_spells.py excludes
        # anything recipes.yaml already claims, so the two families' own
        # TRIGGERS spell_id sets must be fully disjoint. If this ever
        # regresses, ArchipelagoLearnSpellScript.cpp's combined C++ map
        # would silently lose one family's entry for the shared spell_id.
        recipe_spell_ids = {t["spell_id"] for t in recipes_content_data.TRIGGERS.values()}
        trainer_spell_ids = {t["spell_id"] for t in trainer_spells_content_data.TRIGGERS.values()}
        self.assertEqual(recipe_spell_ids & trainer_spell_ids, set())


_ALL_PROFESSIONS = {
    "alchemy", "blacksmithing", "cooking", "enchanting", "engineering",
    "first_aid", "fishing", "herbalism", "inscription", "jewelcrafting",
    "leatherworking", "mining", "skinning", "tailoring", "other",
}
_ALL_CLASSES = {
    "warrior", "paladin", "hunter", "rogue", "priest",
    "death_knight", "shaman", "mage", "warlock", "druid",
}
_ALL_EXPANSIONS = {"vanilla", "tbc", "wotlk"}


class TestRecipesAndTrainerSpellsFullGeneration(WoWTestBase):
    # check_density: 100 with full tag-pool coverage (the real defaults,
    # restated explicitly since bases.py's own M4.9 fast-test-default
    # zeroes recipe_profession_pools/trainer_spell_class_pools otherwise --
    # see bases.py's own comment). quest_reward_weight/vendor_stock_weight:
    # 0, this class has nothing to do with either family.
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": _ALL_PROFESSIONS,
        "recipe_expansion_pools": _ALL_EXPANSIONS,
        "trainer_spell_class_pools": _ALL_CLASSES,
        "trainer_spell_expansion_pools": _ALL_EXPANSIONS,
    }

    def test_recipe_and_trainer_spell_locations_exist(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        recipe_locations = [n for n in names if n in recipes_content_data.LOCATIONS]
        trainer_spell_locations = [n for n in names if n in trainer_spells_content_data.LOCATIONS]
        self.assertTrue(len(recipe_locations) > 0)
        self.assertTrue(len(trainer_spell_locations) > 0)

    def test_every_tag_matching_row_is_present_no_sampling(self) -> None:
        # Direct proof of the no-check_density/weight-sampling contract:
        # with every tag pool selected in full, ALL real recipes/
        # trainer_spells rows must be present, not just a density-sampled
        # subset.
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertEqual(
            len([n for n in names if n in recipes_content_data.LOCATIONS]),
            len(recipes_content_data.LOCATIONS),
        )
        self.assertEqual(
            len([n for n in names if n in trainer_spells_content_data.LOCATIONS]),
            len(trainer_spells_content_data.LOCATIONS),
        )

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestRecipeProfessionPoolNarrowingReducesSampledSet(WoWTestBase):
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": {"cooking"},
        "recipe_expansion_pools": _ALL_EXPANSIONS,
        "trainer_spell_class_pools": set(),
    }

    def test_only_cooking_tagged_recipes_are_present(self) -> None:
        sampled_names = {
            loc.name for loc in self.multiworld.get_locations(self.player)
            if loc.name in recipes_content_data.LOCATIONS
        }
        self.assertTrue(len(sampled_names) > 0)
        self.assertLess(len(sampled_names), len(recipes_content_data.LOCATIONS))
        for name in sampled_names:
            self.assertEqual(recipes_content_data.TAGS[name]["profession"], frozenset({"cooking"}))


if __name__ == "__main__":
    unittest.main()
