import unittest
from types import SimpleNamespace

from .. import slot_data as slot_data_module
from BaseClasses import ItemClassification


class _FakeItem:
    def __init__(self, name: str, player: int, classification: ItemClassification) -> None:
        self.name = name
        self.player = player
        self.classification = classification


class _FakeLocation:
    def __init__(self, address, item) -> None:
        self.address = address
        self.item = item


class TestAddApItemDisplayData(unittest.TestCase):
    def test_builds_one_entry_per_ap_item_family_location(self) -> None:
        locations = [
            _FakeLocation(2000000, _FakeItem("Sword of Might", player=2, classification=ItemClassification.progression)),
            _FakeLocation(1000001, _FakeItem("Minor Heal Potion", player=1, classification=ItemClassification.filler)),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(
                get_locations=lambda player: locations,
                get_player_name=lambda player_id: {1: "Tester", 2: "Alice"}[player_id],
            ),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(
            data["ap_item_display"],
            {
                2000000: {"name": "Alice's Sword of Might", "flags": int(ItemClassification.progression)},
                1000001: {"name": "Tester's Minor Heal Potion", "flags": int(ItemClassification.filler)},
            },
        )

    def test_skips_locations_with_no_item_or_no_address(self) -> None:
        locations = [
            _FakeLocation(None, _FakeItem("Unplaced", player=1, classification=ItemClassification.filler)),
            _FakeLocation(1000002, None),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(data["ap_item_display"], {})


class TestAddVendorCheckRepeatBehavior(unittest.TestCase):
    def test_adds_vendor_check_repeat_behavior_current_key(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(vendor_check_repeat_behavior=SimpleNamespace(current_key="gold_conversion")))
        data: dict = {}
        slot_data_module._add_vendor_check_repeat_behavior(world, data)
        self.assertEqual(data["vendor_check_repeat_behavior"], "gold_conversion")
