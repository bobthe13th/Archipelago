import unittest
from types import SimpleNamespace

from .. import mutation_claimed_rows
from .. import locations as locations_module


class _FakeLocation:
    def __init__(self, name):
        self.name = name


class _FakeQuestFamily:
    TRIGGERS = {
        "Quest: Fake Reward (#1)": {"kind": "quest_reward", "quest_id": 1, "column_index": 0},
    }


class _FakeVendorFamily:
    TRIGGERS = {
        "Vendor: Fake NPC - Fake Item (#1)": {"kind": "vendor_purchase", "npc_entry": 54, "item_slot": 0},
    }


class _FakeZonePoolFamily:
    # zone_pool_credit rows have no backing DB row at all -- must never
    # appear in claimed_rows' output (mirrors slot_data.py's own
    # _AP_ITEM_DISPLAY_TRIGGER_KINDS exclusion of this kind).
    TRIGGERS = {
        "Container: Fake Chest - Fake Item (#1/1)": {"kind": "zone_pool_credit", "zone_key": "fake", "ordinal": 1},
    }


class TestClaimedRows(unittest.TestCase):
    def setUp(self):
        self._original_categories = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [
            SimpleNamespace(key="quest_rewards", locations_module=_FakeQuestFamily),
            SimpleNamespace(key="vendor_stock", locations_module=_FakeVendorFamily),
            SimpleNamespace(key="containersanity", locations_module=_FakeZonePoolFamily),
        ]

    def tearDown(self):
        locations_module._OPTIONAL_CATEGORIES = self._original_categories

    def test_quest_reward_location_claims_quest_template_row(self):
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(
                get_locations=lambda player: [_FakeLocation("Quest: Fake Reward (#1)")]
            ),
        )
        self.assertEqual(mutation_claimed_rows.claimed_rows(world), {("quest_template", 1)})

    def test_vendor_purchase_location_claims_npc_vendor_row(self):
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(
                get_locations=lambda player: [_FakeLocation("Vendor: Fake NPC - Fake Item (#1)")]
            ),
        )
        self.assertEqual(mutation_claimed_rows.claimed_rows(world), {("npc_vendor", (54, 0))})

    def test_zone_pool_credit_location_claims_nothing(self):
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(
                get_locations=lambda player: [_FakeLocation("Container: Fake Chest - Fake Item (#1/1)")]
            ),
        )
        self.assertEqual(mutation_claimed_rows.claimed_rows(world), set())

    def test_location_with_no_matching_trigger_claims_nothing(self):
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(
                get_locations=lambda player: [_FakeLocation("Achievement: Fake Deed")]
            ),
        )
        self.assertEqual(mutation_claimed_rows.claimed_rows(world), set())

    def test_only_locations_actually_instantiated_are_consulted(self):
        # A location present in a family's static TRIGGERS table but NOT
        # returned by get_locations (i.e. not sampled into this seed) must
        # not appear -- Sec4's "varies by the connected slot's options"
        # ruling.
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: []),
        )
        self.assertEqual(mutation_claimed_rows.claimed_rows(world), set())
