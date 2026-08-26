# Archipelago/worlds/wow/test/test_optional_categories.py
from .bases import WoWTestBase
from ..locations import _OPTIONAL_CATEGORIES, OptionalCategory, create_optional_category_locations, _location_matches_pools


class _FakeLocationsModule:
    LOCATIONS = {f"Fake Loc {i}": 999900 + i for i in range(10)}
    TAGS = {
        name: {"kind": frozenset({"alpha"} if i < 5 else {"beta"})}
        for i, name in enumerate(LOCATIONS)
    }
    ALWAYS_PRESENT = frozenset()


class _FakeItemsModule:
    ITEMS = {f"Fake Item {i}": (999800 + i, 1) for i in range(10)}


class TestOptionalCategoryRegistry(WoWTestBase):
    # vendor_stock_weight: 0 (M4.8.0) -- this test only inspects the
    # registry's static shape, never any sampled content; capping removes
    # the unused real ~37,750-row vendor_stock fill from setUp(). Left
    # quest_reward_weight unset -- several classes below in this file reuse
    # that exact option as their fake category's own weight_option proxy,
    # so it's kept consistent at its real default across this file rather
    # than capped per-class (this one class alone doesn't need the cap).
    options = {"game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0}

    def test_registry_holds_exactly_quest_rewards_and_vendor_stock_after_m4_8(self) -> None:
        # Locks in the registry's SHAPE after M4.8.0's tag_options/weight_option
        # rewrite -- forces every future new-family task to touch this file
        # consciously rather than silently drifting.
        self.assertEqual(len(_OPTIONAL_CATEGORIES), 2)
        self.assertEqual(_OPTIONAL_CATEGORIES[0].key, "quest_rewards")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[0].tag_options,
            {"type": "quest_reward_type_pools", "expansion": "quest_reward_expansion_pools"},
        )
        self.assertEqual(_OPTIONAL_CATEGORIES[0].weight_option, "quest_reward_weight")
        self.assertEqual(_OPTIONAL_CATEGORIES[1].key, "vendor_stock")
        self.assertEqual(_OPTIONAL_CATEGORIES[1].tag_options, {"expansion": "vendor_stock_expansion_pools"})
        self.assertEqual(_OPTIONAL_CATEGORIES[1].weight_option, "vendor_stock_weight")


class TestLocationMatchesPools(WoWTestBase):
    options = {
        "game_mode": "sprint",
        "quest_reward_type_pools": {"dungeon_quest"},
        "quest_reward_expansion_pools": {"vanilla", "tbc"},
    }

    def test_and_across_dimensions_or_within_dimension(self) -> None:
        world = self.world

        class _Loc:
            TAGS = {
                "match_both": {"type": frozenset({"dungeon_quest"}), "expansion": frozenset({"vanilla"})},
                "match_type_only": {"type": frozenset({"dungeon_quest"}), "expansion": frozenset({"wotlk"})},
                "match_expansion_only": {"type": frozenset({"elite_quest"}), "expansion": frozenset({"tbc"})},
                "match_neither": {"type": frozenset({"elite_quest"}), "expansion": frozenset({"wotlk"})},
                "match_via_or_within_type": {"type": frozenset({"repeatable", "dungeon_quest"}), "expansion": frozenset({"tbc"})},
            }
            LOCATIONS = {name: i for i, name in enumerate(TAGS)}
            ALWAYS_PRESENT = frozenset()

        category = OptionalCategory(
            key="fake",
            tag_options={"type": "quest_reward_type_pools", "expansion": "quest_reward_expansion_pools"},
            weight_option="quest_reward_weight",
            locations_module=_Loc, items_module=None,
        )
        self.assertTrue(_location_matches_pools(world, category, "match_both"))
        self.assertFalse(_location_matches_pools(world, category, "match_type_only"))
        self.assertFalse(_location_matches_pools(world, category, "match_expansion_only"))
        self.assertFalse(_location_matches_pools(world, category, "match_neither"))
        self.assertTrue(_location_matches_pools(world, category, "match_via_or_within_type"))


class TestZeroRegressionDefaultTagSelection(WoWTestBase):
    # vendor_stock_weight: 0 (M4.8.0) -- see TestOptionalCategoryRegistry's
    # own comment above; this test's fake category only ever reuses
    # quest_reward_weight as its proxy, never vendor_stock_weight.
    # quest_reward_weight: 100 -- this class's fake category reads
    # quest_reward_weight as ITS OWN weight (weight_option proxy, see
    # below) and the test body never reassigns it explicitly, so it must
    # be stated at 100 here: bases.py's WoWTestBase.world_setup now
    # defaults quest_reward_weight to 0 for any class that doesn't set it
    # explicitly, which would otherwise make this test's fake 10-row
    # category sample 0 instead of all 10.
    options = {"game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0, "quest_reward_weight": 100}

    def test_default_tag_selection_passes_every_location_through(self) -> None:
        # Default OptionSets select the full vocabulary (spec §2's
        # zero-regression default) -- combined with check_density=100 and
        # quest_reward_weight's own default of 100, every one of the fake
        # category's 10 rows must come through, regardless of tag content.
        # Bug fixed here (M4.8.0): the selected set below must match the
        # FAKE category's own tag values ("alpha"/"beta", per
        # _FakeLocationsModule.TAGS) -- this fake category deliberately
        # reuses quest_reward_type_pools purely as a proxy weight_option/
        # tag_options field name, not the real vocabulary, so selecting the
        # real dungeon_quest/elite_quest/etc. strings here (which the fake
        # rows never carry) made _location_matches_pools's AND-across-
        # dimensions intersection empty for every row, unconditionally --
        # not what this test's own docstring intends to check.
        world = self.world
        region = self.multiworld.get_region("Northshire", world.player)
        fake_category = OptionalCategory(
            key="fake",
            tag_options={"kind": "quest_reward_type_pools"},
            weight_option="quest_reward_weight",
            locations_module=_FakeLocationsModule, items_module=_FakeItemsModule,
        )
        from .. import locations as locations_module
        original = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [fake_category]
        try:
            world.options.quest_reward_type_pools.value = {"alpha", "beta"}
            created = create_optional_category_locations(world, region)
            self.assertEqual(len(created), 10)
        finally:
            locations_module._OPTIONAL_CATEGORIES = original


class TestTwoStageComposition(WoWTestBase):
    # vendor_stock_weight: 0 (M4.8.0) -- see TestOptionalCategoryRegistry's
    # own comment; unused here, this class's fake category only reuses
    # quest_reward_weight as its proxy (explicitly reassigned per-test
    # below).
    options = {
        "game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0,
        "quest_reward_type_pools": {"dungeon_quest"},  # dummy real value; overwritten per-test below
    }

    def _fake_category(self):
        return OptionalCategory(
            key="fake",
            tag_options={"kind": "quest_reward_type_pools"},
            weight_option="quest_reward_weight",
            locations_module=_FakeLocationsModule, items_module=None,
        )

    def test_narrow_tag_selection_then_full_weight_yields_all_tag_matched_rows(self) -> None:
        world = self.world
        world.options.quest_reward_type_pools.value = {"alpha"}  # narrows _FakeLocationsModule's 10 rows to 5
        world.options.quest_reward_weight.value = 100
        region = self.multiworld.get_region("Northshire", world.player)
        from .. import locations as locations_module
        original = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [self._fake_category()]
        try:
            created = create_optional_category_locations(world, region)
            self.assertEqual(len(created), 5)
            names = {loc.name for loc in created}
            self.assertEqual(names, {f"Fake Loc {i}" for i in range(5)})
        finally:
            locations_module._OPTIONAL_CATEGORIES = original

    def test_narrow_tag_selection_then_half_weight_never_draws_from_tag_excluded_rows(self) -> None:
        world = self.world
        world.options.quest_reward_type_pools.value = {"alpha"}
        world.options.quest_reward_weight.value = 50
        region = self.multiworld.get_region("Northshire", world.player)
        from .. import locations as locations_module
        original = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [self._fake_category()]
        try:
            created = create_optional_category_locations(world, region)
            self.assertEqual(len(created), 3)  # ceil(5 * 1.0 * 0.5) == 3
            names = {loc.name for loc in created}
            self.assertTrue(names.issubset({f"Fake Loc {i}" for i in range(5)}))
        finally:
            locations_module._OPTIONAL_CATEGORIES = original


class TestAlwaysPresentBypassesTagsAndWeight(WoWTestBase):
    # vendor_stock_weight: 0 (M4.8.0) -- see TestOptionalCategoryRegistry's
    # own comment; unused here, this class's fake category reuses
    # quest_reward_weight as its proxy (explicitly reassigned to 0 below).
    options = {
        "game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0,
        "quest_reward_type_pools": {"dungeon_quest"},
    }

    def test_always_present_location_created_even_with_empty_tag_selection_and_zero_weight(self) -> None:
        world = self.world
        world.options.quest_reward_type_pools.value = set()  # would normally exclude everything
        world.options.quest_reward_weight.value = 0
        region = self.multiworld.get_region("Northshire", world.player)

        class _Loc(_FakeLocationsModule):
            ALWAYS_PRESENT = frozenset({"Fake Loc 0"})

        fake_category = OptionalCategory(
            key="fake", tag_options={"kind": "quest_reward_type_pools"},
            weight_option="quest_reward_weight", locations_module=_Loc, items_module=None,
        )
        from .. import locations as locations_module
        original = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [fake_category]
        try:
            created = create_optional_category_locations(world, region)
            names = {loc.name for loc in created}
            self.assertEqual(names, {"Fake Loc 0"})
        finally:
            locations_module._OPTIONAL_CATEGORIES = original


class TestHundredPercentModeStashesSampledNames(WoWTestBase):
    def test_hundred_percent_mode_stashes_sampled_names_on_world(self) -> None:
        from .. import locations as locations_module

        class _FakeLocationsModuleSmall:
            LOCATIONS = {"Fake Loc A": 999900, "Fake Loc B": 999901}
            TAGS = {name: {} for name in LOCATIONS}
            ALWAYS_PRESENT = frozenset()

        class _FakeItemsModuleSmall:
            ITEMS = {"Fake Item A": (999800, 1), "Fake Item B": (999801, 1)}

        fake_category = OptionalCategory(
            key="fake", tag_options={}, weight_option="quest_reward_weight",
            locations_module=_FakeLocationsModuleSmall, items_module=_FakeItemsModuleSmall,
        )
        original_categories = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [fake_category]
        try:
            world = self.world
            world.options.game_mode.value = 12  # hundred_percent
            region = self.multiworld.get_region("Northshire", world.player)
            create_optional_category_locations(world, region)
            self.assertEqual(world.optional_category_sampled_names, {"Fake Item A", "Fake Item B"})
        finally:
            locations_module._OPTIONAL_CATEGORIES = original_categories
            if hasattr(world, "optional_category_sampled_names"):
                del world.optional_category_sampled_names


class TestOptionalCategoryRegionsWiring(WoWTestBase):
    auto_construct = False
    # vendor_stock_weight: 0 (M4.8.0) -- see TestOptionalCategoryRegistry's
    # own comment; unused here, this class's appended fake category reuses
    # quest_reward_weight as its proxy. quest_reward_weight: 100 -- must be
    # stated explicitly (see TestZeroRegressionDefaultTagSelection's own
    # comment on why "leave it unset" no longer works); this class APPENDS
    # its fake category to the real registry rather than replacing it, so
    # the real quest_rewards family is also sampled during this manual
    # world_setup() call, at its own real default -- consistent with this
    # class's behavior before bases.py's new default existed.
    options = {"game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0, "quest_reward_weight": 100}

    def test_registered_category_flows_through_create_regions(self) -> None:
        from .. import locations as locations_module

        fake_category = OptionalCategory(
            key="fake", tag_options={}, weight_option="quest_reward_weight",
            locations_module=_FakeLocationsModule, items_module=None,
        )
        locations_module._OPTIONAL_CATEGORIES.append(fake_category)
        try:
            self.world_setup()
            names = {loc.name for loc in self.multiworld.get_locations(self.world.player)}
            for i in range(10):
                self.assertIn(f"Fake Loc {i}", names)
        finally:
            locations_module._OPTIONAL_CATEGORIES.remove(fake_category)
