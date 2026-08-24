# Archipelago/worlds/wow/test/test_optional_categories.py
from .bases import WoWTestBase
from ..locations import _OPTIONAL_CATEGORIES, create_optional_category_locations


class TestOptionalCategoryRegistry(WoWTestBase):
    options = {"game_mode": "sprint", "check_density": 100, "max_optional_locations": 5000}

    def test_registry_holds_exactly_quest_rewards_and_vendor_stock_after_group_1(self) -> None:
        # This test locked in the registry's SHAPE before Group 1 added its
        # first real entry (previously asserted `_OPTIONAL_CATEGORIES == []`,
        # then updated to len == 1 when Task 6 registered quest_rewards) --
        # Task 9 registers vendor_stock as the second entry, so this is
        # updated to len == 2, which was the point: it forces every
        # new-family task to touch this file consciously rather than
        # silently drifting.
        self.assertEqual(len(_OPTIONAL_CATEGORIES), 2)
        self.assertEqual(_OPTIONAL_CATEGORIES[0].key, "quest_rewards")
        self.assertEqual(_OPTIONAL_CATEGORIES[0].toggle_option, "include_quest_rewards")
        self.assertEqual(_OPTIONAL_CATEGORIES[1].key, "vendor_stock")
        self.assertEqual(_OPTIONAL_CATEGORIES[1].toggle_option, "include_vendor_stock")

    def test_sprint_mode_calls_sample_category_when_categories_exist(self) -> None:
        from .. import locations as locations_module

        class _FakeLocationsModule:
            LOCATIONS = {"Fake Loc A": 999900, "Fake Loc B": 999901, "Fake Loc C": 999902}

        fake_category = locations_module.OptionalCategory(
            key="fake", toggle_option="check_density", weight=100,
            locations_module=_FakeLocationsModule, items_module=None,
        )
        locations_module._OPTIONAL_CATEGORIES.append(fake_category)
        try:
            world = self.world
            region = self.multiworld.get_region("Northshire", world.player)
            created = create_optional_category_locations(world, region)
            self.assertEqual(len(created), 3)  # ceil(3 * 1.0 * 1.0) == 3, all sampled
        finally:
            locations_module._OPTIONAL_CATEGORIES.remove(fake_category)

    def test_hundred_percent_mode_stashes_sampled_names_on_world(self) -> None:
        from .. import locations as locations_module

        class _FakeLocationsModule:
            LOCATIONS = {"Fake Loc A": 999900, "Fake Loc B": 999901}

        fake_category = locations_module.OptionalCategory(
            key="fake", toggle_option="include_quest_rewards", weight=100,
            locations_module=_FakeLocationsModule, items_module=None,
        )
        # Swap the registry to hold ONLY the fake category for this test's
        # duration: force_all_categories (100% mode) makes EVERY registered
        # category eligible regardless of its toggle option, so the two
        # already-registered real categories (quest_rewards, vendor_stock)
        # would otherwise also get sampled and pollute the stashed-names
        # assertion below with real content-table rows.
        original_categories = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [fake_category]
        try:
            world = self.world
            world.options.game_mode.value = 12  # hundred_percent
            region = self.multiworld.get_region("Northshire", world.player)
            create_optional_category_locations(world, region)
            self.assertEqual(world.optional_category_sampled_names, {"Fake Loc A", "Fake Loc B"})
        finally:
            locations_module._OPTIONAL_CATEGORIES = original_categories
            if hasattr(world, "optional_category_sampled_names"):
                del world.optional_category_sampled_names


class TestOptionalCategoryRegionsWiring(WoWTestBase):
    # auto_construct = False so we can register the fake category BEFORE
    # world construction runs -- matching the established pattern in
    # test_goals.py (TestGladiatorNotBuildable etc.), which also needs
    # state mutated ahead of self.world_setup(). This exercises the actual
    # regions.py call site (create_regions -> create_optional_category_locations)
    # end to end, unlike TestOptionalCategoryRegistry above, which calls
    # create_optional_category_locations directly and never runs create_regions
    # at all. Without this test, a mistake in regions.py -- e.g. an
    # accidental game_mode gate on the new call, or appending the sampled
    # locations to the wrong region -- would pass the entire suite.
    auto_construct = False
    options = {"game_mode": "sprint", "check_density": 100, "max_optional_locations": 5000}

    def test_registered_category_flows_through_create_regions(self) -> None:
        from .. import locations as locations_module

        class _FakeLocationsModule:
            LOCATIONS = {"Fake Loc A": 999900, "Fake Loc B": 999901, "Fake Loc C": 999902}

        fake_category = locations_module.OptionalCategory(
            key="fake", toggle_option="check_density", weight=100,
            locations_module=_FakeLocationsModule, items_module=None,
        )
        locations_module._OPTIONAL_CATEGORIES.append(fake_category)
        try:
            self.world_setup()
            names = {loc.name for loc in self.multiworld.get_locations(self.world.player)}
            self.assertIn("Fake Loc A", names)
            self.assertIn("Fake Loc B", names)
            self.assertIn("Fake Loc C", names)
        finally:
            locations_module._OPTIONAL_CATEGORIES.remove(fake_category)
