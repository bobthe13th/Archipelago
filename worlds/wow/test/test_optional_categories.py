# Archipelago/worlds/wow/test/test_optional_categories.py
import unittest

from .bases import WoWTestBase
from .. import WoWWorld
from .. import (
    craftsanity_content_data, enemysanity_content_data, itemsanity_content_data, options,
    quest_rewards_content_data, recipes_content_data, repsanity_content_data, trainer_spells_content_data,
    zone_leveler_content_data,
)
from ..locations import (
    _NO_PHYSICAL_LOCATION_CATEGORY_KEYS, _OPTIONAL_CATEGORIES, OptionalCategory,
    create_optional_category_locations, _location_matches_pools, _min_level_for_row, _zone_leveler_row_matches,
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


class TestMinLevelForRow(WoWTestBase):
    """M4.11.1 Task 12, renamed by M4.11.3.3 (_zone_leveler_possession_family_min_level
    -> _min_level_for_row): unit-level coverage of the min_level lookup
    helper itself, calling module data directly rather than paying for a
    full zone_leveler slot generation."""
    options = {}

    def test_itemsanity_row_carries_a_real_int_min_level(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "itemsanity")
        name = next(iter(itemsanity_content_data.LOCATIONS))
        min_level = _min_level_for_row(category, name)
        self.assertIsInstance(min_level, int)

    def test_trainer_spells_row_carries_a_real_int_min_level(self) -> None:
        # M4.11.3.3: _min_level_for_row is no longer actually CALLED for
        # trainer_spells by _zone_leveler_row_matches (the family left the
        # "no physical location" bucket -- see that function's own
        # docstring), but the helper itself is still generic/correct for
        # any category whose TRIGGERS carries a real min_level key, and
        # trainer_spells still does.
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "trainer_spells")
        name = next(iter(trainer_spells_content_data.LOCATIONS))
        min_level = _min_level_for_row(category, name)
        self.assertIsInstance(min_level, int)

    def test_recipes_row_carries_a_real_int_min_level(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "recipes")
        name = next(iter(recipes_content_data.LOCATIONS))
        min_level = _min_level_for_row(category, name)
        self.assertIsInstance(min_level, int)

    def test_craftsanity_has_no_real_min_level_data(self) -> None:
        # By design, not an oversight -- crafting requirements are
        # skill-tier-gated, not player-level-gated; see
        # _min_level_for_row's own docstring.
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "craftsanity")
        name = next(iter(craftsanity_content_data.LOCATIONS))
        self.assertIsNone(_min_level_for_row(category, name))

    def test_repsanity_has_no_real_min_level_data(self) -> None:
        # By design -- reputation ranks are not level-gated at all.
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "repsanity")
        name = next(iter(repsanity_content_data.LOCATIONS))
        self.assertIsNone(_min_level_for_row(category, name))


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
    """M4.11.1 Task 12, revised M4.11.3.3: zone_only excludes every
    no-physical-location family's rows entirely, regardless of tag-pool
    selection. Iterates locations._NO_PHYSICAL_LOCATION_CATEGORY_KEYS
    directly (Itemsanity/Recipes/Craftsanity) rather than the old,
    now-removed _POSSESSION_TRIGGERED_CATEGORY_KEYS -- Trainer Spells left
    that bucket this milestone (it now has a real area tag and is
    unconditionally zone-checked instead, see
    TestZoneLevelerTrainerSpellsIncludedUnderZoneOnlyNow below).
    zone_leveler_goals is narrowed to reach_zone_level_cap alone -- same
    reasoning test_basic.py's TestZoneLevelerCoreLoop/TestGoldenBoarStatues
    already document: the default goal set requires quest_reward pooling,
    which WoWTestBase zeroes for speed, making the game unbeatable unless a
    class also narrows the goal set."""
    options = {**_ZONE_LEVELER_BASE_OPTIONS, "zone_leveler_content_scope": "zone_only"}

    def test_zone_only_excludes_every_no_physical_location_family(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for key in _NO_PHYSICAL_LOCATION_CATEGORY_KEYS:
            category = next(c for c in _OPTIONAL_CATEGORIES if c.key == key)
            overlap = names & set(category.locations_module.LOCATIONS)
            self.assertEqual(len(overlap), 0, f"{key} rows leaked through zone_only")


class TestEveryZoneBoundOptionalCategoryHasRealAreaTagData(unittest.TestCase):
    """Final whole-branch review fix (Minor #10, M4.11.3 milestone final
    review): TestZoneLevelerContentScope above already pins that
    itemsanity/recipes/craftsanity (_NO_PHYSICAL_LOCATION_CATEGORY_KEYS) ARE
    excluded under zone_only -- this is the missing complement, pinning that
    every OTHER optional category genuinely carries real position-derived
    `area` tag data on at least one row, so _zone_leveler_row_matches's
    unconditional zone check has something real to match against. Without
    this, a future family added to _OPTIONAL_CATEGORIES with no real
    area/position data would be silently, 100% excluded under zone_leveler
    with a fully green test suite -- exactly the failure mode this whole
    milestone existed to fix in the first place. Repsanity is exempted: it
    has its own separate, deliberate non-area-tag handling
    (_zone_leveler_repsanity_matches in locations.py, an expansion-tag
    proxy), and never reaches _zone_leveler_row_matches's area-tag branch at
    all. A plain unittest.TestCase, not WoWTestBase -- this is a live-data
    invariant over the real, already-loaded content-data modules, no world
    generation needed."""

    def test_every_zone_bound_category_has_at_least_one_row_with_real_area_tags(self) -> None:
        exempt_keys = _NO_PHYSICAL_LOCATION_CATEGORY_KEYS | {"repsanity"}
        zone_bound_categories = [c for c in _OPTIONAL_CATEGORIES if c.key not in exempt_keys]
        # Guard against a vacuous pass (same discipline as
        # test_barrens_quest_names_are_all_real_zone_tagged_quest_rewards in
        # test_zone_leveler_content_data.py) -- without this, an empty list
        # here would make the loop below "pass" without checking anything.
        self.assertGreater(len(zone_bound_categories), 0)
        for category in zone_bound_categories:
            has_real_area_data = any(
                tags.get("area") for tags in category.locations_module.TAGS.values()
            )
            self.assertTrue(
                has_real_area_data,
                f"{category.key} carries no real 'area' tag data on any row -- "
                "it would be silently, 100% excluded under zone_leveler.",
            )


class TestZoneLevelerWholeGameScaledWidensTractableFamilies(WoWTestBase):
    """M4.11.1 Task 12, revised M4.11.3.3: whole_game_scaled widens the 2
    real tractable no-physical-location families (Itemsanity, Recipes) to
    rows whose own real min_level falls inside Barrens' level band
    (10-30, zone_leveler_content_data.ZONES["barrens"]), and leaves
    Craftsanity fully excluded -- same as zone_only -- since it carries no
    real min_level data to widen by. Repsanity is exercised separately
    (TestZoneLevelerRepsanity* below); it never reaches this min_level
    logic at all.

    Trainer Spells is deliberately NOT covered by this class anymore --
    M4.11.3.3 moved it out of the level-widening bucket entirely (it now
    has a real area tag and is unconditionally, unaffected-by-content_scope
    zone-checked instead -- covered by
    TestZoneLevelerTrainerSpellsIncludedUnderZoneOnlyNow/
    TestZoneLevelerTrainerSpellRowMatches below), so content_scope no
    longer has any effect on it at all."""
    options = {**_ZONE_LEVELER_BASE_OPTIONS, "zone_leveler_content_scope": "whole_game_scaled"}

    def test_itemsanity_widens_to_rows_inside_barrens_level_band(self) -> None:
        band = zone_leveler_content_data.ZONES["barrens"]
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        widened = names & set(itemsanity_content_data.LOCATIONS)
        self.assertGreater(len(widened), 0)
        for name in widened:
            min_level = itemsanity_content_data.TRIGGERS[name]["min_level"]
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
        # (see _min_level_for_row's own docstring) -- whole_game_scaled
        # behaves identically to zone_only for this family,
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


class TestZoneLevelerTrainerSpellsContributeAtEitherContentScope(WoWTestBase):
    """M4.11.3.3 supersedes M4.11.2's TestZoneLevelerTrainerSpellZoneMatches/
    TestZoneLevelerTrainerSpellsAtDefaultHubZone: Trainer Spells now has a
    real area tag (M4.11.3.1 Task 4) and is unconditionally zone-checked by
    _zone_leveler_row_matches, so it contributes the SAME rows under
    zone_only and whole_game_scaled alike -- content_scope no longer
    affects this family at all (the old min_level-widening axis it used to
    ALSO need, on top of the zone check, is gone along with
    zone_leveler_allow_hub_zone; see _zone_leveler_row_matches's own
    docstring). Frost Nova (#122) carries a direct "barrens" area tag
    (confirmed via direct TAGS inspection); Teleport: Stormwind (#3561)
    resolves only to Stormwind/Elwynn Forest -- never Barrens -- so it
    stays excluded regardless of content_scope."""
    options = {**_ZONE_LEVELER_BASE_OPTIONS, "zone_leveler_content_scope": "whole_game_scaled"}

    def test_known_barrens_taught_spell_included(self) -> None:
        name = "Trainer Spell: Frost Nova (#122)"
        self.assertIn("barrens", trainer_spells_content_data.TAGS[name]["area"])
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn(name, location_names)

    def test_spell_never_taught_in_barrens_excluded(self) -> None:
        name = "Trainer Spell: Teleport: Stormwind (#3561)"
        self.assertNotIn("barrens", trainer_spells_content_data.TAGS[name]["area"])
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn(name, location_names)


class TestZoneLevelerTrainerSpellRowMatches(WoWTestBase):
    """M4.11.3.3: unit-level coverage of _zone_leveler_row_matches itself
    for the trainer_spells category, calling it directly against real
    trainer_spells_content_data.TAGS rows (same fake-world
    types.SimpleNamespace pattern TestZoneLevelerRowMatchesQuestRewards
    below uses) rather than paying for a full zone_leveler slot generation.
    Supersedes M4.11.2's TestZoneLevelerTrainerSpellZoneMatchesUnit -- the
    hub-zone toggle it exercised no longer has any effect (dropped by
    M4.11.3.3, see _zone_leveler_row_matches's own docstring), so this
    class only exercises the one real axis that remains: a row's own
    tags["area"] intersecting the selected zone's own real area_tags."""
    options = {}

    @staticmethod
    def _fake_world(zone_key: str = "barrens"):
        import types

        return types.SimpleNamespace(options=types.SimpleNamespace(
            zone_leveler_starting_zone=types.SimpleNamespace(current_key=zone_key),
            zone_leveler_content_scope="zone_only",
        ))

    def test_frost_nova_matches(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "trainer_spells")
        name = "Trainer Spell: Frost Nova (#122)"
        self.assertIn("barrens", trainer_spells_content_data.TAGS[name]["area"])
        self.assertTrue(_zone_leveler_row_matches(self._fake_world(), category, name))

    def test_summon_warhorse_does_not_match(self) -> None:
        # Summon Warhorse (#34768): taught only by trainers whose real
        # positions resolve to Silvermoon City/Silverpine Forest/Tirisfal
        # Glades/Western Plaguelands/Undercity/Alterac Mountains/Eversong
        # Woods/Orgrimmar (confirmed via direct TAGS inspection against
        # this checkout's real regenerated trainer_spells_content_data.TAGS)
        # -- never Barrens, so it's excluded regardless of content_scope
        # (the old hub-zone-toggle-only reachability path this row used to
        # need is gone).
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "trainer_spells")
        name = "Trainer Spell: Summon Warhorse (#34768)"
        area_tags = set(trainer_spells_content_data.TAGS[name]["area"])
        self.assertIn("orgrimmar", area_tags)
        self.assertNotIn("barrens", area_tags)
        self.assertFalse(_zone_leveler_row_matches(self._fake_world(), category, name))

    def test_teleport_stormwind_never_matches_barrens(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "trainer_spells")
        name = "Trainer Spell: Teleport: Stormwind (#3561)"
        self.assertNotIn("barrens", trainer_spells_content_data.TAGS[name]["area"])
        self.assertFalse(_zone_leveler_row_matches(self._fake_world(), category, name))


class TestZoneLevelerRowMatchesQuestRewards(WoWTestBase):
    """M4.11.1 Task 12 post-hoc fix round, revised M4.11.3.3: unit-level
    coverage of _zone_leveler_row_matches for the quest_rewards category,
    calling it directly against real quest_rewards_content_data.TAGS rows
    rather than paying for a full zone_leveler slot generation. Supersedes
    the old, now-removed _zone_leveler_quest_reward_zone_matches's own unit
    tests -- same real rows, same real assertions, just calling the new
    generic function with an explicit quest_rewards OptionalCategory.

    The confirmed bug this fix originally closed (M4.11.1 Task 12): Quest
    Rewards is a real, physically zone-bound family (a real quest-giver
    NPC), but the OLD code let it fall through a generic "always True"
    branch, so a Barrens slot could sample a quest whose quest-giver stands
    in a totally different, unreachable zone. These tests confirm the fix
    still holds under the new generic function: only a row whose own real
    tags["area"] intersects the selected zone's own real area_tags
    matches, and this holds regardless of zone_leveler_content_scope
    (Quest Rewards' restriction is not gated by that toggle at all -- it's
    outside _NO_PHYSICAL_LOCATION_CATEGORY_KEYS).

    test_row_with_unresolvable_zone_sentinel_is_excluded also pins
    M4.11.3.3's own real regression fix (confirmed via an actual failing
    test run, not assumed): an unresolvable-area quest_rewards row must
    stay excluded under whole_game_scaled too, not fall through to the
    no-physical-location level-widening branch the way an itemsanity/
    recipes/craftsanity row legitimately would -- see
    _zone_leveler_row_matches's own docstring for why category.key
    membership, not row-level area-tag truthiness, is what decides that."""
    options = {}

    @staticmethod
    def _fake_world(content_scope: str, zone_key: str = "barrens"):
        import types

        return types.SimpleNamespace(options=types.SimpleNamespace(
            zone_leveler_content_scope=content_scope,
            zone_leveler_starting_zone=types.SimpleNamespace(current_key=zone_key),
        ))

    @staticmethod
    def _category():
        return next(c for c in _OPTIONAL_CATEGORIES if c.key == "quest_rewards")

    def test_row_in_selected_zone_matches_under_zone_only(self) -> None:
        # "Quest: Chen's Empty Keg Reward (#819)" -- real area tag
        # "barrens" (The Barrens), confirmed by direct TAGS inspection.
        name = "Quest: Chen's Empty Keg Reward (#819)"
        self.assertEqual(quest_rewards_content_data.TAGS[name].get("area"), frozenset({"barrens"}))
        world = self._fake_world("zone_only")
        self.assertTrue(_zone_leveler_row_matches(world, self._category(), name))

    def test_row_in_selected_zone_matches_under_whole_game_scaled(self) -> None:
        # Same row, but under whole_game_scaled -- must still match; the
        # content_scope toggle never affects Quest Rewards at all.
        name = "Quest: Chen's Empty Keg Reward (#819)"
        world = self._fake_world("whole_game_scaled")
        self.assertTrue(_zone_leveler_row_matches(world, self._category(), name))

    def test_row_in_a_different_real_zone_is_excluded(self) -> None:
        # "Quest: Kanrethad's Quest Reward (#1)" -- real area tag
        # "designer_island" (a real, resolved zone, just not Barrens),
        # confirmed by direct TAGS inspection. Must be excluded under BOTH
        # content_scope values -- this is not the no-physical-location
        # widening path.
        name = "Quest: Kanrethad's Quest Reward (#1)"
        self.assertEqual(quest_rewards_content_data.TAGS[name].get("area"), frozenset({"designer_island"}))
        self.assertFalse(_zone_leveler_row_matches(self._fake_world("zone_only"), self._category(), name))
        self.assertFalse(_zone_leveler_row_matches(self._fake_world("whole_game_scaled"), self._category(), name))

    def test_row_with_unresolvable_zone_sentinel_is_excluded(self) -> None:
        # "Quest: A Lesson to Learn Reward (#26)" -- the `area` key is
        # OMITTED from its tags block entirely (its real QuestSortID never
        # resolves to a real zone -- see extract_quest_rewards.py's
        # _resolve_zone_id), this data's own "unresolvable, real zone
        # unknown" sentinel. The safe default for a physically zone-locked
        # game mode is exclusion, not inclusion, since we genuinely don't
        # know this row's real zone -- NOT the no-physical-location
        # level-widening treatment (this row has a real, if unresolved,
        # physical location; it just isn't itemsanity/recipes/craftsanity).
        name = "Quest: A Lesson to Learn Reward (#26)"
        self.assertNotIn("area", quest_rewards_content_data.TAGS[name])
        self.assertFalse(_zone_leveler_row_matches(self._fake_world("zone_only"), self._category(), name))
        self.assertFalse(_zone_leveler_row_matches(self._fake_world("whole_game_scaled"), self._category(), name))


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
        # _zone_leveler_row_matches is ever consulted. That bypass is
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
            self.assertIn("barrens", quest_rewards_content_data.TAGS[name].get("area", frozenset()))

    def test_quest_with_unresolvable_zone_sentinel_never_appears(self) -> None:
        # Same ALWAYS_PRESENT exclusion as above -- a handful of the 19
        # always-present rows legitimately carry zone_id 0 themselves (they
        # bypass this filter entirely, pre-existing/out of scope), so this
        # only asserts the NEW filter's own behavior: no non-always-present
        # zero-zone row is ever let through by
        # _zone_leveler_row_matches.
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = (
            names & set(quest_rewards_content_data.LOCATIONS)
        ) - quest_rewards_content_data.ALWAYS_PRESENT
        zero_zone_names = {
            name for name, tags in quest_rewards_content_data.TAGS.items()
            if not tags.get("area")
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
        # _zone_leveler_row_matches is ever consulted. That bypass is
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
            self.assertIn("barrens", quest_rewards_content_data.TAGS[name].get("area", frozenset()))

    def test_quest_with_unresolvable_zone_sentinel_never_appears(self) -> None:
        # Same ALWAYS_PRESENT exclusion as above -- a handful of the 19
        # always-present rows legitimately carry zone_id 0 themselves (they
        # bypass this filter entirely, pre-existing/out of scope), so this
        # only asserts the NEW filter's own behavior: no non-always-present
        # zero-zone row is ever let through by
        # _zone_leveler_row_matches.
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_quest_rewards = (
            names & set(quest_rewards_content_data.LOCATIONS)
        ) - quest_rewards_content_data.ALWAYS_PRESENT
        zero_zone_names = {
            name for name, tags in quest_rewards_content_data.TAGS.items()
            if not tags.get("area")
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
    _zone_leveler_row_matches is never even consulted -- see its call
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
            if "barrens" not in quest_rewards_content_data.TAGS[name].get("area", frozenset())
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


class TestZoneLevelerOrgrimmarQuestExcludedNowThatHubZoneWideningIsGone(WoWTestBase):
    """Real, disclosed behavior change (M4.11.3.3): M4.11.2's own
    TestZoneLevelerQuestRewardsIncludeHubZoneWhenToggleOn/
    TestZoneLevelerQuestRewardsExcludeHubZoneWhenToggleOff pinned
    zone_leveler_allow_hub_zone actually widening Quest Rewards' in-bounds
    zone set to include Durotar/Orgrimmar. Task 1's flattened
    ZoneLevelerZoneData no longer carries any hub-zone data at all
    (allowed_hub_zone_ids was REMOVED, not renamed -- area_tags is a fixed,
    real per-zone constant, frozenset({"barrens"}) for Barrens), and the
    new collapsed _zone_leveler_row_matches (M4.11.3.3) never reads any
    hub-zone toggle at all -- confirmed via direct source inspection, not
    assumed.

    Final whole-branch review fix (Minor #9, M4.11.3 milestone final
    review): this class used to pass zone_leveler_allow_hub_zone=True in its
    own options dict and was named/documented as proving the toggle no
    longer widens anything -- but Task 3 of M4.11.3.3 deleted the
    ZoneLevelerAllowHubZone option from options.py entirely, so that key was
    silently dropped by Generate.py's world_setup (an unrecognized option
    key is a warning, not an error) and this class was never actually
    exercising a toggle-on path at all, just the plain default path with an
    inert dict entry. Renamed and rewritten to describe what it actually
    verifies now that there is no toggle to test: "Quest: Ripple Delivery
    Reward (#81)" (real area tag frozenset({"orgrimmar"}), confirmed via
    direct TAGS inspection) is excluded under the default zone_only content
    scope, because Barrens' own area_tags never include "orgrimmar" -- the
    same real row M4.11.2's own tests used to pin the OLD widening behavior
    now demonstrates the mechanism's complete removal instead."""
    options = _ZONE_LEVELER_QUEST_REWARD_OPTIONS

    def test_orgrimmar_only_quest_excluded_under_default_zone_only(self) -> None:
        name = "Quest: Ripple Delivery Reward (#81)"
        self.assertEqual(quest_rewards_content_data.TAGS[name].get("area"), frozenset({"orgrimmar"}))
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn(name, location_names)


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


class TestZoneLevelerTrainerSpellsIncludedUnderZoneOnlyNow(WoWTestBase):
    # Real, deliberate behavior change (M4.11.3.3): Trainer Spells is now
    # a physically zone-bound family (real area tags, M4.11.3.1), so its
    # zone check is unconditional -- like Quest Rewards -- not gated by
    # zone_leveler_content_scope. Previously (M4.11.2) this family was
    # FULLY EXCLUDED under zone_only; it is not anymore.
    #
    # zone_leveler_goals narrowed to reach_zone_level_cap alone -- same
    # reasoning _ZONE_LEVELER_BASE_OPTIONS above documents (the default
    # goal set's instance_clears goal would otherwise build its own
    # "Instance Unlock: <name>" item-name set from EVERY key in
    # zone_data.instance_keys, including dire_maul/maraudon/onyxia_s_lair --
    # real, verified-correct instances (Task 1's own review) that were
    # never curated with a core_loop.yaml Instance Unlock item/location at
    # all, an out-of-scope pre-existing gap this test isn't about).
    #
    # Final whole-branch review fix (Minor #9, M4.11.3 milestone final
    # review): dropped "zone_leveler_allow_hub_zone": True -- that option was
    # deleted from options.py by Task 3 of M4.11.3.3, so it was silently
    # dropped by Generate.py's world_setup (an unrecognized option key is a
    # warning, not an error) and did nothing real here either.
    options = {"game_mode": "zone_leveler", "zone_leveler_starting_zone": "barrens",
               "zone_leveler_goals": {"reach_zone_level_cap"},
               "trainer_spell_class_pools": set(options.TrainerSpellClassPools.default),
               "trainer_spell_expansion_pools": set(options.TrainerSpellExpansionPools.default)}
    # zone_leveler_content_scope deliberately left at its default (zone_only)

    def test_a_horde_hub_taught_spell_is_now_included_under_zone_only(self) -> None:
        # Real, confirmed (direct TAGS inspection): Frost Nova's own
        # tags["area"] includes "barrens" directly (the fixed
        # resolve_area_tags_for_positions mechanism, M4.11.3.1 Task 4), so
        # it matches Barrens' own zone_data.area_tags unconditionally.
        name = "Trainer Spell: Frost Nova (#122)"
        self.assertIn("barrens", trainer_spells_content_data.TAGS[name]["area"])
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Trainer Spell: Frost Nova (#122)", location_names)


class TestZoneLevelerVendorStockContainersanityGathersanityEnemysanityNowFiltered(WoWTestBase):
    # Real payoff of this whole milestone: these 4 families had ZERO zone
    # restriction before M4.11.3 (the defect M4.11.1's own close-out
    # diagnosed but didn't fix). Enemysanity is exercised directly here
    # (its own type_pools/expansion_pools widened from WoWTestBase's
    # fast-test-default empty sets -- otherwise every row, in OR out of
    # Barrens, would be tag-pool-excluded regardless of this fix, making
    # any assertion here vacuous); Vendor Stock/Containersanity/
    # Gathersanity share the exact same TAGS['area'] mechanism
    # (_zone_leveler_row_matches reads category.locations_module.TAGS
    # uniformly for every category), so this one family's real,
    # regenerated-data coverage stands in for all 4.
    #
    # "Enemy: Brother Anton (#1182)" / "Enemy: Kobold Vermin (#6)": real
    # rows confirmed via direct TAGS inspection against this checkout's own
    # regenerated enemysanity_content_data.py (M4.11.3.2) --
    # Brother Anton's real area tags are frozenset({"desolace",
    # "stonetalon_mountains", "barrens"}) (includes Barrens), Kobold
    # Vermin's are frozenset({"elwynn_forest"}) (a genuinely
    # all-outside-Barrens spawn -- a single Elwynn Forest kobold, not a
    # Barrens-adjacent species like Ghostpaw Runner).
    options = {
        "game_mode": "zone_leveler", "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
        "enemysanity_type_pools": set(options.EnemysanityTypePools.default),
        "enemysanity_expansion_pools": set(options.EnemysanityExpansionPools.default),
    }

    def test_a_known_out_of_zone_enemysanity_location_is_excluded(self) -> None:
        name = "Enemy: Kobold Vermin (#6)"
        self.assertEqual(enemysanity_content_data.TAGS[name]["area"], frozenset({"elwynn_forest"}))
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn(name, location_names)

    def test_a_known_barrens_enemysanity_location_is_included(self) -> None:
        name = "Enemy: Brother Anton (#1182)"
        self.assertIn("barrens", enemysanity_content_data.TAGS[name]["area"])
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn(name, location_names)
