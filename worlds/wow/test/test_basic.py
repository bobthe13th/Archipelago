# Archipelago/worlds/wow/test/test_basic.py
import types
import unittest

from .bases import WoWTestBase
from .. import quest_rewards_content_data
from .. import core_loop_content_data
from .. import traps_content_data


class TestDefault(WoWTestBase):
    options = {}


class TestNorthshireGeneration(WoWTestBase):
    # M4.8.0: test_default_item_pool_size below needs quest_reward_weight/
    # vendor_stock_weight at their REAL production default (100), not
    # WoWTestBase.world_setup's fast-test default of 0 -- explicitly set
    # here so this class's own options dict wins the merge (see bases.py).
    options = {"quest_reward_weight": 100, "vendor_stock_weight": 100}

    def test_all_locations_reachable(self) -> None:
        """M2: all 19 curated locations must be reachable with no items required
        (matches rules.py's no-op access rules for this milestone)."""
        self.assertTrue(len(self.multiworld.get_reachable_locations()) >= 19)

    def test_default_item_pool_size(self) -> None:
        """M4.8.0: with the plain `quests` family retired, and Quest
        Rewards/Vendor Inventories now on-by-default (quest_reward_weight/
        vendor_stock_weight both default 100, replacing the old
        include_quest_rewards/include_vendor_stock toggles which defaulted
        False), the fixed core content (core-loop items + 7 unconditional
        gate items) is joined by BOTH DB-derived families sampled at their
        default weight against check_density's own default (25). Computed
        via density.predict_sample_size rather than hardcoded, since the
        DB-derived families' real row counts change whenever the content
        tables are regenerated.

        M4.9.3.1 Task 11 fix: core_loop's own item count is no longer a
        fixed 21 either -- create_core_loop_item_pool (items.py) now pads
        core-loop's item pool with filler so it exactly matches this
        slot's real, track-aware core-loop LOCATION count (85 for the
        standard track, 31 for death_knight), a hard pre-existing
        item==location parity invariant this apworld enforces per family.
        This test's slot never sets death_knight_slot (neither this class
        nor WoWTestBase.world_setup does), so it resolves to that option's
        real default (False) -- i.e. the standard track. Mirror
        create_core_loop_item_pool's own computation
        (LEVEL_LOCATIONS_BY_TRACK[track] + INSTANCE_CLEAR_LOCATIONS) rather
        than hardcoding a number, so this stays correct if the DB-derived
        core_loop content tables are ever regenerated.

        M4.10.7 fix: Holidaysanity items are pure items-only content, same
        "no location of its own" shape as gates -- this class never sets
        combo_unlocks_scope, so it resolves to that option's real default
        ("off"), under which 9 of Holidaysanity's 14 items are
        unconditionally pooled (the other 5 need combo_unlocks_scope ==
        "both", see items.py's _COMBO_SCOPE_GATED_HOLIDAYS). Computed via
        count_enabled_holidaysanity_items (items.py) rather than hardcoding
        9, so this stays correct if Holidaysanity's roster is ever
        regenerated."""
        from .. import density
        from .. import quest_rewards_content_data
        from .. import vendor_stock_content_data
        from ..items import count_enabled_holidaysanity_items
        is_dk_slot = bool(self.world.options.death_knight_slot)
        track = "death_knight" if is_dk_slot else "standard"
        core_loop_item_count = (
            len(core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK[track])
            + len(core_loop_content_data.INSTANCE_CLEAR_LOCATIONS)
        )
        fixed_count = core_loop_item_count + 7  # core-loop items (track-aware) + 7 unconditional gates (riding x5, flight x2)
        always_present_count = len(quest_rewards_content_data.ALWAYS_PRESENT)
        quest_reward_candidates = len(quest_rewards_content_data.LOCATIONS) - always_present_count
        quest_reward_sampled = density.predict_sample_size(25, 100, quest_reward_candidates)
        vendor_stock_always_present_count = len(vendor_stock_content_data.ALWAYS_PRESENT)
        vendor_stock_candidates = len(vendor_stock_content_data.LOCATIONS) - vendor_stock_always_present_count
        vendor_stock_sampled = density.predict_sample_size(25, 100, vendor_stock_candidates)
        # M4.10.4: repsanity is weight_option=None (every tag-matched row
        # included unconditionally), same shape as recipes/trainer_spells/
        # containersanity/gathersanity/enemysanity -- but like all of those,
        # bases.py's world_setup zeroes its tag pools by default for every
        # WoWTestBase test (test-speed convention), so it contributes zero
        # locations here and correctly has no term in this formula, same as
        # its weight_option=None siblings above.
        holidaysanity_default_count = count_enabled_holidaysanity_items(self.world)
        expected = (
            fixed_count + always_present_count + quest_reward_sampled
            + vendor_stock_always_present_count + vendor_stock_sampled
            + holidaysanity_default_count
        )
        self.assertEqual(len(self.multiworld.itempool), expected)

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
        content/filler.yaml's 37 rows reserved for gates (the max possible,
        one per gates_content_data.ITEMS entry, grown from 27 by Task 21's 2
        combo-unlock items and M4.9's 8 new gate items) down to exactly
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


class TestHolidaysanityItemPoolYieldsAllFourteenByDefault(WoWTestBase):
    # M4.10.7 Task 3: combo_unlocks_scope must be "both" to reach
    # Holidaysanity's own full 14-item roster -- 5 of the 14 Holiday Unlock
    # items are combo-scope-gated (see items.py's
    # _COMBO_SCOPE_GATED_HOLIDAYS), so this class's own options dict wins
    # the WoWTestBase.world_setup merge (see bases.py) to pool all 14, not
    # just the 9 unconditional ones.
    options = {"combo_unlocks_scope": "both"}

    def test_create_holidaysanity_item_pool_yields_all_fourteen_by_default(self) -> None:
        from ..items import create_holidaysanity_item_pool
        pool = create_holidaysanity_item_pool(self.world)
        self.assertEqual(len(pool), 14)


class TestHolidaysanityItemPoolExcludesComboGatedWhenScopeOff(WoWTestBase):
    options = {"combo_unlocks_scope": "off"}

    def test_create_holidaysanity_item_pool_excludes_combo_gated_when_scope_off(self) -> None:
        from ..items import create_holidaysanity_item_pool
        pool = create_holidaysanity_item_pool(self.world)
        self.assertEqual(len(pool), 9)  # 14 - the 5 combo_unlocks_scope-gated holidays


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
    "Bank Access",
    "Gathering Access",
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
    "Progressive Glyph Slot: Slot 1",
    "Progressive Glyph Slot: Slot 2",
    "Progressive Glyph Slot: Slot 3",
    "Progressive Glyph Slot: Slot 4",
    "Progressive Glyph Slot: Slot 5",
    "Progressive Glyph Slot: Slot 6",
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
        for name in quest_rewards_content_data.ALWAYS_PRESENT:
            self.assertTrue(self.can_reach_location(name))

    def test_item_pool_matches_location_count_exactly(self) -> None:
        """Same invariant as TestNorthshireGeneration's version of this
        test, checked here at the other end of the option range (every
        optional gate on) -- see that test's docstring for why exact parity
        (not just locations >= items) is required."""
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestGateItemSphereZeroWithNarrowedQuestRewardPools(WoWTestBase):
    """M4.8.0: the same sphere-0 guard as TestGateItemSphereZero, but with
    quest_reward_type_pools narrowed to a single pool -- confirms tag
    narrowing doesn't affect the always_present sphere-0 locations (they
    bypass tag-filtering entirely) and that the narrowed candidate/item
    pool still maintains exact item=location parity."""

    options = {
        "proficiency_gating": True,
        "access_gating": True,
        "character_unlock_gating": True,
        "quest_reward_type_pools": {"dungeon_quest"},
        "quest_reward_weight": 100,
    }

    def test_all_always_present_quest_locations_reachable_with_zero_items(self) -> None:
        for name in quest_rewards_content_data.ALWAYS_PRESENT:
            self.assertTrue(self.can_reach_location(name))

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestGateItemSphereZeroWithNarrowedVendorStockPools(WoWTestBase):
    """M4.8.0: the same sphere-0 guard, with vendor_stock_expansion_pools
    narrowed to a single pool."""

    options = {
        "proficiency_gating": True,
        "access_gating": True,
        "character_unlock_gating": True,
        "vendor_stock_expansion_pools": {"tbc"},
        "vendor_stock_weight": 100,
    }

    def test_all_always_present_quest_locations_reachable_with_zero_items(self) -> None:
        for name in quest_rewards_content_data.ALWAYS_PRESENT:
            self.assertTrue(self.can_reach_location(name))

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestCoreLoopAccessRules(WoWTestBase):
    """Final-review fix (M2.1) + M4.9 update: rules.py must attach real
    prerequisites to the core-loop locations, matching the real C++
    server's genuine prerequisites, so the fill algorithm can no longer
    place a required Progressive Level Cap copy on a milestone location
    that itself requires already having that copy. M4.9: the old
    Death-Knight "safety collapse" (every location below level 55 needed
    the SAME copy count as level 55) is retired -- default (non-DK) slots
    now use each location's own natural per-level threshold, since the
    standard track no longer needs to share reachability with a class that
    can never reach it (that class gets its own, separate death_knight
    track instead -- see TestDeathKnightSlotLevelMilestoneTracks, Task 5)."""

    def test_reach_level_80_needs_all_fourteen_progressive_level_caps(self) -> None:
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(progressive_caps), 14)
        self.collect(progressive_caps[:13])
        self.assertFalse(self.can_reach_location("Reach Level 80"))
        self.collect(progressive_caps[13:])
        self.assertTrue(self.can_reach_location("Reach Level 80"))

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

    def test_reach_level_10_and_below_need_no_progressive_level_cap(self) -> None:
        # M4.9: levels 1-10 are already within STARTING_LEVEL_CAP (10), so
        # they need zero Progressive Level Cap copies -- unlike the old
        # DK-safety-collapsed threshold (9 copies), the standard track's own
        # natural math applies now that Death Knight no longer shares this
        # track.
        self.assertTrue(self.can_reach_location("Reach Level 1"))
        self.assertTrue(self.can_reach_location("Reach Level 10"))

    def test_reach_level_55_needs_nine_progressive_level_caps(self) -> None:
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.collect(progressive_caps[:8])
        self.assertFalse(self.can_reach_location("Reach Level 55"))
        self.collect(progressive_caps[8:9])
        self.assertTrue(self.can_reach_location("Reach Level 55"))


class TestSprintGoal(WoWTestBase):
    def test_sprint_goal_requires_ten_of_fourteen_progressive_level_caps(self) -> None:
        """M4.9: Progressive Level Cap's total pooled copy count grew from
        10 to 14 (core_loop.yaml, to support the every-level milestone
        track's own level-80 ceiling), but Sprint's own goal is still
        level 60 -- goals.py's _set_completion_rule_sprint now derives the
        real level-60 threshold (10) instead of requiring ALL copies, so
        the remaining 4 copies are collectible but not required to win.

        Note: WorldTestBase.collect_by_name collects *every* matching item
        in the pool in one call (it is not "collect one copy"), so to
        exercise the 9-vs-10 boundary we must collect specific item objects
        directly via self.collect() rather than calling collect_by_name in
        a loop.
        """
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(progressive_caps), 14)
        self.collect(progressive_caps[:9])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect(progressive_caps[9:10])
        self.assertTrue(self.multiworld.completion_condition[self.player](state))

    def test_core_loop_item_pool_matches_expected_total(self) -> None:
        # M4.9: 14 Progressive Level Cap copies (was 10) + 7 unconditional
        # unlock items (Ragefire Chasm, Deadmines, Dark Portal, Northrend
        # Passage, Molten Core, Sunwell Plateau, Icecrown Citadel) = 21.
        # This is a real, deliberate total -- NOT derived from the standard
        # track's own 85-location count (80 level milestones + 5 instance
        # clears): Progressive Level Cap copies and "Reach Level N"
        # locations are two independently-sized things that happened to
        # both equal 17 under the old every-5-levels granularity by
        # coincidence, not by any enforced invariant.
        core_loop_item_count = sum(count for _, count in core_loop_content_data.ITEMS.values())
        self.assertEqual(core_loop_item_count, 21)


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


class TestTrapsGatesAndHolidaysanityCombinedParity(WoWTestBase):
    """Task 17's parity extension to Task 11's mechanism: traps and gates
    are two independently-sized optional families sharing one filler
    ceiling (content/filler.yaml's 122 rows, grown from 73 by M4.10.1's
    per-level-milestone trap-ceiling fix). M4.10.7 (Holidaysanity) adds a
    third such family -- same "no AP location of its own" shape as gates
    and traps -- growing that shared ceiling again to 136 (122 + 14,
    Holidaysanity's own worst case: content/holidaysanity.yaml's 14 Holiday
    Unlock items, all pooled only when combo_unlocks_scope is "both").
    Stress-tests all three at their most extreme settings simultaneously
    (including combo_unlocks_scope: "both", the setting that actually
    reaches the full 37-item gates worst case AND Holidaysanity's full
    14-item worst case) -- if the combined count_enabled_gates_items() +
    count_enabled_trap_items() + count_enabled_holidaysanity_items() ever
    exceeds 136, or if the three counts are computed inconsistently between
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

    def test_holidaysanity_is_actually_maxed_out_by_this_class_s_options(self) -> None:
        # Confirms this class's existing options dict (unchanged from its
        # pre-M4.10.7 gates/traps-only form) really does reach
        # Holidaysanity's own worst case too, so the parity test above is
        # exercising all three families' combined ceiling, not just two of
        # three.
        from .. import items as items_module
        self.assertEqual(items_module.count_enabled_holidaysanity_items(self.world), 14)

    def test_all_quest_locations_still_reachable_with_zero_items(self) -> None:
        # Traps carry no access rule and gate no location -- sphere-0 safety
        # should be unaffected by traps_enabled, same guarantee
        # TestGateItemSphereZero already covers for the gate family alone.
        for name in quest_rewards_content_data.ALWAYS_PRESENT:
            self.assertTrue(self.can_reach_location(name))


class TestFillerPoolCoversWorstCaseGatesAndTraps(unittest.TestCase):
    """M4.9.5 final review (Fix 12): TestTrapsGatesAndHolidaysanityCombinedParity
    above (renamed by M4.10.7 when Holidaysanity joined it) is
    the one test that would normally prove this milestone's most
    safety-critical invariant (enough filler locations exist for the
    worst-case combination of gate items + trap items) -- but it's
    currently red for an unrelated, pre-existing reason: an earlier,
    separate, still-in-progress milestone (M4.9.3) changed level milestones
    to per-level, which changed items.py's _trap_baseline_location_count()'s
    real return value away from the number content/filler.yaml's row count
    was last sized against (see filler.yaml's own header comment for the
    full explanation). That drift is out of scope for this plan to fix.

    This test asserts the same real invariant WITHOUT depending on a full
    seed generation succeeding, using the exact same real
    _trap_baseline_location_count function count_enabled_trap_items relies
    on (not a hardcoded guess), so it stays honest about whether the
    invariant actually holds today. It is EXPECTED to currently FAIL for
    the same known, out-of-scope M4.9.3 drift -- that is this test
    correctly surfacing a real, already-known gap, not a bug in this
    test. Do not "fix" this test by changing the filler pool size; that
    belongs to whichever effort is already tracking the M4.9.3 drift."""

    def test_filler_pool_covers_worst_case_gates_and_traps(self) -> None:
        from .. import filler_content_data, gates_content_data
        from .. import items as items_module

        max_gate_items = len(gates_content_data.ITEMS)

        # Worst case trap count: trap_percentage_of_filler at its Range max
        # (100), whichever track's baseline location count is larger --
        # reuse the same real _trap_baseline_location_count function
        # count_enabled_trap_items itself calls, for both tracks, rather
        # than recomputing or guessing the totals ourselves.
        standard_world = types.SimpleNamespace(options=types.SimpleNamespace(death_knight_slot=False))
        dk_world = types.SimpleNamespace(options=types.SimpleNamespace(death_knight_slot=True))
        max_trap_items = max(
            items_module._trap_baseline_location_count(standard_world),
            items_module._trap_baseline_location_count(dk_world),
        )

        self.assertGreaterEqual(len(filler_content_data.LOCATIONS), max_gate_items + max_trap_items)


class TestDeathKnightOptionsExistAndDefaultOff(WoWTestBase):
    def test_death_knight_slot_defaults_false(self) -> None:
        self.assertFalse(bool(self.multiworld.worlds[self.player].options.death_knight_slot))

    def test_death_knight_level1_start_defaults_false(self) -> None:
        self.assertFalse(bool(self.multiworld.worlds[self.player].options.death_knight_level1_start))

    def test_neither_option_is_mirrored_to_slot_data(self) -> None:
        # M4.9: death_knight_slot is a pure generation-time signal (which
        # locations even exist) -- the C++ level hook reads the real player
        # class instead (Task 4), so there is nothing for it to read from
        # slot_data. death_knight_level1_start is realm-wide config-sync
        # bookkeeping only (Task 6) -- same "not mirrored" precedent as
        # starting_choice.
        data = self.multiworld.worlds[self.player].fill_slot_data()
        self.assertNotIn("death_knight_slot", data)
        self.assertNotIn("death_knight_level1_start", data)


class TestDeathKnightSlotLevelMilestoneTracks(WoWTestBase):
    """M4.9 spec Sec6: a Death-Knight-flagged slot's location set must
    exclude every sub-55 standard-track location and include the 55-80
    Death Knight track instead. Also a real-generation item=location parity
    check for the death_knight track specifically (TestGateItemSphereZero's
    sibling for this option, at the other end of core_loop's own track
    axis)."""

    options = {"death_knight_slot": True}

    def test_sub_55_standard_locations_are_absent(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for level in range(1, 55):
            self.assertNotIn(f"Reach Level {level}", location_names)

    def test_death_knight_track_55_to_80_is_present(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for level in range(55, 81):
            self.assertIn(f"Reach Level {level} (Death Knight)", location_names)

    def test_standard_track_55_to_80_is_absent(self) -> None:
        # Confirms the two tracks are genuinely exclusive for this slot --
        # not just "the DK track was added on top of the standard one".
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for level in range(55, 81):
            self.assertNotIn(f"Reach Level {level}", location_names)

    def test_core_loop_location_count_is_thirty_one(self) -> None:
        # 26 death_knight level milestones (55-80) + 5 instance clears.
        core_loop_names = set(core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK["death_knight"].values()) | set(
            core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES.values()
        )
        present = {loc.name for loc in self.multiworld.get_locations(self.player)} & core_loop_names
        self.assertEqual(len(present), 31)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        # Real-generation parity check (spec Sec6): the DK track's own
        # location count (31 core-loop + whatever optional categories this
        # generation sampled) must exactly equal the pooled item count --
        # same invariant TestGateItemSphereZero/TestNorthshireGeneration
        # already enforce for the standard track's default configuration.
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestStandardSlotLevelMilestoneTracks(WoWTestBase):
    """Complement to TestDeathKnightSlotLevelMilestoneTracks above: a
    default (death_knight_slot off) slot gets the full 1-80 standard track
    and none of the death_knight track. This is also exercised implicitly
    by every other default-options test in this file, but this class makes
    the track-exclusivity property explicit and directly comparable to its
    DK-flagged sibling."""

    def test_full_standard_track_is_present(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for level in range(1, 81):
            self.assertIn(f"Reach Level {level}", location_names)

    def test_death_knight_track_is_entirely_absent(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for level in range(55, 81):
            self.assertNotIn(f"Reach Level {level} (Death Knight)", location_names)

    def test_core_loop_location_count_is_eighty_five(self) -> None:
        # 80 standard level milestones (1-80) + 5 instance clears.
        core_loop_names = set(core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK["standard"].values()) | set(
            core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES.values()
        )
        present = {loc.name for loc in self.multiworld.get_locations(self.player)} & core_loop_names
        self.assertEqual(len(present), 85)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))
