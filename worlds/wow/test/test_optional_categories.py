# Archipelago/worlds/wow/test/test_optional_categories.py
from .bases import WoWTestBase
from .. import WoWWorld
from .. import (
    craftsanity_content_data, itemsanity_content_data, options, quest_rewards_content_data, recipes_content_data,
    repsanity_content_data, trainer_spells_content_data, zone_leveler_content_data,
)
from ..locations import (
    _OPTIONAL_CATEGORIES, OptionalCategory, create_optional_category_locations, _location_matches_pools,
    _POSSESSION_TRIGGERED_CATEGORY_KEYS, _zone_leveler_possession_family_min_level, _zone_leveler_scope_matches,
    _zone_leveler_quest_reward_zone_matches, _zone_leveler_trainer_spell_zone_matches,
)


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

    def test_registry_holds_all_ten_families_after_m4_10_6(self) -> None:
        # Locks in the registry's SHAPE after M4.10.6's new family -- forces
        # every future new-family task to touch this file consciously
        # rather than silently drifting.
        self.assertEqual(len(_OPTIONAL_CATEGORIES), 10)
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
        self.assertEqual(_OPTIONAL_CATEGORIES[9].key, "itemsanity")
        self.assertEqual(
            _OPTIONAL_CATEGORIES[9].tag_options,
            {
                "class": "itemsanity_class_pools",
                "quality": "itemsanity_quality_pools",
                "expansion": "itemsanity_expansion_pools",
            },
        )
        self.assertIsNone(_OPTIONAL_CATEGORIES[9].weight_option)
        self.assertIsNotNone(_OPTIONAL_CATEGORIES[9].items_module)
        self.assertIn("craftsanity", {c.key for c in _OPTIONAL_CATEGORIES})
        self.assertIn("itemsanity", {c.key for c in _OPTIONAL_CATEGORIES})


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


class TestZoneLevelerPossessionFamilyMinLevel(WoWTestBase):
    """M4.11.1 Task 12: unit-level coverage of the min_level lookup helper
    itself, calling module data directly rather than paying for a full
    zone_leveler slot generation."""
    options = {}

    def test_itemsanity_row_carries_a_real_int_min_level(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "itemsanity")
        name = next(iter(itemsanity_content_data.LOCATIONS))
        min_level = _zone_leveler_possession_family_min_level(name, category)
        self.assertIsInstance(min_level, int)

    def test_trainer_spells_row_carries_a_real_int_min_level(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "trainer_spells")
        name = next(iter(trainer_spells_content_data.LOCATIONS))
        min_level = _zone_leveler_possession_family_min_level(name, category)
        self.assertIsInstance(min_level, int)

    def test_recipes_row_carries_a_real_int_min_level(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "recipes")
        name = next(iter(recipes_content_data.LOCATIONS))
        min_level = _zone_leveler_possession_family_min_level(name, category)
        self.assertIsInstance(min_level, int)

    def test_craftsanity_has_no_real_min_level_data(self) -> None:
        # By design, not an oversight -- crafting requirements are
        # skill-tier-gated, not player-level-gated; see
        # _zone_leveler_possession_family_min_level's own docstring.
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "craftsanity")
        name = next(iter(craftsanity_content_data.LOCATIONS))
        self.assertIsNone(_zone_leveler_possession_family_min_level(name, category))

    def test_repsanity_has_no_real_min_level_data(self) -> None:
        # By design -- reputation ranks are not level-gated at all.
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "repsanity")
        name = next(iter(repsanity_content_data.LOCATIONS))
        self.assertIsNone(_zone_leveler_possession_family_min_level(name, category))


class TestZoneLevelerScopeMatchesUnaffectsNonPossessionCategories(WoWTestBase):
    """M4.11.1 Task 12 (post-hoc fix round): _zone_leveler_scope_matches
    always returns True for a category that is BOTH outside
    _POSSESSION_TRIGGERED_CATEGORY_KEYS AND not "quest_rewards",
    independent of content_scope -- vendor_stock has no real zone data
    curated at all (that's M4.11.2's full-breadth follow-up), so this
    generic path doesn't touch it either way. Quest Rewards used to be
    covered by this same always-True generic path too, but the fix round
    gave it its own dedicated, real zone-id-based restriction instead (see
    TestZoneLevelerQuestRewardZoneMatches/
    TestZoneLevelerQuestRewardsRestrictedToSelectedZoneRegardlessOfContentScope
    below) -- it is deliberately no longer exercised by this class.
    Exercised via a fake world/options object (same types.SimpleNamespace
    pattern test_goals.py's own TestValidateZoneLevelerFullDensity already
    uses) rather than a full slot generation, since this is a pure
    function-behavior fact."""
    options = {}

    def test_non_possession_non_quest_reward_category_always_matches_under_zone_only(self) -> None:
        import types

        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "vendor_stock")
        world = types.SimpleNamespace(options=types.SimpleNamespace(
            zone_leveler_content_scope="zone_only",
            zone_leveler_starting_zone=types.SimpleNamespace(current_key="barrens"),
        ))
        self.assertTrue(_zone_leveler_scope_matches(world, category, "irrelevant-name"))


# M4.11.1 Task 12: every possession-triggered family's own tag pools widened
# to their full real default -- bases.py's WoWTestBase otherwise zeroes
# several of them for test speed. Widening them here isolates the
# zone-scope filter itself as the thing excluding/including rows below, not
# an incidental empty/narrow tag pool.
#
# NOTE: deliberately NOT shared via subclassing between the two content_scope
# test classes below (zone_only vs. whole_game_scaled) -- an earlier draft
# had TestZoneLevelerWholeGameScaledWidensTractableFamilies subclass
# TestZoneLevelerContentScope for its options, but unittest then also
# inherits (and re-runs) the PARENT's own zone_only-specific test method
# under the SUBCLASS's whole_game_scaled options, where it legitimately
# fails (itemsanity rows ARE present under whole_game_scaled). Two sibling
# classes sharing this same base-options constant avoids that trap.
_ZONE_LEVELER_BASE_OPTIONS = {
    "game_mode": "zone_leveler",
    "zone_leveler_starting_zone": "barrens",
    "zone_leveler_goals": {"reach_zone_level_cap"},
    "itemsanity_class_pools": set(options.ItemsanityClassPools.default),
    "itemsanity_quality_pools": set(options.ItemsanityQualityPools.default),
    "itemsanity_expansion_pools": set(options.ItemsanityExpansionPools.default),
    "craftsanity_profession_pools": set(options.CraftsanityProfessionPools.default),
    "craftsanity_class_pools": set(options.CraftsanityClassPools.default),
    "craftsanity_expansion_pools": set(options.CraftsanityExpansionPools.default),
    "repsanity_expansion_pools": set(options.RepsanityExpansionPools.default),
    "repsanity_rank_tier_pools": set(options.RepsanityRankTierPools.default),
    "recipe_profession_pools": set(options.RecipeProfessionPools.default),
    "recipe_expansion_pools": set(options.RecipeExpansionPools.default),
    "trainer_spell_class_pools": set(options.TrainerSpellClassPools.default),
    "trainer_spell_expansion_pools": set(options.TrainerSpellExpansionPools.default),
}


class TestZoneLevelerContentScope(WoWTestBase):
    """M4.11.1 Task 12: zone_only excludes every possession-triggered
    family's rows entirely, regardless of tag-pool selection.
    zone_leveler_goals is narrowed to reach_zone_level_cap alone -- same
    reasoning test_basic.py's TestZoneLevelerCoreLoop/TestGoldenBoarStatues
    already document: the default goal set requires quest_reward pooling,
    which WoWTestBase zeroes for speed, making the game unbeatable unless a
    class also narrows the goal set."""
    options = {**_ZONE_LEVELER_BASE_OPTIONS, "zone_leveler_content_scope": "zone_only"}

    def test_zone_only_excludes_every_possession_triggered_family(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for key in _POSSESSION_TRIGGERED_CATEGORY_KEYS:
            category = next(c for c in _OPTIONAL_CATEGORIES if c.key == key)
            overlap = names & set(category.locations_module.LOCATIONS)
            self.assertEqual(len(overlap), 0, f"{key} rows leaked through zone_only")


class TestZoneLevelerWholeGameScaledWidensTractableFamilies(WoWTestBase):
    """M4.11.1 Task 12: whole_game_scaled widens exactly the 3 tractable
    possession-triggered families (Itemsanity, Recipes, Trainer Spells) to
    rows whose own real min_level falls inside Barrens' level band
    (10-30, zone_leveler_content_data.ZONES["barrens"]), and leaves
    Craftsanity/Repsanity fully excluded -- same as zone_only for those two
    -- since neither carries real min_level data to widen by.

    zone_leveler_allow_hub_zone is set True here (M4.11.2): Trainer Spells
    is now ADDITIONALLY gated by _zone_leveler_trainer_spell_zone_matches
    (real trainer position data), and confirmed against the live DB, zero
    real class trainers stand in the open-world Barrens zone itself (id 17)
    -- every one of them is in a capital city, and for Barrens' own roster
    that means Orgrimmar/Durotar (the curated allowed_hub_zone_ids). Without
    this toggle on, the level-band widening this test targets would never
    have any trainer_spells row to widen INTO, which would defeat the point
    of this test (which is about the min_level axis, not the zone axis)."""
    options = {
        **_ZONE_LEVELER_BASE_OPTIONS, "zone_leveler_content_scope": "whole_game_scaled",
        "zone_leveler_allow_hub_zone": True,
    }

    def test_itemsanity_widens_to_rows_inside_barrens_level_band(self) -> None:
        band = zone_leveler_content_data.ZONES["barrens"]
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        widened = names & set(itemsanity_content_data.LOCATIONS)
        self.assertGreater(len(widened), 0)
        for name in widened:
            min_level = itemsanity_content_data.TRIGGERS[name]["min_level"]
            self.assertGreaterEqual(min_level, band.min_level)
            self.assertLessEqual(min_level, band.max_level)

    def test_trainer_spells_widens_to_rows_inside_barrens_level_band(self) -> None:
        band = zone_leveler_content_data.ZONES["barrens"]
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        widened = names & set(trainer_spells_content_data.LOCATIONS)
        self.assertGreater(len(widened), 0)
        for name in widened:
            min_level = trainer_spells_content_data.TRIGGERS[name]["min_level"]
            self.assertGreaterEqual(min_level, band.min_level)
            self.assertLessEqual(min_level, band.max_level)

    def test_recipes_widens_to_rows_inside_barrens_level_band(self) -> None:
        band = zone_leveler_content_data.ZONES["barrens"]
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        widened = names & set(recipes_content_data.LOCATIONS)
        self.assertGreater(len(widened), 0)
        for name in widened:
            min_level = recipes_content_data.TRIGGERS[name]["min_level"]
            self.assertGreaterEqual(min_level, band.min_level)
            self.assertLessEqual(min_level, band.max_level)

    def test_craftsanity_stays_fully_excluded_but_repsanity_includes_vanilla(self) -> None:
        # M4.11.2: Craftsanity has no real min_level data to widen by
        # (see _zone_leveler_possession_family_min_level's own docstring) --
        # whole_game_scaled behaves identically to zone_only for this family,
        # even with tag pools wide open. Repsanity, by contrast, is now
        # filtered by expansion tag (vanilla-only under zone_leveler),
        # regardless of content_scope, so vanilla-tagged repsanity factions
        # are includable.
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertEqual(len(names & set(craftsanity_content_data.LOCATIONS)), 0)
        # Verify some vanilla repsanity rows ARE present
        repsanity_rows = names & set(repsanity_content_data.LOCATIONS)
        self.assertGreater(len(repsanity_rows), 0)
        # Verify all present repsanity rows are vanilla-tagged
        for name in repsanity_rows:
            expansion_tags = repsanity_content_data.TAGS[name].get("expansion", frozenset())
            self.assertIn("vanilla", expansion_tags)


class TestZoneLevelerTrainerSpellZoneMatches(WoWTestBase):
    """M4.11.2: Trainer Spells is the one possession-triggered family that
    is ALSO physically zone-bound (a real trainer NPC must be visited), so
    under whole_game_scaled it needs BOTH its existing min_level check AND
    this new trainer_zone_ids check to include a row. zone_leveler_allow_hub_zone
    is on here -- both spells below have real min_level within 10-30
    (Frost Nova: 10; Teleport: Stormwind: 20), so without the hub toggle
    both would qualify on min_level alone and this test wouldn't isolate
    the NEW zone check at all; confirmed live-DB numbers (extract_trainer_
    spells.py's own trainer_zone_ids): Frost Nova (#122) resolves to,
    among others, Durotar (14) and Orgrimmar (1637); Teleport: Stormwind
    (#3561) resolves ONLY to Stormwind itself (1519) -- no Horde-hub
    trainer teaches it, matching the real game (an Alliance-only
    teleport spell)."""
    options = {
        "game_mode": "zone_leveler", "zone_leveler_starting_zone": "barrens",
        "zone_leveler_content_scope": "whole_game_scaled", "zone_leveler_allow_hub_zone": True,
        "zone_leveler_goals": {"reach_zone_level_cap"},
        "trainer_spell_class_pools": set(options.TrainerSpellClassPools.default),
        "trainer_spell_expansion_pools": set(options.TrainerSpellExpansionPools.default),
    }

    def test_known_orgrimmar_taught_spell_included(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Trainer Spell: Frost Nova (#122)", location_names)

    def test_spell_with_no_horde_hub_trainer_excluded(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Trainer Spell: Teleport: Stormwind (#3561)", location_names)


class TestZoneLevelerTrainerSpellZoneMatchesUnit(WoWTestBase):
    """M4.11.2: unit-level coverage of _zone_leveler_trainer_spell_zone_matches
    itself, calling it directly against real trainer_spells_content_data.TRIGGERS
    rows (same fake-world types.SimpleNamespace pattern
    TestZoneLevelerQuestRewardZoneMatches uses above) rather than paying for
    a full zone_leveler slot generation."""
    options = {}

    @staticmethod
    def _fake_world(allow_hub_zone: bool, zone_key: str = "barrens"):
        import types

        return types.SimpleNamespace(options=types.SimpleNamespace(
            zone_leveler_starting_zone=types.SimpleNamespace(current_key=zone_key),
            zone_leveler_allow_hub_zone=allow_hub_zone,
        ))

    def test_frost_nova_matches_when_hub_zone_allowed(self) -> None:
        name = "Trainer Spell: Frost Nova (#122)"
        self.assertTrue({14, 1637} & set(trainer_spells_content_data.TRIGGERS[name]["trainer_zone_ids"]))
        self.assertTrue(_zone_leveler_trainer_spell_zone_matches(self._fake_world(True), name))

    def test_frost_nova_does_not_match_when_hub_zone_disallowed(self) -> None:
        # No real class trainer stands in the open-world Barrens zone (17)
        # itself -- confirmed against the live DB -- so with the hub toggle
        # off, this real Durotar/Orgrimmar-taught spell is out of bounds.
        name = "Trainer Spell: Frost Nova (#122)"
        self.assertFalse(_zone_leveler_trainer_spell_zone_matches(self._fake_world(False), name))

    def test_teleport_stormwind_never_matches_barrens(self) -> None:
        # Resolves only to Stormwind (1519) -- not Barrens (17) nor either
        # of Barrens' own curated hub zones (14/1637) -- so this stays
        # excluded regardless of the hub toggle.
        name = "Trainer Spell: Teleport: Stormwind (#3561)"
        self.assertFalse(_zone_leveler_trainer_spell_zone_matches(self._fake_world(True), name))
        self.assertFalse(_zone_leveler_trainer_spell_zone_matches(self._fake_world(False), name))


class TestZoneLevelerQuestRewardZoneMatches(WoWTestBase):
    """M4.11.1 Task 12 post-hoc fix round: unit-level coverage of
    _zone_leveler_quest_reward_zone_matches itself, calling it directly
    against real quest_rewards_content_data.TRIGGERS rows (same fake-world
    types.SimpleNamespace pattern
    TestZoneLevelerScopeMatchesUnaffectsNonPossessionCategories uses)
    rather than paying for a full zone_leveler slot generation.

    The confirmed bug: Quest Rewards is a real, physically zone-bound
    family (a real quest-giver NPC), but the OLD code let
    category.key == "quest_rewards" fall through
    _zone_leveler_scope_matches' "not in
    _POSSESSION_TRIGGERED_CATEGORY_KEYS -> always True" branch, so a
    Barrens slot could sample a quest whose quest-giver stands in a
    totally different, unreachable zone -- reachable per AP's own logic
    (no equivalent of Dark Portal Access gates same-continent vanilla
    travel) but physically un-walkable-to given the zone lock. These tests
    confirm the fix: only a row whose own real zone_id equals the
    selected zone's real zone_id matches, and this holds regardless of
    zone_leveler_content_scope (unlike the 5 possession-triggered
    families, Quest Rewards' restriction is not gated by that toggle at
    all)."""
    options = {}

    @staticmethod
    def _fake_world(content_scope: str, zone_key: str = "barrens"):
        import types

        return types.SimpleNamespace(options=types.SimpleNamespace(
            zone_leveler_content_scope=content_scope,
            zone_leveler_starting_zone=types.SimpleNamespace(current_key=zone_key),
        ))

    def test_row_in_selected_zone_matches_under_zone_only(self) -> None:
        # "Quest: Chen's Empty Keg Reward (#819)" -- real zone_id 17
        # (The Barrens), confirmed by direct TRIGGERS inspection.
        name = "Quest: Chen's Empty Keg Reward (#819)"
        self.assertEqual(quest_rewards_content_data.TRIGGERS[name]["zone_id"], 17)
        world = self._fake_world("zone_only")
        self.assertTrue(_zone_leveler_quest_reward_zone_matches(world, name))

    def test_row_in_selected_zone_matches_under_whole_game_scaled(self) -> None:
        # Same row, but under whole_game_scaled -- must still match; the
        # content_scope toggle never affects Quest Rewards at all.
        name = "Quest: Chen's Empty Keg Reward (#819)"
        world = self._fake_world("whole_game_scaled")
        self.assertTrue(_zone_leveler_quest_reward_zone_matches(world, name))

    def test_row_in_a_different_real_zone_is_excluded(self) -> None:
        # "Quest: Kanrethad's Quest Reward (#1)" -- real zone_id 151
        # (a real, resolved zone, just not Barrens), confirmed by direct
        # TRIGGERS inspection. Must be excluded under BOTH content_scope
        # values -- this is not the possession-triggered widening path.
        name = "Quest: Kanrethad's Quest Reward (#1)"
        self.assertEqual(quest_rewards_content_data.TRIGGERS[name]["zone_id"], 151)
        self.assertFalse(_zone_leveler_quest_reward_zone_matches(self._fake_world("zone_only"), name))
        self.assertFalse(_zone_leveler_quest_reward_zone_matches(self._fake_world("whole_game_scaled"), name))

    def test_row_with_unresolvable_zone_sentinel_is_excluded(self) -> None:
        # "Quest: A Lesson to Learn Reward (#26)" -- real zone_id 0, this
        # data's own "unresolvable, real zone unknown" sentinel. The safe
        # default for a physically zone-locked game mode is exclusion, not
        # inclusion, since we genuinely don't know this row's real zone.
        name = "Quest: A Lesson to Learn Reward (#26)"
        self.assertEqual(quest_rewards_content_data.TRIGGERS[name]["zone_id"], 0)
        self.assertFalse(_zone_leveler_quest_reward_zone_matches(self._fake_world("zone_only"), name))
        self.assertFalse(_zone_leveler_quest_reward_zone_matches(self._fake_world("whole_game_scaled"), name))


# M4.11.1 Task 12 post-hoc fix round: a lighter options base than
# _ZONE_LEVELER_BASE_OPTIONS above -- this class is only about Quest
# Rewards' own zone restriction, so only quest_reward_type_pools/
# quest_reward_expansion_pools need to be wide open (they already default
# to their full vocabulary, per QuestRewardTypePools/
# QuestRewardExpansionPools's own docstrings, so nothing needs widening
# there at all) and quest_reward_weight/check_density need to be turned up
# from WoWTestBase's fast-test zero. Every possession-triggered family's
# own pools are deliberately left at WoWTestBase's fast-test-default empty
# sets (unrelated to this fix, and leaving them empty keeps this class
# fast). check_density=100 + quest_reward_weight=100 makes
# density.predict_sample_size deterministic (ceil(candidates * 1 * 1) ==
# every candidate that survived the scope filter), so the sampled set can
# be compared for EXACT equality against the real zone-17 roster, not just
# "some subset of it".
_ZONE_LEVELER_QUEST_REWARD_OPTIONS = {
    "game_mode": "zone_leveler",
    "zone_leveler_starting_zone": "barrens",
    "zone_leveler_goals": {"reach_zone_level_cap"},
    "quest_reward_weight": 100,
    "check_density": 100,
}


class TestZoneLevelerQuestRewardsRestrictedToSelectedZoneUnderZoneOnly(WoWTestBase):
    """M4.11.1 Task 12 post-hoc fix round: under zone_only, a Barrens slot's
    Quest Rewards location pool contains ONLY quests whose real zone_id is
    17 (The Barrens) -- the exact same real roster
    zone_leveler_content_data.ZONES["barrens"].quest_reward_location_names
    already computes and clear_all_zone_quests (goals.py) already depends
    on, confirming this fix's filter and that pre-existing goal machinery
    agree on what "Barrens' own quest rewards" means."""
    options = {**_ZONE_LEVELER_QUEST_REWARD_OPTIONS, "zone_leveler_content_scope": "zone_only"}

    def test_quest_reward_pool_exactly_matches_barrens_zone_id_roster(self) -> None:
        # ALWAYS_PRESENT quest_reward rows (the 19 migrated Northshire/
        # Goldshire starting quests) are excluded from this comparison --
        # they bypass ALL scoping (tag pools, content_scope, AND this new
        # zone filter) unconditionally, via create_optional_category_locations'
        # own separate always_present loop, which runs BEFORE
        # _zone_leveler_scope_matches is ever consulted. That bypass is
        # pre-existing, documented (QuestRewardWeight's own docstring), and
        # entirely out of this fix's scope -- confirmed empirically: every
        # row this filter actually lets through DOES match Barrens' own
        # zone_id, and ALWAYS_PRESENT rows are the only ones that don't.
        expected = set(zone_leveler_content_data.ZONES["barrens"].quest_reward_location_names)
        self.assertGreater(len(expected), 0)
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = (
            names & set(quest_rewards_content_data.LOCATIONS)
        ) - quest_rewards_content_data.ALWAYS_PRESENT
        self.assertEqual(sampled_quest_rewards, expected)
        for name in sampled_quest_rewards:
            self.assertEqual(quest_rewards_content_data.TRIGGERS[name]["zone_id"], 17)

    def test_quest_with_unresolvable_zone_sentinel_never_appears(self) -> None:
        # Same ALWAYS_PRESENT exclusion as above -- a handful of the 19
        # always-present rows legitimately carry zone_id 0 themselves (they
        # bypass this filter entirely, pre-existing/out of scope), so this
        # only asserts the NEW filter's own behavior: no non-always-present
        # zero-zone row is ever let through by
        # _zone_leveler_quest_reward_zone_matches.
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = (
            names & set(quest_rewards_content_data.LOCATIONS)
        ) - quest_rewards_content_data.ALWAYS_PRESENT
        zero_zone_names = {
            name for name, trigger in quest_rewards_content_data.TRIGGERS.items()
            if trigger.get("zone_id") == 0
        }
        self.assertGreater(len(zero_zone_names), 0)
        self.assertEqual(len(sampled_quest_rewards & zero_zone_names), 0)


class TestZoneLevelerQuestRewardsRestrictedToSelectedZoneUnderWholeGameScaled(WoWTestBase):
    """M4.11.1 Task 12 post-hoc fix round: the same restriction as
    TestZoneLevelerQuestRewardsRestrictedToSelectedZoneUnderZoneOnly, but
    under whole_game_scaled -- confirms Quest Rewards' zone restriction is
    genuinely unconditional on content_scope, unlike the 5
    possession-triggered families the toggle actually widens/narrows."""
    options = {**_ZONE_LEVELER_QUEST_REWARD_OPTIONS, "zone_leveler_content_scope": "whole_game_scaled"}

    def test_quest_reward_pool_exactly_matches_barrens_zone_id_roster(self) -> None:
        # ALWAYS_PRESENT quest_reward rows (the 19 migrated Northshire/
        # Goldshire starting quests) are excluded from this comparison --
        # they bypass ALL scoping (tag pools, content_scope, AND this new
        # zone filter) unconditionally, via create_optional_category_locations'
        # own separate always_present loop, which runs BEFORE
        # _zone_leveler_scope_matches is ever consulted. That bypass is
        # pre-existing, documented (QuestRewardWeight's own docstring), and
        # entirely out of this fix's scope -- confirmed empirically: every
        # row this filter actually lets through DOES match Barrens' own
        # zone_id, and ALWAYS_PRESENT rows are the only ones that don't.
        expected = set(zone_leveler_content_data.ZONES["barrens"].quest_reward_location_names)
        self.assertGreater(len(expected), 0)
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = (
            names & set(quest_rewards_content_data.LOCATIONS)
        ) - quest_rewards_content_data.ALWAYS_PRESENT
        self.assertEqual(sampled_quest_rewards, expected)
        for name in sampled_quest_rewards:
            self.assertEqual(quest_rewards_content_data.TRIGGERS[name]["zone_id"], 17)

    def test_quest_with_unresolvable_zone_sentinel_never_appears(self) -> None:
        # Same ALWAYS_PRESENT exclusion as above -- a handful of the 19
        # always-present rows legitimately carry zone_id 0 themselves (they
        # bypass this filter entirely, pre-existing/out of scope), so this
        # only asserts the NEW filter's own behavior: no non-always-present
        # zero-zone row is ever let through by
        # _zone_leveler_quest_reward_zone_matches.
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = (
            names & set(quest_rewards_content_data.LOCATIONS)
        ) - quest_rewards_content_data.ALWAYS_PRESENT
        zero_zone_names = {
            name for name, trigger in quest_rewards_content_data.TRIGGERS.items()
            if trigger.get("zone_id") == 0
        }
        self.assertGreater(len(zero_zone_names), 0)
        self.assertEqual(len(sampled_quest_rewards & zero_zone_names), 0)


class TestZoneLevelerQuestRewardRestrictionDoesNotAffectOtherGameModes(WoWTestBase):
    """M4.11.1 Task 12 post-hoc fix round: the new Quest Rewards zone
    restriction is zone_leveler-specific -- game_mode defaults to sprint
    (option_sprint) here, so it must NOT apply: the full, unrestricted
    ~9,208-row Quest Rewards pool must remain available, spanning every
    real zone_id including 0 (unresolvable) and every real zone other than
    Barrens' 17, exactly like before this fix round. check_density=100 +
    quest_reward_weight=100 again makes the sample deterministic (every
    row is a candidate, since game_mode != "zone_leveler" means
    _zone_leveler_scope_matches is never even consulted -- see its call
    site in create_optional_category_locations), so this compares against
    the real, full LOCATIONS roster for exact equality."""
    options = {"quest_reward_weight": 100, "check_density": 100}

    def test_full_unrestricted_quest_reward_pool_is_sampled(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = names & set(quest_rewards_content_data.LOCATIONS)
        self.assertEqual(sampled_quest_rewards, set(quest_rewards_content_data.LOCATIONS))

    def test_rows_outside_barrens_zone_id_are_present(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = names & set(quest_rewards_content_data.LOCATIONS)
        non_barrens = {
            name for name in sampled_quest_rewards
            if quest_rewards_content_data.TRIGGERS[name].get("zone_id") != 17
        }
        self.assertGreater(len(non_barrens), 0)


class TestZoneLevelerAlwaysPresentQuestRewardsRestrictedToZone(WoWTestBase):
    """M4.11.2 Task 2: Quest Rewards' 19 ALWAYS_PRESENT starting-quest rows
    (the migrated Northshire/Goldshire quests) must be zone-filtered under
    zone_leveler, just like every other quest_rewards row. This test verifies
    that out-of-zone always_present rows are excluded."""
    options = {
        **_ZONE_LEVELER_QUEST_REWARD_OPTIONS,
        "zone_leveler_content_scope": "zone_only"
    }

    def test_out_of_zone_always_present_row_excluded(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Quest: Skirmish at Echo Ridge Reward (#21)", location_names)


class TestNonZoneLevelerModeStillIncludesAllAlwaysPresentRows(WoWTestBase):
    """M4.11.2 Task 2: The zone filtering fix must not affect other game modes --
    non-zone_leveler modes must still include all ALWAYS_PRESENT rows regardless
    of zone."""
    options = {"game_mode": "sprint"}

    def test_always_present_row_still_included(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Quest: Skirmish at Echo Ridge Reward (#21)", location_names)


class TestZoneLevelerQuestRewardsIncludeHubZoneWhenToggleOn(WoWTestBase):
    options = {
        **_ZONE_LEVELER_QUEST_REWARD_OPTIONS,
        "zone_leveler_allow_hub_zone": True,
    }

    def test_durotar_or_orgrimmar_quest_included(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Quest: Ripple Delivery Reward (#81)", location_names)


class TestZoneLevelerQuestRewardsExcludeHubZoneWhenToggleOff(WoWTestBase):
    options = {
        **_ZONE_LEVELER_QUEST_REWARD_OPTIONS,
        "zone_leveler_allow_hub_zone": False,
    }

    def test_durotar_or_orgrimmar_quest_excluded(self) -> None:
        # Matches the physical zone-lock's own real enforcement -- if the
        # player can't walk there, the check shouldn't exist either.
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Quest: Ripple Delivery Reward (#81)", location_names)


class TestZoneLevelerRepsanityVanillaOnly(WoWTestBase):
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
        "repsanity_expansion_pools": set(options.RepsanityExpansionPools.default),
        "repsanity_rank_tier_pools": set(options.RepsanityRankTierPools.default),
    }

    def test_vanilla_faction_included(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Reputation: Booty Bay (Friendly)", location_names)

    def test_non_vanilla_faction_excluded(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Reputation: Silvermoon City (Friendly)", location_names)


class TestZoneLevelerRepsanityUnaffectedByContentScope(WoWTestBase):
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
        "zone_leveler_content_scope": "whole_game_scaled",
        "repsanity_expansion_pools": set(options.RepsanityExpansionPools.default),
        "repsanity_rank_tier_pools": set(options.RepsanityRankTierPools.default),
    }

    def test_non_vanilla_faction_still_excluded_under_whole_game_scaled(self) -> None:
        # Confirms the vanilla-only restriction is NOT the possession-triggered
        # zone_only/whole_game_scaled toggle -- it applies identically either way.
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Reputation: Silvermoon City (Friendly)", location_names)
