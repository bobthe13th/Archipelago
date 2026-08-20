# Archipelago/worlds/wow/test/test_basic.py
from .bases import WoWTestBase
from .. import content_data
from .. import core_loop_content_data
from .. import traps_content_data


class TestDefault(WoWTestBase):
    options = {}


class TestNorthshireGeneration(WoWTestBase):
    def test_all_locations_reachable(self) -> None:
        """M2: all 19 curated locations must be reachable with no items required
        (matches rules.py's no-op access rules for this milestone)."""
        self.assertTrue(len(self.multiworld.get_reachable_locations()) >= 19)

    def test_default_item_pool_size(self) -> None:
        """As of M2.1, create_items always adds both M2's quest-item pool
        (19) and the core-loop item pool (14 as of M2.1, grown to 17 by Task
        23's three new raid Instance Unlock items): 36 total. In M4 Tasks
        5-6, 7 gate items are added unconditionally (riding x5, flight x2 =
        43 total). Every other Group 1 gate item (Tasks 7/8/10, 27 of them)
        is option-gated and off by default, so it's absent from this count --
        see each option's TestXItemsPooledWhenOptionOn class for the
        option-on pool. Formerly named test_item_pool_matches_location_count
        when this number needed to equal the location count exactly; Task 11
        made that unnecessary to check here -- see
        test_item_pool_matches_location_count_exactly below (and
        locations.py's create_filler_locations) for how parity is now
        maintained dynamically instead of via a fixed number."""
        self.assertEqual(len(self.multiworld.itempool), 43)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        """Task 11: AP's generation pipeline has no generic step that pads a
        short itempool to match location count (Main.py's only itempool<->
        create_filler() interaction is a fixed-size 1:1 swap for
        start_inventory_from_pool removals, not padding) -- confirmed
        empirically, distribute_items_restrictive raises "Unable to fill all
        locations" just as readily when locations exceed items as when items
        exceed locations. So real 1:1 parity is required for every option
        combination, not just "locations >= items". locations.py's
        create_filler_locations achieves this dynamically: it slices
        content/filler.yaml's 27 rows (the max possible, one per
        gates_content_data.ITEMS entry) down to exactly
        items.py's count_enabled_gates_items(world) for whatever options
        this generation actually has -- see TestGateItemSphereZero (every
        optional gate on) for the other end of that range."""
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestGatesItemPool(WoWTestBase):
    def test_gates_items_are_in_the_pool(self) -> None:
        for tier_name in (
            "Progressive Riding: Apprentice",
            "Progressive Riding: Journeyman",
            "Progressive Riding: Expert",
            "Progressive Riding: Artisan",
            "Progressive Riding: Cold Weather Flying",
            "Flight Unlock: Outland",
            "Flight Unlock: Northrend",
        ):
            self.assertEqual(len(self.get_items_by_name(tier_name)), 1)


_PROFICIENCY_ITEM_NAMES = (
    "Armor Proficiency: Plate",
    "Armor Proficiency: Mail",
    "Armor Proficiency: Leather",
    "Weapon Proficiency: Two-Handed Swords",
    "Weapon Proficiency: Axes",
    "Weapon Proficiency: Maces",
    "Weapon Proficiency: Staves",
    "Weapon Proficiency: Wands",
)


class TestProficiencyItemsPooledWhenOptionOff(WoWTestBase):
    options = {"proficiency_gating": False}

    def test_proficiency_items_absent_when_option_is_off(self) -> None:
        for name in _PROFICIENCY_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 0)


class TestProficiencyItemsPooledWhenOptionOn(WoWTestBase):
    options = {"proficiency_gating": True}

    def test_proficiency_items_present_when_option_is_on(self) -> None:
        for name in _PROFICIENCY_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 1)


_ACCESS_ITEM_NAMES = (
    "Auction House Access",
    "Hearthstone Access",
    "Mailbox Access",
)


class TestAccessItemsPooledWhenOptionOff(WoWTestBase):
    options = {"access_gating": False}

    def test_access_items_absent_when_option_is_off(self) -> None:
        for name in _ACCESS_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 0)


class TestAccessItemsPooledWhenOptionOn(WoWTestBase):
    options = {"access_gating": True}

    def test_access_items_present_when_option_is_on(self) -> None:
        for name in _ACCESS_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 1)


_CHARACTER_UNLOCK_ITEM_NAMES = (
    "Progressive Bank Bag Slot: Slot 1",
    "Progressive Bank Bag Slot: Slot 2",
    "Progressive Bank Bag Slot: Slot 3",
    "Progressive Bank Bag Slot: Slot 4",
    "Progressive Bank Bag Slot: Slot 5",
    "Progressive Bank Bag Slot: Slot 6",
    "Progressive Bank Bag Slot: Slot 7",
    "Talent Point Access",
    "Dual Spec Unlock",
)


class TestCharacterUnlockItemsPooledWhenOptionOff(WoWTestBase):
    options = {"character_unlock_gating": False}

    def test_character_unlock_items_absent_when_option_is_off(self) -> None:
        for name in _CHARACTER_UNLOCK_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 0)


class TestCharacterUnlockItemsPooledWhenOptionOn(WoWTestBase):
    options = {"character_unlock_gating": True}

    def test_character_unlock_items_present_when_option_is_on(self) -> None:
        for name in _CHARACTER_UNLOCK_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 1)


class TestComboUnlockItemsScopeOff(WoWTestBase):
    options = {"combo_unlocks_scope": "off"}

    def test_neither_combo_item_is_pooled(self) -> None:
        self.assertEqual(len(self.get_items_by_name("TBC Combo Unlock")), 0)
        self.assertEqual(len(self.get_items_by_name("WotLK Combo Unlock")), 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestComboUnlockItemsScopeTbc(WoWTestBase):
    options = {"combo_unlocks_scope": "tbc"}

    def test_only_tbc_combo_item_is_pooled(self) -> None:
        self.assertEqual(len(self.get_items_by_name("TBC Combo Unlock")), 1)
        self.assertEqual(len(self.get_items_by_name("WotLK Combo Unlock")), 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestComboUnlockItemsScopeWotlk(WoWTestBase):
    options = {"combo_unlocks_scope": "wotlk"}

    def test_only_wotlk_combo_item_is_pooled(self) -> None:
        self.assertEqual(len(self.get_items_by_name("TBC Combo Unlock")), 0)
        self.assertEqual(len(self.get_items_by_name("WotLK Combo Unlock")), 1)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestComboUnlockItemsScopeBoth(WoWTestBase):
    options = {"combo_unlocks_scope": "both"}

    def test_both_combo_items_are_pooled(self) -> None:
        self.assertEqual(len(self.get_items_by_name("TBC Combo Unlock")), 1)
        self.assertEqual(len(self.get_items_by_name("WotLK Combo Unlock")), 1)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestGateItemSphereZero(WoWTestBase):
    """§16's "gate-item sphere-0 test": no riding/proficiency/access/
    character-unlock gate may block any sphere-0 completion path. Turns
    every optional gate family on (the maximal-restriction case) rather
    than using default options -- with every gate off by default, a test
    using default options couldn't actually prove any gate is sphere-0-safe,
    since an off gate trivially blocks nothing. rules.py never calls
    world.set_rule on any of the 19 quest locations (see rules.py's M2
    comment) and no Group 1 task added one either, so this is a regression
    guard against a future gate task accidentally doing so, not a fix for
    a live bug."""

    options = {
        "proficiency_gating": True,
        "access_gating": True,
        "character_unlock_gating": True,
    }

    def test_all_quest_locations_reachable_with_zero_items(self) -> None:
        for name in content_data.LOCATIONS:
            self.assertTrue(self.can_reach_location(name))

    def test_item_pool_matches_location_count_exactly(self) -> None:
        """Same invariant as TestNorthshireGeneration's version of this
        test, checked here at the other end of the option range (every
        optional gate on) -- see that test's docstring for why exact parity
        (not just locations >= items) is required."""
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestCoreLoopAccessRules(WoWTestBase):
    """Final-review fix: rules.py must attach real prerequisites to the
    core-loop locations, matching the real C++ server's genuine
    prerequisites, so the fill algorithm can no longer place a required
    Progressive Level Cap copy on a milestone location that itself requires
    already having that copy (which produced permanently unwinnable seeds
    when rules.py's set_rules was a no-op)."""

    def test_reach_level_60_needs_all_ten_progressive_level_caps(self) -> None:
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.collect(progressive_caps[:9])
        self.assertFalse(self.can_reach_location("Reach Level 60"))
        self.collect(progressive_caps[9:])
        self.assertTrue(self.can_reach_location("Reach Level 60"))

    def test_clear_ragefire_chasm_needs_its_instance_unlock(self) -> None:
        self.assertFalse(self.can_reach_location("Clear Ragefire Chasm"))
        unlock = self.get_items_by_name("Instance Unlock: Ragefire Chasm")
        self.collect(unlock)
        self.assertTrue(self.can_reach_location("Clear Ragefire Chasm"))

    def test_clear_deadmines_needs_its_instance_unlock(self) -> None:
        self.assertFalse(self.can_reach_location("Clear Deadmines"))
        unlock = self.get_items_by_name("Instance Unlock: Deadmines")
        self.collect(unlock)
        self.assertTrue(self.can_reach_location("Clear Deadmines"))

    def test_reach_level_10_now_needs_full_dk_safe_requirement(self) -> None:
        # Fix under test: every "Reach Level N" location for N < 55 must require
        # the SAME copy count as "Reach Level 55" (9 copies), not its own smaller
        # per-level threshold -- otherwise a required Progressive Level Cap copy
        # could land on a Death Knight-unreachable location (levels 5-55 never
        # fire their level-up hook for a DK, see rules.py's module docstring).
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.collect(progressive_caps[:8])
        self.assertFalse(self.can_reach_location("Reach Level 10"))
        self.collect(progressive_caps[8:9])
        self.assertTrue(self.can_reach_location("Reach Level 10"))

    def test_reach_level_55_and_below_share_the_same_threshold(self) -> None:
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.collect(progressive_caps[:9])
        for level in (10, 15, 20, 25, 30, 35, 40, 45, 50, 55):
            self.assertTrue(self.can_reach_location(f"Reach Level {level}"))


class TestSprintGoal(WoWTestBase):
    def test_sprint_goal_requires_all_progressive_level_caps(self) -> None:
        """Reaching the Sprint goal must require all 10 Progressive Level
        Cap copies (starting cap 10, +5 each, reaches exactly 60).

        Note: WorldTestBase.collect_by_name collects *every* matching item
        in the pool in one call (it is not "collect one copy"), so to
        exercise the 9-vs-10 boundary we must collect specific item objects
        directly via self.collect() rather than calling collect_by_name in
        a loop.
        """
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(progressive_caps), 10)
        self.collect(progressive_caps[:9])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect(progressive_caps[9:])
        self.assertTrue(self.multiworld.completion_condition[self.player](state))

    def test_core_loop_item_pool_matches_location_count(self) -> None:
        core_loop_item_count = sum(count for _, count in core_loop_content_data.ITEMS.values())
        # 12 level milestones + 5 instance clears (Ragefire Chasm, Deadmines,
        # and Task 23's Molten Core/Sunwell Plateau/Icecrown Citadel).
        core_loop_location_count = 12 + 5
        self.assertEqual(core_loop_item_count, core_loop_location_count)


_ALL_TRAP_ITEM_NAMES = tuple(traps_content_data.ITEMS)
_LETHAL_TRAP_ITEM_NAMES = tuple(name for name in _ALL_TRAP_ITEM_NAMES if traps_content_data.LETHAL_BY_ITEM_NAME[name])
_NON_LETHAL_TRAP_ITEM_NAMES = tuple(name for name in _ALL_TRAP_ITEM_NAMES if name not in _LETHAL_TRAP_ITEM_NAMES)


class TestTrapItemsPooledWhenOptionOff(WoWTestBase):
    options = {"traps_enabled": False}

    def test_no_trap_items_in_pool(self) -> None:
        for name in _ALL_TRAP_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestTrapItemsPooledWhenOptionOn(WoWTestBase):
    options = {"traps_enabled": True, "trap_percentage_of_filler": 100, "lethal_traps_enabled": True}

    def test_trap_item_total_matches_count_enabled_trap_items(self) -> None:
        from .. import items as items_module
        expected = items_module.count_enabled_trap_items(self.world)
        actual = sum(len(self.get_items_by_name(name)) for name in _ALL_TRAP_ITEM_NAMES)
        self.assertEqual(actual, expected)
        self.assertGreater(expected, 0, "trap_percentage_of_filler=100 must produce a nonzero total")

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestLethalTrapsExcludedByDefault(WoWTestBase):
    options = {"traps_enabled": True, "trap_percentage_of_filler": 100}

    def test_no_lethal_trap_items_when_lethal_traps_enabled_is_off(self) -> None:
        for name in _LETHAL_TRAP_ITEM_NAMES:
            self.assertEqual(len(self.get_items_by_name(name)), 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestTrapEligibility(WoWTestBase):
    """Directly exercises items.py's eligibility/count helpers rather than
    relying on random sampling to happen to produce (or omit) a lethal trap
    -- with only 2 lethal item types among 17, a randomized distribution
    test could pass or fail by chance depending on trap_percentage_of_filler
    and world.random's seed, which would make this test flaky. Testing the
    deterministic helpers directly avoids that."""
    options = {"traps_enabled": True, "lethal_traps_enabled": True}

    def test_lethal_traps_are_eligible_when_option_is_on(self) -> None:
        from .. import items as items_module
        eligible = items_module._eligible_trap_names(self.world)
        for name in _LETHAL_TRAP_ITEM_NAMES:
            self.assertIn(name, eligible)


class TestTrapDistributionModeWeighted(WoWTestBase):
    options = {"traps_enabled": True, "trap_percentage_of_filler": 100, "trap_distribution_mode": "weighted"}

    def test_distribution_sums_to_the_predicted_total(self) -> None:
        from .. import items as items_module
        expected = items_module.count_enabled_trap_items(self.world)
        actual = sum(len(self.get_items_by_name(name)) for name in _NON_LETHAL_TRAP_ITEM_NAMES)
        self.assertEqual(actual, expected)


class TestTrapDistributionModeUniform(WoWTestBase):
    options = {"traps_enabled": True, "trap_percentage_of_filler": 100, "trap_distribution_mode": "uniform"}

    def test_distribution_sums_to_the_predicted_total(self) -> None:
        from .. import items as items_module
        expected = items_module.count_enabled_trap_items(self.world)
        actual = sum(len(self.get_items_by_name(name)) for name in _NON_LETHAL_TRAP_ITEM_NAMES)
        self.assertEqual(actual, expected)

    def test_spread_is_roughly_even_across_eligible_types(self) -> None:
        counts = [len(self.get_items_by_name(name)) for name in _NON_LETHAL_TRAP_ITEM_NAMES]
        self.assertLessEqual(max(counts) - min(counts), 1, "uniform distribution should differ by at most 1 between any two eligible types")


class TestTrapDistributionModeChaos(WoWTestBase):
    options = {"traps_enabled": True, "trap_percentage_of_filler": 100, "trap_distribution_mode": "chaos"}

    def test_distribution_sums_to_the_predicted_total(self) -> None:
        from .. import items as items_module
        expected = items_module.count_enabled_trap_items(self.world)
        actual = sum(len(self.get_items_by_name(name)) for name in _NON_LETHAL_TRAP_ITEM_NAMES)
        self.assertEqual(actual, expected)


class TestTrapsAndGatesCombinedParity(WoWTestBase):
    """Task 17's parity extension to Task 11's mechanism: traps and gates
    are two independently-sized optional families sharing one filler
    ceiling (content/filler.yaml's 62 rows, grown from 60 by Task 21's two
    combo-unlock items). Stress-tests both at their most extreme settings
    simultaneously (including combo_unlocks_scope: "both", the setting that
    actually reaches the full 29-item gates worst case) -- if the combined
    count_enabled_gates_items() + count_enabled_trap_items() ever exceeds
    62, or if the two counts are computed inconsistently between
    create_items and create_regions' create_filler_locations, this is
    where it would show up as a FillError."""
    options = {
        "proficiency_gating": True,
        "access_gating": True,
        "character_unlock_gating": True,
        "combo_unlocks_scope": "both",
        "traps_enabled": True,
        "trap_percentage_of_filler": 100,
        "lethal_traps_enabled": True,
    }

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))

    def test_all_quest_locations_still_reachable_with_zero_items(self) -> None:
        # Traps carry no access rule and gate no location -- sphere-0 safety
        # should be unaffected by traps_enabled, same guarantee
        # TestGateItemSphereZero already covers for the gate family alone.
        for name in content_data.LOCATIONS:
            self.assertTrue(self.can_reach_location(name))
