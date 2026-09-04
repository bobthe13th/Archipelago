# Archipelago/worlds/wow/test/test_containersanity.py
import unittest
from unittest import mock

from .bases import WoWTestBase
from .. import containersanity_content_data


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


class TestContainersanityItemsModuleDropped(unittest.TestCase):
    """M4.11.4.1 Task 5: Containersanity no longer pairs each of its
    locations with a synthesized/aligned item row -- it shares Enemysanity/
    Repsanity's items_module=None shape (locations.py's
    create_optional_category_item_pool falls back to create_filler_item_pool
    for the deficit instead, see that function's own docstring)."""

    def test_containersanity_items_module_is_none(self) -> None:
        from ..locations import _OPTIONAL_CATEGORIES
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "containersanity")
        self.assertIsNone(category.items_module)


class TestContainersanityZoneCapPredicate(WoWTestBase):
    """M4.11.4.1 Task 5: the new containersanity_chests_per_zone cap is
    enforced by _containersanity_zone_cap_matches, which reads a real
    ordinal (1-based position within a zone's own capped sequence) off
    containersanity_content_data.TRIGGERS[name]["ordinal"]. Task 6 (a later
    task in this same plan) is what rewrites extract_containersanity.py and
    regenerates containersanity_content_data.py with that real "ordinal"/
    "zone_key" shape -- at the time this task runs, the checked-in content
    data module is still the OLD, pre-M4.11.4 per-real-chest-item format
    (TRIGGERS rows carry 'kind': 'gameobject_loot'/'loot_id'/'item_entry',
    no 'ordinal' key at all -- confirmed by direct inspection). Per the
    coordinator's ruling, this predicate's own logic only cares about the
    TRIGGERS dict SHAPE, not real DB content, so this test monkeypatches
    containersanity_content_data.LOCATIONS/TAGS/TRIGGERS/ALWAYS_PRESENT with
    a small fixture in the NEW (post-Task-6) shape, instead of depending on
    the real, not-yet-regenerated module. Task 8 (later, after Task 6 lands)
    is the real end-to-end check against real regenerated data.

    containersanity_expansion_pools/containersanity_chests_per_zone are
    deliberately NOT set via this class's own `options` dict: WoWTestBase's
    world_setup (bases.py) runs a full, real create_regions() during setUp,
    BEFORE this test method's own mock.patch.object block ever takes
    effect -- widening containersanity_expansion_pools at the class-option
    level would make that real setUp pass real, still-old-format
    containersanity rows through the new predicate and KeyError on the real
    (not yet regenerated) TRIGGERS dict. Leaving containersanity_expansion_
    pools at bases.py's fast-test default (empty set) means zero real
    containersanity rows are ever candidates during setUp, so the new
    predicate is never invoked against real data at all; both options are
    instead set directly on world.options inside the test body, after
    setUp has already completed, mirroring TestTwoStageComposition's own
    "set world.options.*.value inside the test, not via the class options
    dict" pattern in test_optional_categories.py."""

    def test_containersanity_candidates_respect_chests_per_zone_cap(self) -> None:
        from ..locations import create_optional_category_locations

        fake_locations = {f"Container: Fake Barrens Chest {i}": 8990000 + i for i in range(1, 4)}
        fake_tags = {name: {"expansion": frozenset({"wotlk"})} for name in fake_locations}
        fake_triggers = {
            name: {"kind": "zone_pool_credit", "zone_key": "barrens", "ordinal": i}
            for i, name in enumerate(fake_locations, start=1)
        }

        world = self.world
        world.options.containersanity_expansion_pools.value = {"wotlk"}
        world.options.containersanity_chests_per_zone.value = 2
        region = self.multiworld.get_region("Northshire", world.player)
        with mock.patch.object(containersanity_content_data, "LOCATIONS", fake_locations), \
             mock.patch.object(containersanity_content_data, "TAGS", fake_tags), \
             mock.patch.object(containersanity_content_data, "TRIGGERS", fake_triggers), \
             mock.patch.object(containersanity_content_data, "ALWAYS_PRESENT", frozenset()):
            created = create_optional_category_locations(world, region)

        created_fake_names = {loc.name for loc in created if loc.name in fake_locations}
        expected_names = {name for name, trigger in fake_triggers.items() if trigger["ordinal"] <= 2}
        self.assertEqual(created_fake_names, expected_names)
        # Sanity check the fixture itself is exercising the cap (not
        # vacuously passing because nothing at all got created).
        self.assertEqual(len(expected_names), 2)


if __name__ == "__main__":
    unittest.main()
