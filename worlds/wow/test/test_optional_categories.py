# Archipelago/worlds/wow/test/test_optional_categories.py
from .. import density
from .bases import WoWTestBase
from ..locations import _OPTIONAL_CATEGORIES, create_optional_category_locations


class TestOptionalCategoryRegistry(WoWTestBase):
    options = {"game_mode": "sprint", "check_density": 100, "max_optional_locations": 5000}

    def test_registry_starts_empty_before_any_family_registers(self) -> None:
        # This test locks in the registry's SHAPE before Group 1 adds its
        # first real entry -- once quest_rewards registers, this assertion
        # is expected to need updating to len == 1, which is the point:
        # it forces every new-family task to touch this file consciously.
        self.assertEqual(_OPTIONAL_CATEGORIES, [])

    def test_sprint_mode_calls_sample_category_when_categories_exist(self) -> None:
        # Regression guard for the exact M4 bug this task fixes: Sprint mode
        # must be able to pull SOME locations through the density budget,
        # once at least one category is registered. Uses a fake in-test
        # category rather than waiting for Group 1's real one to land.
        from .. import locations as locations_module

        class _FakeLocationsModule:
            LOCATIONS = {"Fake Loc A": 999900, "Fake Loc B": 999901, "Fake Loc C": 999902}

        fake_category = locations_module.OptionalCategory(
            key="fake", toggle_option="check_density", weight=100,
            locations_module=_FakeLocationsModule, items_module=None,
        )
        locations_module._OPTIONAL_CATEGORIES.append(fake_category)
        try:
            # NOTE: WorldTestBase.setUp() already called self.world_setup()
            # once (auto_construct defaults True) before this test method
            # runs -- self.world/self.multiworld are already populated by
            # then; world_setup() itself returns None, it doesn't hand back
            # a World. Do not call self.world_setup() again here.
            world = self.world
            budget = density.DensityBudget(check_density=100, hard_ceiling=5000)
            region = self.multiworld.get_region("Northshire", world.player)
            created = create_optional_category_locations(world, region, budget)
            self.assertEqual(len(created), 3)  # ceil(3 * 1.0 * 1.0) == 3, all sampled
        finally:
            locations_module._OPTIONAL_CATEGORIES.remove(fake_category)


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
