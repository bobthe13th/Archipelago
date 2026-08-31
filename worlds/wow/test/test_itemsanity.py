# Archipelago/worlds/wow/test/test_itemsanity.py
from .bases import WoWTestBase
from .. import itemsanity_content_data


class TestItemsanityRealGeneration(WoWTestBase):
    """itemsanity_class_pools/itemsanity_quality_pools/itemsanity_expansion_pools
    default to empty (bases.py's test-speed default, same M4.10.6 fix
    craftsanity/containersanity/etc. already need) -- must be set to
    non-empty values here so this class's real-generation assertions
    aren't vacuously false. Itemsanity is by far the largest family
    (39,355 rows as of M4.10.6's own generation, though a parallel review
    fix is expected to shrink that count), so narrowing to a single class
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
            self.assertNotIn("  ", name)

    def test_no_location_name_contains_junk_placeholder_text(self) -> None:
        junk_patterns = ("m4-7test", "zzdeprecated", "obsolete")
        for name in itemsanity_content_data.LOCATIONS:
            lowered = name.lower()
            for junk in junk_patterns:
                self.assertNotIn(junk, lowered)
