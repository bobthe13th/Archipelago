# Archipelago/worlds/wow/test/test_optional_categories.py
from .bases import WoWTestBase
from .. import WoWWorld
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
    # the unused real ~37,750-row vendor_stock fill from setUp().
    # quest_reward_weight is left unset here, which -- per bases.py's
    # WoWTestBase.world_setup -- means it defaults to 0 too (not the real
    # option default of 100): this class doesn't need the real quest_rewards
    # family sampled either, so that's fine. Several classes below in this
    # file DO need quest_reward_weight restated explicitly at 100, since
    # they reuse that exact option as their fake category's own
    # weight_option proxy -- see each one's own comment.
    options = {"game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0}

    def test_registry_holds_all_nine_families_after_m4_10_5(self) -> None:
        # Locks in the registry's SHAPE after M4.10.5's new family -- forces
        # every future new-family task to touch this file consciously
        # rather than silently drifting.
        self.assertEqual(len(_OPTIONAL_CATEGORIES), 9)
        self.assertEqual(_OPTIONAL_CATEGORIES[0].key, "quest_rewards")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[0].tag_options,
            {"type": "quest_reward_type_pools", "expansion": "quest_reward_expansion_pools"},
        )
        self.assertEqual(_OPTIONAL_CATEGORIES[0].weight_option, "quest_reward_weight")
        self.assertEqual(_OPTIONAL_CATEGORIES[1].key, "vendor_stock")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[1].tag_options,
            {"expansion": "vendor_stock_expansion_pools"},
        )
        self.assertEqual(_OPTIONAL_CATEGORIES[1].weight_option, "vendor_stock_weight")
        self.assertEqual(_OPTIONAL_CATEGORIES[2].key, "recipes")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[2].tag_options,
            {"profession": "recipe_profession_pools", "expansion": "recipe_expansion_pools"},
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[2].weight_option)
        self.assertEqual(_OPTIONAL_CATEGORIES[3].key, "trainer_spells")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[3].tag_options,
            {"class": "trainer_spell_class_pools", "expansion": "trainer_spell_expansion_pools"},
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[3].weight_option)
        self.assertEqual(_OPTIONAL_CATEGORIES[4].key, "containersanity")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[4].tag_options,
            {"expansion": "containersanity_expansion_pools"},
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[4].weight_option)
        self.assertEqual(_OPTIONAL_CATEGORIES[5].key, "gathersanity")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[5].tag_options,
            {"expansion": "gathersanity_expansion_pools", "source": "gathersanity_source_pools"},
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[5].weight_option)
        self.assertEqual(_OPTIONAL_CATEGORIES[6].key, "enemysanity")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[6].tag_options,
            {"type": "enemysanity_type_pools", "expansion": "enemysanity_expansion_pools"},
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[6].weight_option)
        self.assertIsNone(_OPTIONAL_CATEGORIES[6].items_module)
        self.assertEqual(_OPTIONAL_CATEGORIES[7].key, "repsanity")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[7].tag_options,
            {
                "expansion": "repsanity_expansion_pools",
                "rank_tier": "repsanity_rank_tier_pools",
            },
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[7].weight_option)
        self.assertIsNone(_OPTIONAL_CATEGORIES[7].items_module)
        self.assertEqual(_OPTIONAL_CATEGORIES[8].key, "craftsanity")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[8].tag_options,
            {
                "profession": "craftsanity_profession_pools",
                "class": "craftsanity_class_pools",
                "expansion": "craftsanity_expansion_pools",
            },
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[8].weight_option)
        self.assertIsNotNone(_OPTIONAL_CATEGORIES[8].items_module)
        self.assertIn("craftsanity", {c.key for c in _OPTIONAL_CATEGORIES})


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


class TestNoWeightOptionCategoryIncludesEveryTagMatchedRowUnconditionally(WoWTestBase):
    options = {"game_mode": "sprint", "check_density": 0, "vendor_stock_weight": 0}

    def test_zero_check_density_still_includes_every_tag_matched_row_when_weight_option_is_none(self) -> None:
        # The whole point of weight_option=None (M4.9): check_density=0
        # would normally zero out EVERY weight-sampled category
        # (density.sample_category's own math), but a category with no
        # weight_option bypasses that stage entirely -- this is the
        # behavioral proof, not just the registry shape.
        world = self.world
        region = self.multiworld.get_region("Northshire", world.player)
        fake_category = OptionalCategory(
            key="fake", tag_options={}, locations_module=_FakeLocationsModule, items_module=_FakeItemsModule,
        )
        from .. import locations as locations_module
        original = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [fake_category]
        try:
            created = create_optional_category_locations(world, region)
            self.assertEqual(len(created), 10)
        finally:
            locations_module._OPTIONAL_CATEGORIES = original


class TestOptionalCategoriesFullyRegisteredInWorldDatapackage(WoWTestBase):
    # M4.9.2 final review, Finding 2: a family can be fully compiled and
    # correctly appended to _OPTIONAL_CATEGORIES (locations.py) while still
    # never being spread into WoWWorld.location_name_to_id/item_name_to_id
    # (__init__.py) -- that exact gap shipped for recipes/trainer_spells
    # and was only caught by AP-core's separate test/general datapackage
    # tests, which this milestone never ran. This test closes that gap at
    # the wow-scoped level: every LOCATIONS/ITEMS key of every registered
    # family must resolve in the world's own name-to-id maps.
    def test_every_registered_family_locations_and_items_are_in_world_maps(self) -> None:
        for category in _OPTIONAL_CATEGORIES:
            missing_locations = set(category.locations_module.LOCATIONS) - set(WoWWorld.location_name_to_id)
            self.assertEqual(
                missing_locations, set(),
                f"{category.key}: locations missing from WoWWorld.location_name_to_id",
            )
            if category.items_module is not None:
                missing_items = set(category.items_module.ITEMS) - set(WoWWorld.item_name_to_id)
                self.assertEqual(
                    missing_items, set(),
                    f"{category.key}: items missing from WoWWorld.item_name_to_id",
                )


class TestCraftsanityRealGeneration(WoWTestBase):
    # M4.10.5: regression test for craftsanity's tag dimension handling.
    # Craftsanity has items with mutually exclusive tag dimensions (either
    # 'profession' or 'class', never both). A bug in _location_matches_pools
    # where missing dimensions were treated as empty sets would cause ALL
    # 1698 craftsanity items to fail matching under full inclusion, making
    # the family completely non-functional. This test verifies that under
    # full inclusion (all profession/class/expansion values selected),
    # craftsanity produces real locations of both types, and under full
    # exclusion (empty pools), produces zero craftsanity locations.
    options = {
        "game_mode": "sprint",
        "check_density": 100,
        "vendor_stock_weight": 0,
        "craftsanity_profession_pools": {
            "alchemy", "blacksmithing", "cooking", "enchanting", "engineering",
            "first_aid", "inscription", "jewelcrafting", "leatherworking",
            "mining", "other", "tailoring"
        },
        "craftsanity_class_pools": {"mage", "warlock"},
        "craftsanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
    }

    def test_craftsanity_includes_profession_tagged_items_under_full_inclusion(self) -> None:
        # Under full profession pool inclusion, profession-tagged locations
        # must appear (verify at least one real profession-tagged craft).
        location_names = {loc.name for loc in self.multiworld.get_locations(self.world.player)}
        self.assertIn("Craft: Goretusk Liver Pie (#724)", location_names)

    def test_craftsanity_includes_class_tagged_items_under_full_inclusion(self) -> None:
        # Under full class pool inclusion, class-tagged (mage/warlock) items
        # must appear (verify at least one real class-tagged craft).
        location_names = {loc.name for loc in self.multiworld.get_locations(self.world.player)}
        self.assertIn("Craft: Conjured Bread (#1113)", location_names)


class TestCraftsanityExcludedWithEmptyPools(WoWTestBase):
    # M4.10.5: verify inverse -- with empty craftsanity pools (test speed
    # defaults), zero craftsanity locations should be created.
    options = {
        "game_mode": "sprint",
        "check_density": 100,
        "vendor_stock_weight": 0,
        "craftsanity_profession_pools": set(),
        "craftsanity_class_pools": set(),
        "craftsanity_expansion_pools": set(),
    }

    def test_craftsanity_produces_zero_locations_with_empty_pools(self) -> None:
        # With all pools empty, AND-across-dimensions logic ensures no
        # craftsanity items match.
        location_names = {loc.name for loc in self.multiworld.get_locations(self.world.player)}
        craftsanity_locs = {name for name in location_names if name.startswith("Craft:")}
        self.assertEqual(len(craftsanity_locs), 0)
