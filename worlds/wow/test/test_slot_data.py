import unittest
from types import SimpleNamespace

from .. import locations as locations_module
from .. import slot_data as slot_data_module
from BaseClasses import ItemClassification


class _FakeItem:
    def __init__(self, name: str, player: int, classification: ItemClassification) -> None:
        self.name = name
        self.player = player
        self.classification = classification


class _FakeLocation:
    def __init__(self, name, address, item) -> None:
        self.name = name
        self.address = address
        self.item = item


class _FakeFamilyLocationsModule:
    LOCATIONS = {"Quest: Fake Reward (#1)": 2000000}


class _FakeVendorLocationsModule:
    LOCATIONS = {"Vendor: Fake NPC - Fake Item (#1)": 2500000}


class _FakeContainersanityLocationsModule:
    LOCATIONS = {"Container: Fake Chest - Fake Item (#1/1)": 8000000}


class TestAddApItemDisplayData(unittest.TestCase):
    def setUp(self) -> None:
        # Finding I3: _add_ap_item_display_data now only includes locations
        # whose name is registered under the quest_rewards/vendor_stock
        # OptionalCategory entries -- swap the registry for this test's
        # duration so it exercises the real filtering logic against a small,
        # controlled set of names instead of the full 41k-row real content
        # tables. Restored in tearDown regardless of test outcome.
        self._original_categories = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = [
            locations_module.OptionalCategory(
                key="quest_rewards", tag_options={}, weight_option="quest_reward_weight",
                locations_module=_FakeFamilyLocationsModule, items_module=None,
            ),
            locations_module.OptionalCategory(
                key="vendor_stock", tag_options={}, weight_option="vendor_stock_weight",
                locations_module=_FakeVendorLocationsModule, items_module=None,
            ),
            locations_module.OptionalCategory(
                key="containersanity", tag_options={"expansion": "containersanity_expansion_pools"},
                weight_option=None,
                locations_module=_FakeContainersanityLocationsModule, items_module=None,
            ),
        ]

    def tearDown(self) -> None:
        locations_module._OPTIONAL_CATEGORIES = self._original_categories

    def test_builds_one_entry_per_ap_item_family_location(self) -> None:
        locations = [
            _FakeLocation("Quest: Fake Reward (#1)", 2000000, _FakeItem("Sword of Might", player=2, classification=ItemClassification.progression)),
            _FakeLocation("Vendor: Fake NPC - Fake Item (#1)", 2500000, _FakeItem("Minor Heal Potion", player=1, classification=ItemClassification.filler)),
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
                2500000: {"name": "Tester's Minor Heal Potion", "flags": int(ItemClassification.filler)},
            },
        )

    def test_skips_locations_with_no_item_or_no_address(self) -> None:
        locations = [
            _FakeLocation("Quest: Fake Reward (#1)", None, _FakeItem("Unplaced", player=1, classification=ItemClassification.filler)),
            _FakeLocation("Vendor: Fake NPC - Fake Item (#1)", 2500000, None),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(data["ap_item_display"], {})

    def test_includes_containersanity_locations(self) -> None:
        # M4.10.1 final regression pass (Task 8): _AP_ITEM_DISPLAY_FAMILY_KEYS
        # originally omitted "containersanity" entirely, which silently made
        # SynthesizeAndRewireLocations (APItemDisplay.cpp) skip the whole
        # family -- it iterates ONLY this slot_data map, so
        # BuildLocationIdToGameobjectLootSlot's own map (built server-side
        # from the exact same location ids) was never even consulted. A
        # Containersanity location must appear in ap_item_display exactly
        # like quest_rewards/vendor_stock locations do.
        locations = [
            _FakeLocation("Container: Fake Chest - Fake Item (#1/1)", 8000000, _FakeItem("Fishing Pole", player=1, classification=ItemClassification.useful)),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(
            data["ap_item_display"],
            {8000000: {"name": "Tester's Fishing Pole", "flags": int(ItemClassification.useful)}},
        )

    def test_excludes_locations_outside_quest_rewards_and_vendor_stock(self) -> None:
        # Finding I3's actual regression target: a location that has a real
        # item placed and a real address, but does NOT belong to either
        # registered family (e.g. a core-loop level-up location) must be
        # excluded, not included "harmlessly" as the pre-fix code did.
        locations = [
            _FakeLocation("Reach Level 10", 900010, _FakeItem("Progressive Level Cap", player=1, classification=ItemClassification.progression)),
            _FakeLocation("Quest: Fake Reward (#1)", 2000000, _FakeItem("Sword of Might", player=1, classification=ItemClassification.progression)),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(
            data["ap_item_display"],
            {2000000: {"name": "Tester's Sword of Might", "flags": int(ItemClassification.progression)}},
        )


class TestAddInstanceClearMode(unittest.TestCase):
    def test_adds_instance_clear_mode_current_key(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(instance_clear_mode=SimpleNamespace(current_key="final_boss_only")))
        data: dict = {}
        slot_data_module._add_instance_clear_mode(world, data)
        self.assertEqual(data["instance_clear_mode"], "final_boss_only")


class TestAddVendorCheckRepeatBehavior(unittest.TestCase):
    def test_adds_vendor_check_repeat_behavior_current_key(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(vendor_check_repeat_behavior=SimpleNamespace(current_key="gold_conversion")))
        data: dict = {}
        slot_data_module._add_vendor_check_repeat_behavior(world, data)
        self.assertEqual(data["vendor_check_repeat_behavior"], "gold_conversion")


class TestAddLootSlotCheckRepeatBehavior(unittest.TestCase):
    def test_adds_loot_slot_check_repeat_behavior_current_key(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(loot_slot_check_repeat_behavior=SimpleNamespace(current_key="vanilla_item")))
        data: dict = {}
        slot_data_module._add_loot_slot_check_repeat_behavior(world, data)
        self.assertEqual(data["loot_slot_check_repeat_behavior"], "vanilla_item")
