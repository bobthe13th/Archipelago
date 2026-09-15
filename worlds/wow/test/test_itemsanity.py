# Archipelago/worlds/wow/test/test_itemsanity.py
from .bases import WoWTestBase
from .. import itemsanity_content_data


class TestItemsanityRealGeneration(WoWTestBase):
    """itemsanity_class_pools/itemsanity_quality_pools/itemsanity_expansion_pools
    default to empty (bases.py's test-speed default, same M4.10.6 fix
    craftsanity/containersanity/etc. already need) -- must be set to
    non-empty values here so this class's real-generation assertions
    aren't vacuously false. Itemsanity is by far the largest family
    (46,096 rows as of this checkout's own regeneration -- see
    extract_itemsanity.py; no longer a fixed number, it can shift again
    the next time the family is regenerated), so narrowing to a single class
    ("misc") and a single quality ("normal") -- while leaving
    itemsanity_expansion_pools at its full vocabulary -- keeps this test
    fast, same narrowing convention as
    TestContainersanityRealGenerationWotlkOnly (containersanity_expansion_pools
    narrowed to just "wotlk") and TestCraftsanityRealGeneration (profession/
    class pools narrowed). Hearthstone (#6948) is tagged class=misc,
    quality=normal, expansion=vanilla in itemsanity_content_data.py, so it
    is a real, always-selected anchor under this narrowing -- it has been
    the recurring spot-check anchor throughout this milestone's execution.
    """

    options = {
        "game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0,
        "itemsanity_class_pools": {"misc"},
        "itemsanity_quality_pools": {"normal"},
        "itemsanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
    }

    def test_real_seed_includes_hearthstone_location(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Itemsanity: Hearthstone (#6948)", location_names)

    def test_only_misc_normal_tagged_rows_are_present(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_itemsanity = {n for n in location_names if n in itemsanity_content_data.LOCATIONS}
        self.assertTrue(len(sampled_itemsanity) > 0)
        self.assertLess(len(sampled_itemsanity), len(itemsanity_content_data.LOCATIONS))
        for name in sampled_itemsanity:
            tags = itemsanity_content_data.TAGS[name]
            self.assertIn("misc", tags["class"])
            self.assertIn("normal", tags["quality"])


class TestItemsanityDefaultExcludesDebugAndUnobtainableTiers(WoWTestBase):
    """I3 (final whole-branch review, M4.11.5.1): itemsanity_debug_item_inclusion
    left unset resolves to its own real default (exclude_all) -- confirms
    every location actually created under that default is genuinely
    tagged "normal" (untagged): neither the debug nor the unobtainable
    tier ever becomes a real, checkable location by default. Same
    misc/normal narrowing as TestItemsanityRealGeneration above (keeps
    this fast) -- verified live that misc+normal alone still contains
    516 real debug/unobtainable-tagged rows, so this default-exclusion
    assertion is a real, non-vacuous check, not just an empty-set
    tautology."""

    options = {
        "game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0,
        "itemsanity_class_pools": {"misc"},
        "itemsanity_quality_pools": {"normal"},
        "itemsanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
    }

    def test_no_created_location_has_a_debug_category_tag(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_itemsanity = {n for n in location_names if n in itemsanity_content_data.LOCATIONS}
        self.assertTrue(len(sampled_itemsanity) > 0)
        for name in sampled_itemsanity:
            self.assertNotIn("debug_category", itemsanity_content_data.TAGS[name])


class TestItemsanityIncludeAllOptionAddsDebugCategoryLocations(WoWTestBase):
    """I3 (final whole-branch review, M4.11.5.1): the inverse of
    TestItemsanityDefaultExcludesDebugAndUnobtainableTiers above --
    setting itemsanity_debug_item_inclusion to include_all is a genuine
    behavior change, not a no-op: at least one created location now
    carries a real debug_category tag (either "debug" or
    "unobtainable")."""

    options = {
        "game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0,
        "itemsanity_class_pools": {"misc"},
        "itemsanity_quality_pools": {"normal"},
        "itemsanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
        "itemsanity_debug_item_inclusion": "include_all",
    }

    def test_at_least_one_created_location_has_a_debug_category_tag(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        sampled_itemsanity = {n for n in location_names if n in itemsanity_content_data.LOCATIONS}
        self.assertTrue(any(
            "debug_category" in itemsanity_content_data.TAGS[name] for name in sampled_itemsanity
        ))


class TestItemsanityExcludedWithEmptyPools(WoWTestBase):
    """Inverse check -- with empty itemsanity pools (bases.py's test-speed
    default, restated explicitly here for clarity), zero itemsanity
    locations should be created. Mirrors craftsanity's
    TestCraftsanityExcludedWithEmptyPools."""

    options = {
        "game_mode": "sprint",
        "check_density": 100,
        "vendor_stock_weight": 0,
        "itemsanity_class_pools": set(),
        "itemsanity_quality_pools": set(),
        "itemsanity_expansion_pools": set(),
    }

    def test_itemsanity_produces_zero_locations_with_empty_pools(self) -> None:
        # With all pools empty, AND-across-dimensions logic ensures no
        # itemsanity items match.
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        itemsanity_locs = {name for name in location_names if name.startswith("Itemsanity:")}
        self.assertEqual(len(itemsanity_locs), 0)


class TestItemsanityContentDataRosterCleanliness(WoWTestBase):
    """Reads itemsanity_content_data.LOCATIONS directly -- no multiworld
    generation needed. Guards against the M1 whitespace bug and leftover
    junk-data name patterns found during the parallel M4.10.6 final-review
    regeneration; robust to that regeneration's exact final row count
    changing, since these assertions never depend on len(LOCATIONS)."""

    options = {"game_mode": "sprint", "check_density": 0, "vendor_stock_weight": 0}

    def test_no_location_name_has_a_double_space(self) -> None:
        for name in itemsanity_content_data.LOCATIONS:
            # M4.11.5.1: debug-tier rows are now real, kept, tagged
            # locations (opt-in-able via itemsanity_debug_item_inclusion), not
            # dropped -- their real, junky Blizzard-internal names are expected
            # to look like junk; this guard is about genuinely player-facing
            # ("normal") content only.
            if "debug" in itemsanity_content_data.TAGS[name].get("debug_category", frozenset()):
                continue
            self.assertNotIn("  ", name)

    def test_no_location_name_contains_junk_placeholder_text(self) -> None:
        junk_patterns = ("m4-7test", "zzdeprecated", "obsolete")
        for name in itemsanity_content_data.LOCATIONS:
            # M4.11.5.1: see test_no_location_name_has_a_double_space above.
            if "debug" in itemsanity_content_data.TAGS[name].get("debug_category", frozenset()):
                continue
            lowered = name.lower()
            for junk in junk_patterns:
                self.assertNotIn(junk, lowered)
