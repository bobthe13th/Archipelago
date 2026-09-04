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
    TRIGGERS = {"Quest: Fake Reward (#1)": {"kind": "quest_reward", "quest_id": 1}}


class _FakeVendorLocationsModule:
    LOCATIONS = {"Vendor: Fake NPC - Fake Item (#1)": 2500000}
    TRIGGERS = {"Vendor: Fake NPC - Fake Item (#1)": {"kind": "vendor_purchase", "npc_entry": 1}}


class _FakeContainersanityLocationsModule:
    # M4.11.4.1 rewrote this family to 100% abstract zone-pool locations --
    # there is no backing gameobject_loot_template row for one, so
    # SynthesizeAndRewireLocations can never resolve it (see Fix 3).
    LOCATIONS = {"Container: Fake Chest - Fake Item (#1/1)": 8000000}
    TRIGGERS = {
        "Container: Fake Chest - Fake Item (#1/1)":
            {"kind": "zone_pool_credit", "zone_key": "fake_zone", "ordinal": 1},
    }


class _FakeGathersanityLocationsModule:
    # Deliberately MIXED, mirroring the real family after M4.11.4.2: a
    # zone_pool_credit gathering-node row (not resolvable) alongside a real
    # skinning_loot row (resolvable, still needs synthesis).
    LOCATIONS = {
        "Gathersanity: Fake Vein - Fake Ore (#1/1)": 9000000,
        "Gathersanity: Fake Hide (skinning #1/2)": 9000001,
    }
    TRIGGERS = {
        "Gathersanity: Fake Vein - Fake Ore (#1/1)":
            {"kind": "zone_pool_credit", "zone_key": "fake_zone|mining|apprentice", "ordinal": 1},
        "Gathersanity: Fake Hide (skinning #1/2)":
            {"kind": "skinning_loot", "loot_id": 1, "wow_item_entry": 2},
    }


class _FakeHookOnlyLocationsModule:
    # A family with no TRIGGERS table at all (fired by a C++ hook, never by
    # rewriting a real DB row) must contribute nothing and must not raise.
    LOCATIONS = {"Achievement: Fake Deed": 3000000}


class TestAddApItemDisplayData(unittest.TestCase):
    def setUp(self) -> None:
        # Finding I3 + M4.11.4.2 Fix 3: _add_ap_item_display_data now only
        # includes locations whose OWN generated trigger kind
        # SynthesizeAndRewireLocations can actually resolve -- swap the
        # registry for this test's duration so it exercises the real filtering
        # logic against a small, controlled set of names instead of the full
        # 130k-row real content tables. Restored in tearDown regardless of
        # test outcome.
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
            locations_module.OptionalCategory(
                key="gathersanity",
                tag_options={
                    "expansion": "gathersanity_expansion_pools",
                    "source": "gathersanity_source_pools",
                },
                weight_option=None,
                locations_module=_FakeGathersanityLocationsModule, items_module=None,
            ),
            locations_module.OptionalCategory(
                key="achievements", tag_options={}, weight_option=None,
                locations_module=_FakeHookOnlyLocationsModule, items_module=None,
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

    def test_excludes_zone_pool_credit_locations(self) -> None:
        # M4.11.4.2 final review fix wave 2 (Fix 3). This test previously
        # asserted the OPPOSITE (test_includes_containersanity_locations,
        # M4.10.1) -- correctly, back when every Containersanity location was
        # a real gameobject_loot row. M4.11.4.1 rewrote the family to abstract
        # zone-pool locations, which by construction have NO backing
        # quest_template/npc_vendor/loot_template row for
        # SynthesizeAndRewireLocations (APItemDisplay.cpp) to rewrite. Leaving
        # them eligible made the C++ side synthesize a permanent orphan
        # item_template row AND log one "no matching ... trigger -- skipped,
        # no row to rewrite" LOG_ERROR per location, on every server boot
        # (22,519 of them at real scale across both families).
        locations = [
            _FakeLocation("Container: Fake Chest - Fake Item (#1/1)", 8000000, _FakeItem("Fishing Pole", player=1, classification=ItemClassification.useful)),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(data["ap_item_display"], {})

    def test_includes_gathersanity_loot_rows_but_not_its_zone_pool_rows(self) -> None:
        # M4.10.2 final whole-branch review (C1) established that Gathersanity
        # locations must reach ap_item_display at all -- SynthesizeAndRewireLocations
        # iterates ONLY this slot_data map, so the server-side skinning/
        # disenchant loot-slot lookup maps (built from the exact same location
        # ids) are never even consulted for a location missing from it.
        #
        # M4.11.4.2 Fix 3 narrows that: the family is now MIXED. Its
        # skinning_loot/disenchant_loot rows still need real synthesis; its
        # gathering_node rows are abstract zone_pool_credit locations that can
        # never resolve. A family-keyed filter cannot express this -- that is
        # exactly why eligibility moved to the per-location trigger kind.
        locations = [
            _FakeLocation("Gathersanity: Fake Vein - Fake Ore (#1/1)", 9000000, _FakeItem("Copper Ore", player=1, classification=ItemClassification.filler)),
            _FakeLocation("Gathersanity: Fake Hide (skinning #1/2)", 9000001, _FakeItem("Rugged Leather", player=1, classification=ItemClassification.filler)),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(
            data["ap_item_display"],
            {9000001: {"name": "Tester's Rugged Leather", "flags": int(ItemClassification.filler)}},
        )

    def test_family_with_no_triggers_table_contributes_nothing(self) -> None:
        # A hook-fired family (achievements, rares, ...) has no TRIGGERS table
        # at all; the eligibility scan must skip it silently rather than raise.
        locations = [
            _FakeLocation("Achievement: Fake Deed", 3000000, _FakeItem("Tabard", player=1, classification=ItemClassification.filler)),
        ]
        world = SimpleNamespace(
            player=1,
            multiworld=SimpleNamespace(get_locations=lambda player: locations, get_player_name=lambda p: "Tester"),
        )
        data: dict = {}
        slot_data_module._add_ap_item_display_data(world, data)
        self.assertEqual(data["ap_item_display"], {})

    def test_eligible_trigger_kinds_match_the_cpp_dispatch(self) -> None:
        # Generalized trip-wire for the bug class that has now recurred three
        # times (M4.10.1 containersanity omitted, M4.10.2 gathersanity
        # omitted, M4.11.4.2 zone_pool_credit wrongly INCLUDED). The set below
        # must stay in lock-step with the branches
        # SynthesizeAndRewireLocations (APItemDisplay.cpp) actually dispatches
        # on -- if that C++ function grows or loses a branch, change this too.
        self.assertEqual(
            slot_data_module._AP_ITEM_DISPLAY_TRIGGER_KINDS,
            frozenset({"quest_reward", "vendor_purchase", "skinning_loot", "disenchant_loot"}),
        )
        # And "abstract pool slot" must never be in it, whichever family emits it.
        self.assertNotIn("zone_pool_credit", slot_data_module._AP_ITEM_DISPLAY_TRIGGER_KINDS)

    def test_no_real_zone_pool_credit_location_is_eligible(self) -> None:
        # Checked against the REAL registry (not this class's fakes), so a
        # future family emitting zone_pool_credit rows can't silently
        # reintroduce the orphan-row/log-spam regression. Also asserts the
        # real resolvable rows ARE still eligible, so this can't pass
        # vacuously by excluding everything. setUp swapped the registry for
        # fakes, so restore the real one for the duration of this one test.
        locations_module._OPTIONAL_CATEGORIES = self._original_categories
        eligible = slot_data_module._ap_item_display_eligible_location_names()
        resolvable_seen = 0
        for category in self._original_categories:
            triggers = getattr(category.locations_module, "TRIGGERS", None)
            if not triggers:
                continue
            for name, trigger in triggers.items():
                kind = trigger.get("kind")
                if kind == "zone_pool_credit":
                    self.assertNotIn(name, eligible)
                elif kind in slot_data_module._AP_ITEM_DISPLAY_TRIGGER_KINDS:
                    self.assertIn(name, eligible)
                    resolvable_seen += 1
        self.assertGreater(resolvable_seen, 0)
        self.assertEqual(len(eligible), resolvable_seen)

    def test_excludes_locations_with_no_resolvable_trigger(self) -> None:
        # Finding I3's actual regression target: a location that has a real
        # item placed and a real address, but whose trigger the C++ side can't
        # resolve (e.g. a core-loop level-up location, which isn't in any
        # OptionalCategory at all) must be excluded, not included
        # "harmlessly" as the pre-fix code did.
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


class TestAddHolidaysanityStacking(unittest.TestCase):
    def test_adds_holidaysanity_stacking_bool(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(holidaysanity_stacking=True))
        data = {}
        slot_data_module._add_holidaysanity_stacking(world, data)
        self.assertTrue(data["holidaysanity_stacking"])


class TestAddZoneLevelerData(unittest.TestCase):
    def test_noop_for_non_zone_leveler_game_mode(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(game_mode="sprint"))
        data: dict = {}
        slot_data_module._add_zone_leveler_data(world, data)
        self.assertEqual(data, {})

    def test_adds_zone_key_goals_statues_and_instances_for_zone_leveler(self) -> None:
        from .. import zone_leveler_content_data

        zone_data = zone_leveler_content_data.ZONES["barrens"]
        world = SimpleNamespace(options=SimpleNamespace(
            game_mode="zone_leveler",
            zone_leveler_starting_zone=SimpleNamespace(current_key="barrens"),
            zone_leveler_goals=SimpleNamespace(value={"golden_boar_statues", "instance_clears"}),
            zone_leveler_statues_required=SimpleNamespace(value=5),
            zone_leveler_instances_required=SimpleNamespace(value=1),
        ))
        data: dict = {}
        slot_data_module._add_zone_leveler_data(world, data)
        self.assertEqual(data["zone_leveler_zone_key"], "barrens")
        self.assertEqual(data["zone_leveler_goals"], sorted({"golden_boar_statues", "instance_clears"}))
        self.assertEqual(data["zone_leveler_statues_required"], 5)
        self.assertEqual(data["zone_leveler_instances_required"], 1)
        # Final whole-branch review fix (Minor #6): emits the CURATED subset,
        # not the raw, wider zone_data.instance_keys -- and for Barrens these
        # two sets genuinely differ (dire_maul/maraudon/onyxia_s_lair are
        # real, reachable, but never curated with a core_loop.yaml
        # instance_clear row), so this assertion would have failed before
        # the slot_data.py fix if it had compared against the curated set.
        self.assertEqual(
            data["zone_leveler_instance_keys"],
            list(zone_leveler_content_data.curated_instance_keys(zone_data)),
        )
        self.assertNotEqual(data["zone_leveler_instance_keys"], list(zone_data.instance_keys))

    def test_drops_hub_zone_fields(self) -> None:
        """M4.11.3.3 Task 3: zone_leveler_zone_id/zone_leveler_allowed_hub_zone_ids/
        zone_leveler_allow_hub_zone are no longer emitted -- Task 1 already removed
        the ZoneLevelerZoneData fields the first two read, and Task 3 removes the
        zone_leveler_allow_hub_zone option itself."""
        world = SimpleNamespace(options=SimpleNamespace(
            game_mode="zone_leveler",
            zone_leveler_starting_zone=SimpleNamespace(current_key="barrens"),
            zone_leveler_goals=SimpleNamespace(value=set()),
            zone_leveler_statues_required=SimpleNamespace(value=5),
            zone_leveler_instances_required=SimpleNamespace(value=1),
        ))
        data: dict = {}
        slot_data_module._add_zone_leveler_data(world, data)
        self.assertNotIn("zone_leveler_zone_id", data)
        self.assertNotIn("zone_leveler_allowed_hub_zone_ids", data)
        self.assertNotIn("zone_leveler_allow_hub_zone", data)

    def test_goals_statues_and_instances_required_reflect_options(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(
            game_mode="zone_leveler",
            zone_leveler_starting_zone=SimpleNamespace(current_key="barrens"),
            zone_leveler_goals=SimpleNamespace(
                value={"reach_zone_level_cap", "clear_all_zone_quests", "golden_boar_statues", "instance_clears"}
            ),
            zone_leveler_statues_required=SimpleNamespace(value=12),
            zone_leveler_instances_required=SimpleNamespace(value=3),
        ))
        data: dict = {}
        slot_data_module._add_zone_leveler_data(world, data)
        self.assertEqual(
            data["zone_leveler_goals"],
            ["clear_all_zone_quests", "golden_boar_statues", "instance_clears", "reach_zone_level_cap"],
        )
        self.assertEqual(data["zone_leveler_statues_required"], 12)
        self.assertEqual(data["zone_leveler_instances_required"], 3)
