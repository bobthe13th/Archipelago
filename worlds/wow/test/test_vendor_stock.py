# Archipelago/worlds/wow/test/test_vendor_stock.py
import re
import unittest

from BaseClasses import Location

from .bases import WoWTestBase
from .. import vendor_stock_content_data


class TestVendorStockRowAlignment(unittest.TestCase):
    """items.py's create_optional_category_item_pool (M4.5 Task 3 fix) pairs
    a sampled location to its reward item by ROW INDEX, not by name --
    confirmed necessary because LOCATIONS/ITEMS use different name prefixes
    for the same row ("Vendor: X - Y (#N)" vs "Vendor Item: X - Y (#N)").
    That pairing is only correct if LOCATIONS and ITEMS are emitted in the
    same row order. Nothing else in this suite can observe an order
    mismatch -- length parity and fill would both still pass even if row 5's
    location paired with row 900's item -- so this test pins the ordering
    invariant directly by cross-checking the shared row-index suffix "(#N)"
    both names carry."""

    def test_locations_and_items_are_row_order_aligned_by_row_index(self) -> None:
        location_names = list(vendor_stock_content_data.LOCATIONS)
        item_names = list(vendor_stock_content_data.ITEMS)
        self.assertEqual(len(location_names), len(item_names))
        for index, (location_name, item_name) in enumerate(zip(location_names, item_names)):
            location_row_id = re.search(r"\(#(\d+)\)$", location_name).group(1)
            item_row_id = re.search(r"\(#(\d+)\)$", item_name).group(1)
            self.assertEqual(
                location_row_id, item_row_id,
                f"row {index}: location {location_name!r} (#{location_row_id}) does not "
                f"align with item {item_name!r} (#{item_row_id})",
            )


class TestVendorStockHasNoRule(WoWTestBase):
    """Deliberate difference from Quest Rewards (M4.5 Task 6): Vendor
    Inventories has NO access rule at all -- per the plan's Repo-state
    finding #5, there's no reputation-gating data (no `conditions` table)
    and no real region/zone graph in this checkout to attach an
    Access(NPC_Location)-style rule to. rules.py is untouched by this task,
    so every vendor_stock location must carry AP's own class default access
    rule (Location.access_rule), never a real one. The single assertion
    below (no access rule) is a general invariant that holds regardless of
    HOW MANY vendor_stock rows get sampled -- unlike some quest_rewards
    tests, it doesn't depend on any specific named location -- so
    vendor_stock_weight: 10 (M4.8.0) caps the sample to ~10% of the real
    ~37,750-row table rather than VendorStockWeight's own real-seed default
    of 100 (literally every row), which made this test pathologically slow
    (confirmed empirically) without strengthening the assertion at all.
    quest_reward_weight: 0 -- this class has nothing to do with
    quest_rewards; left uncapped it would ALSO default to 100 via
    check_density: 100, silently filling the full ~9,220-row table too."""

    options = {"game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 10, "quest_reward_weight": 0}

    def test_all_vendor_stock_locations_have_no_access_rule(self) -> None:
        vendor_locations = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name in vendor_stock_content_data.LOCATIONS
        ]
        self.assertTrue(len(vendor_locations) > 0)
        for loc in vendor_locations:
            self.assertIs(loc.access_rule, Location.access_rule)


class TestVendorStockAvailableOutsideSprint(WoWTestBase):
    """Task 3's OptionalCategory registry -- and VendorStockWeight's own
    docstring (M4.8.0, replacing the retired IncludeVendorStock toggle) --
    both claim Vendor Inventories works in EVERY game mode, not just
    Sprint. Every other test in this file only ever exercises Sprint,
    so nothing prior to this class actually ran the family under a different
    mode's own sampler running side by side. Key Hunt is the sharpest case:
    it's the one other mode whose own create_rares_locations also samples
    through density and sets world.key_hunt_sampled_rare_count as a side
    effect, so this is the one place the new registry and the pre-existing
    sampler actually run side by side. WoWTestBase's default test_fill/
    test_all_state_can_reach_everything already cover full-generation
    reachability for this option combination; this class adds the parity/
    presence checks those defaults don't."""

    # vendor_stock_weight: 10 (M4.8.0) -- neither test in this class depends
    # on a specific named location, just "at least one exists" / a general
    # parity invariant, so this doesn't need VendorStockWeight's own
    # real-seed default of 100 (the full ~37,750-row table).
    # quest_reward_weight: 0 -- this class has nothing to do with
    # quest_rewards at all, and without capping it explicitly it would ALSO
    # default to 100 via check_density: 100, silently filling the full
    # ~9,220-row table for no test-relevant reason.
    options = {
        "game_mode": "key_hunt",
        "check_density": 100,
        "vendor_stock_weight": 10,
        "quest_reward_weight": 0,
    }

    def test_vendor_stock_locations_exist_in_key_hunt_mode(self) -> None:
        vendor_stock_locations = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name in vendor_stock_content_data.LOCATIONS
        ]
        self.assertTrue(len(vendor_stock_locations) > 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestVendorStockItemPoolMatchesLocationCount(WoWTestBase):
    """Same invariant as TestVendorStockAvailableOutsideSprint's version of
    this test, checked here under Sprint mode (the default-owning mode for
    every other family in this file) with Vendor Inventories sampled in --
    this is exactly the invariant items.py's row-index item-pooling fix (Task 3)
    exists to protect. vendor_stock_weight: 10 (M4.8.0) -- see
    TestVendorStockHasNoRule's own comment above; this test's assertion is
    also a general invariant, not dependent on a specific location.
    quest_reward_weight: 0 for the same reason as TestVendorStockHasNoRule."""

    options = {"game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 10, "quest_reward_weight": 0}

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))
