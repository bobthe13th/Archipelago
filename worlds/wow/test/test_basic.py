# Archipelago/worlds/wow/test/test_basic.py
import types
import unittest

from .bases import WoWTestBase
from .. import quest_rewards_content_data
from .. import core_loop_content_data
from .. import traps_content_data
from .. import golden_boar_statues_content_data


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
        slot's real, track-aware core-loop LOCATION count (88 for the
        standard track, 34 for death_knight as of M4.11.1 Task 4's 3 new
        instance clears -- was 85/31), a hard pre-existing item==location
        parity invariant this apworld enforces per family.
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
        regenerated.

        M4.11.4.2 (final review fix wave 2, Fix 4): Progressive Mining/
        Herbalism are pure items-only content too, same "no location of its
        own" shape as Holidaysanity -- unconditional (no enable/disable
        option), so all 12 real copies (this checkout's real
        zone_pool_credit content: 6 tiers x 2 professions) are always
        pooled. This formula previously had no term for them at all, so it
        under-counted the real itempool by exactly 12 the moment Task 5
        regenerated real gathering_node content -- caught by this test
        going red in the whole-milestone final review's full local pytest
        run. Computed via count_gathering_skill_progression_items (items.py)
        rather than hardcoding 12, so this stays correct if Gathersanity's
        content is ever regenerated with a different real tier spread."""
        from .. import density
        from .. import quest_rewards_content_data
        from .. import vendor_stock_content_data
        from ..items import count_enabled_holidaysanity_items, count_gathering_skill_progression_items
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
        gathering_skill_progression_count = count_gathering_skill_progression_items(self.world)
        expected = (
            fixed_count + always_present_count + quest_reward_sampled
            + vendor_stock_always_present_count + vendor_stock_sampled
            + holidaysanity_default_count + gathering_skill_progression_count
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

    def test_reach_level_80_needs_all_seventy_progressive_level_caps(self) -> None:
        # M4.11.1 (Task 3): LEVEL_CAP_STEP dropped from 5 to 1, so the
        # standard track's total grew from 14 to 70 (LEVEL_CAP_TOTAL_BY_TRACK
        # ["standard"] == 80 - 10 == 70) -- same "hold ALL copies to reach
        # the ceiling" invariant, just a bigger raw copy count.
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(progressive_caps), 70)
        self.collect(progressive_caps[:69])
        self.assertFalse(self.can_reach_location("Reach Level 80"))
        self.collect(progressive_caps[69:])
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
        # M4.9: levels 1-10 are already within the standard track's starting
        # cap (STARTING_LEVEL_CAP_BY_TRACK["standard"] == 10, M4.11.1), so
        # they need zero Progressive Level Cap copies -- unlike the old
        # DK-safety-collapsed threshold (9 copies), the standard track's own
        # natural math applies now that Death Knight no longer shares this
        # track.
        self.assertTrue(self.can_reach_location("Reach Level 1"))
        self.assertTrue(self.can_reach_location("Reach Level 10"))

    def test_reach_level_55_needs_forty_five_progressive_level_caps(self) -> None:
        # M4.11.1 (Task 3): (55 - 10) / 1 == 45 copies (was 9 at step 5).
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.collect(progressive_caps[:44])
        self.assertFalse(self.can_reach_location("Reach Level 55"))
        self.collect(progressive_caps[44:45])
        self.assertTrue(self.can_reach_location("Reach Level 55"))


class TestSprintGoal(WoWTestBase):
    def test_sprint_goal_requires_fifty_of_seventy_progressive_level_caps(self) -> None:
        """M4.11.1 (Task 3): LEVEL_CAP_STEP dropped from 5 to 1, so
        Progressive Level Cap's total pooled copy count grew from 14 to 70
        (core_loop.yaml, to support the every-level milestone track's own
        level-80 ceiling), but Sprint's own goal is still level 60 --
        goals.py's _set_completion_rule_sprint now derives the real
        level-60 threshold ((60 - 10) / 1 == 50) instead of requiring ALL
        copies, so the remaining 20 copies are collectible but not required
        to win.

        Note: WorldTestBase.collect_by_name collects *every* matching item
        in the pool in one call (it is not "collect one copy"), so to
        exercise the 49-vs-50 boundary we must collect specific item objects
        directly via self.collect() rather than calling collect_by_name in
        a loop.
        """
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(progressive_caps), 70)
        self.collect(progressive_caps[:49])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect(progressive_caps[49:50])
        self.assertTrue(self.multiworld.completion_condition[self.player](state))

    def test_core_loop_item_pool_matches_expected_total(self) -> None:
        # M4.11.1 (Task 3): 70 Progressive Level Cap copies (was 14, since
        # LEVEL_CAP_STEP dropped from 5 to 1: LEVEL_CAP_TOTAL_BY_TRACK
        # ["standard"] == 80 - 10 == 70) + 10 unconditional unlock items
        # (Ragefire Chasm, Deadmines, Dark Portal, Northrend Passage, Molten
        # Core, Sunwell Plateau, Icecrown Citadel, Wailing Caverns, Razorfen
        # Kraul, Razorfen Downs -- the last 3 added M4.11.1 Task 4 for
        # BarrensBeater) = 80. This is a real, deliberate total -- NOT
        # derived from the standard track's own 88-location count (80 level
        # milestones + 8 instance clears): Progressive Level Cap copies and
        # "Reach Level N" locations are two independently-sized things that
        # happen to be close under the new step-1 granularity, not by any
        # enforced invariant.
        core_loop_item_count = sum(count for _, count in core_loop_content_data.ITEMS.values())
        self.assertEqual(core_loop_item_count, 80)


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
    M4.11.1 (Task 4, BarrensBeater) grew it again to 139 (136 + 3): adding
    Wailing Caverns/Razorfen Kraul/Razorfen Downs to core_loop.yaml's
    INSTANCE_CLEAR_LOCATIONS (5 -> 8) raised the trap ceiling
    (_trap_baseline_location_count) from 85 to 88, per filler.yaml's own
    trip-wire note anticipating exactly this kind of core_loop growth.
    M4.11.4.2 (final review fix wave, Fix 4) grew it again to 151 (139 +
    12): Progressive Mining/Herbalism are a fourth "no AP location of its
    own" family (count_gathering_skill_progression_items), unconditional
    like Holidaysanity -- see
    TestFillerPoolCoversWorstCaseGatesTrapsHolidaysanityAndGatheringSkillProgression
    for the dedicated trip-wire.
    Stress-tests all three (gates/traps/Holidaysanity) at their most extreme
    settings simultaneously (including combo_unlocks_scope: "both", the
    setting that actually reaches the full 37-item gates worst case AND
    Holidaysanity's full 14-item worst case) -- if the combined
    count_enabled_gates_items() + count_enabled_trap_items() +
    count_enabled_holidaysanity_items() + count_gathering_skill_progression_items()
    ever exceeds 151, or if the counts are computed inconsistently between
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


class TestFillerPoolCoversWorstCaseGatesTrapsHolidaysanityAndGatheringSkillProgression(unittest.TestCase):
    """M4.9.5 final review (Fix 12): TestTrapsGatesAndHolidaysanityCombinedParity
    above (renamed by M4.10.7 when Holidaysanity joined it) is
    the one test that would normally prove this milestone's most
    safety-critical invariant (enough filler locations exist for the
    worst-case combination of gate items + trap items + Holidaysanity
    items) -- but it's
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
    belongs to whichever effort is already tracking the M4.9.3 drift.

    M4.11.4.2 (final review fix wave 2, Fix 4): renamed again (class and
    method) and gained a 4th term, count_gathering_skill_progression_items --
    Progressive Mining/Herbalism are unconditional (no enable/disable option,
    same shape as Holidaysanity), and this class's own assertion had not
    been taught about them, so it kept passing (139 >= 139) even after the
    real `needed` total in locations.py's create_filler_locations grew past
    content/filler.yaml's actual row count by exactly 12 -- the drift this
    trip-wire exists to catch. See filler.yaml's own header comment for the
    matching 139 -> 151 row-count resize."""

    def test_filler_pool_covers_worst_case_gates_traps_holidaysanity_and_gathering_skill_progression(self) -> None:
        from .. import filler_content_data, gates_content_data, holidaysanity_content_data
        from .. import items as items_module

        max_gate_items = len(gates_content_data.ITEMS)

        # M4.10.7 final review fix (I1): Holidaysanity has NO enable/disable
        # option -- create_holidaysanity_item_pool contributes to every
        # seed, and its worst case is the full ITEMS count (all 14, i.e.
        # combo_unlocks_scope wide enough to include the 5 gated holidays).
        # Only the docstring above was updated for M4.10.7; the assertion
        # below was still under-checking by these 14 items.
        max_holidaysanity_items = len(holidaysanity_content_data.ITEMS)

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

        # M4.11.4.2: also unconditional (no enable/disable option), same
        # shape as Holidaysanity above -- count_gathering_skill_progression_items
        # ignores `world` entirely today (kept for signature consistency, see
        # its own docstring), so any world works here.
        max_gathering_skill_items = items_module.count_gathering_skill_progression_items(standard_world)

        self.assertGreaterEqual(
            len(filler_content_data.LOCATIONS),
            max_gate_items + max_trap_items + max_holidaysanity_items + max_gathering_skill_items,
        )


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

    def test_core_loop_location_count_is_thirty_four(self) -> None:
        # 26 death_knight level milestones (55-80) + 8 instance clears
        # (M4.11.1 Task 4 grew this from 5 to 8: Wailing Caverns, Razorfen
        # Kraul, Razorfen Downs added for BarrensBeater).
        core_loop_names = set(core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK["death_knight"].values()) | set(
            core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES.values()
        )
        present = {loc.name for loc in self.multiworld.get_locations(self.player)} & core_loop_names
        self.assertEqual(len(present), 34)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        # Real-generation parity check (spec Sec6): the DK track's own
        # location count (34 core-loop + whatever optional categories this
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

    def test_core_loop_location_count_is_eighty_eight(self) -> None:
        # 80 standard level milestones (1-80) + 8 instance clears (M4.11.1
        # Task 4 grew this from 5 to 8: Wailing Caverns, Razorfen Kraul,
        # Razorfen Downs added for BarrensBeater).
        core_loop_names = set(core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK["standard"].values()) | set(
            core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES.values()
        )
        present = {loc.name for loc in self.multiworld.get_locations(self.player)} & core_loop_names
        self.assertEqual(len(present), 88)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestZoneLevelerBarrensLevelTrack(WoWTestBase):
    """M4.11.1 (Task 9): Zone Leveler's own Barrens level-cap track (levels
    11-30) must be gated by Progressive Level Cap copies the same way as
    the standard/death_knight tracks, and a zone_leveler slot must create
    only Barrens' own three curated instance-clear locations (Wailing
    Caverns, Razorfen Kraul, Razorfen Downs) -- not all 8 of core_loop's
    real instances (that full set is what standard/death_knight slots get;
    see TestStandardSlotLevelMilestoneTracks/TestDeathKnightSlotLevelMilestoneTracks
    above).

    zone_leveler_goals is narrowed to reach_zone_level_cap alone (Task 11):
    this class is only about level-cap/instance-clear LOCATION structure,
    not full goal-completion semantics (see test_goals.py's own
    TestZoneLeveler* classes for that). Left at its default (all four goal
    kinds ANDed), WoWTestBase's own generic beatable-game check (run
    automatically for every WoWTestBase subclass, per bases.py's own
    docstring) would also require clear_all_zone_quests' full item set --
    but WoWTestBase's fast-test default zeroes quest_reward_weight, so none
    of Barrens' own quest-reward locations/items would ever be pooled,
    making that goal permanently unsatisfiable and this class's own
    unrelated location-structure tests collaterally unbeatable."""

    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
    }

    def test_reach_level_30_needs_twenty_of_the_pooled_progressive_level_caps(self) -> None:
        # Finding 10 correction (final whole-branch review, 2026-09-01):
        # Progressive Level Cap's pooled copy count is now genuinely
        # per-track (core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK), not
        # flat/track-independent as this test used to assert -- pooling the
        # standard track's flat 70 for zone_leveler_barrens too let a
        # BarrensBeater realm's level cap walk all the way to 80, well past
        # its own intended level-30 ceiling. zone_leveler_barrens pools
        # exactly LEVEL_CAP_TOTAL_BY_TRACK["zone_leveler_barrens"] == 20 (its
        # own 30 - 10 threshold, unchanged), exercised here the same
        # "collect N-1, then the Nth" way
        # TestCoreLoopAccessRules.test_reach_level_55_needs_forty_five_progressive_level_caps
        # does for the standard track.
        caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(caps), 20)
        self.collect(caps[:19])
        self.assertFalse(self.can_reach_location("Reach Level 30 (Zone Leveler)"))
        self.collect(caps[19:20])
        self.assertTrue(self.can_reach_location("Reach Level 30 (Zone Leveler)"))

    def test_barrens_track_creates_only_its_three_curated_instances(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Clear Wailing Caverns", names)
        self.assertIn("Clear Razorfen Kraul", names)
        self.assertIn("Clear Razorfen Downs", names)
        self.assertNotIn("Clear Molten Core", names)
        self.assertNotIn("Clear Ragefire Chasm", names)
        self.assertNotIn("Clear Deadmines", names)
        self.assertNotIn("Clear Sunwell Plateau", names)
        self.assertNotIn("Clear Icecrown Citadel", names)

    def test_standard_and_death_knight_tracks_are_entirely_absent(self) -> None:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        for level in range(1, 81):
            self.assertNotIn(f"Reach Level {level}", names)
        for level in range(55, 81):
            self.assertNotIn(f"Reach Level {level} (Death Knight)", names)

    def test_core_loop_location_count_is_twenty_three(self) -> None:
        # 20 zone_leveler_barrens level milestones (11-30) + 3 curated
        # instance clears (Wailing Caverns, Razorfen Kraul, Razorfen Downs).
        core_loop_names = set(
            core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK["zone_leveler_barrens"].values()
        ) | {
            core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES[key]
            for key in ("wailing_caverns", "razorfen_kraul", "razorfen_downs")
        }
        present = {loc.name for loc in self.multiworld.get_locations(self.player)} & core_loop_names
        self.assertEqual(len(present), 23)


class TestGoldenBoarStatues(WoWTestBase):
    """M4.11.1 (Task 10): golden_boar_statues.yaml's 20 curated Barrens
    rare-kill locations, and the "Golden Boar Statue" item pool that must
    exactly parallel however many of them got density-sampled -- same
    location/item parity shape TestSprintGoal and the Key Hunt tests use for
    rares_content_data. check_density: 100 forces
    density.predict_sample_size(20 rows, weight 100) to ceil(20*1*1) == 20,
    i.e. every curated row, so both tests below can assert against the full
    roster size rather than a random subset.

    zone_leveler_goals is narrowed to golden_boar_statues alone (Task 11):
    this class is only about statue location/item parity, not full
    goal-completion semantics (see test_goals.py's own TestZoneLeveler*
    classes for that). Left at its default (all four goal kinds ANDed),
    WoWTestBase's own generic beatable-game check would also require
    clear_all_zone_quests' full item set -- but WoWTestBase's fast-test
    default zeroes quest_reward_weight, so none of Barrens' own
    quest-reward locations/items would ever be pooled, making that goal
    permanently unsatisfiable and this class's own unrelated statue tests
    collaterally unbeatable."""

    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "check_density": 100,
        "zone_leveler_goals": {"golden_boar_statues"},
    }

    def test_all_curated_statue_locations_sampled_at_density_100(self) -> None:
        names = {
            loc.name for loc in self.multiworld.get_locations(self.player)
            if loc.name.startswith("Golden Boar Statue Kill:")
        }
        self.assertEqual(len(names), len(golden_boar_statues_content_data.LOCATIONS))

    def test_statue_item_count_matches_sampled_location_count(self) -> None:
        statues = self.get_items_by_name("Golden Boar Statue")
        statue_locations = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name.startswith("Golden Boar Statue Kill:")
        ]
        self.assertEqual(len(statues), len(statue_locations))


class TestZoneLevelerExcludesIrrelevantCoreLoopItems(WoWTestBase):
    """M4.11.2 (fix round 1, controller ruling): zone_leveler excludes only
    5 core_loop items -- the non-curated raid/dungeon instance unlocks
    (Ragefire Chasm, Deadmines, Molten Core, Sunwell Plateau, Icecrown
    Citadel) -- because none of them has a matching location anywhere in a
    zone_leveler slot (distinct from the 3 curated Barrens instances, which
    stay pooled and are asserted present below).

    Dark Portal Access and Northrend Passage are deliberately NOT excluded,
    despite superficially looking like the same kind of "irrelevant to a
    zone-locked character" item (they too "enable travel outside the
    starting zone"). The original commit (c7e09e3d) excluded all 7 on that
    premise, but the premise is factually wrong for these 2: rules.py gates
    Enemysanity's non-vanilla-tagged (tbc/wotlk) creature-kill locations on
    state.has("Dark Portal Access", ...) / state.has("Northrend Passage",
    ...), with no zone_leveler exemption, and Enemysanity remains fully
    pool-eligible and completely zone-unrestricted this milestone (its own
    zone-tagging is Phase 2, out of scope for the whole M4.11.2 milestone).
    fish_content_data.py also gates Northrend fish behind "Northrend
    Passage". At real production-default pools, excluding these 2 items
    makes thousands of already-pooled Enemysanity locations permanently
    unreachable -- see TestZoneLevelerCoreLoopExclusionEnemysanityReachability
    below, which reproduces that exact scenario via this suite's normal
    test_fill/test_all_state_can_reach_everything convention."""
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
    }

    _EXCLUDED_ITEM_NAMES = frozenset({
        "Instance Unlock: Ragefire Chasm",
        "Instance Unlock: Deadmines",
        "Instance Unlock: Molten Core",
        "Instance Unlock: Sunwell Plateau",
        "Instance Unlock: Icecrown Citadel",
    })

    def test_excluded_items_absent_from_pool(self) -> None:
        item_names = {item.name for item in self.multiworld.itempool if item.player == self.player}
        self.assertTrue(self._EXCLUDED_ITEM_NAMES.isdisjoint(item_names))

    def test_barrens_curated_instance_unlocks_still_present(self) -> None:
        item_names = {item.name for item in self.multiworld.itempool if item.player == self.player}
        for name in (
            "Instance Unlock: Wailing Caverns",
            "Instance Unlock: Razorfen Kraul",
            "Instance Unlock: Razorfen Downs",
        ):
            self.assertIn(name, item_names)

    def test_dark_portal_access_and_northrend_passage_still_present(self) -> None:
        # Regression guard for the Critical finding: these 2 items look
        # superficially similar to the 5 excluded instance unlocks but must
        # remain pooled unconditionally under zone_leveler -- see this
        # class's own docstring for why.
        item_names = {item.name for item in self.multiworld.itempool if item.player == self.player}
        self.assertIn("Dark Portal Access", item_names)
        self.assertIn("Northrend Passage", item_names)

    def test_progressive_level_cap_still_present(self) -> None:
        item_names = {item.name for item in self.multiworld.itempool if item.player == self.player}
        self.assertIn("Progressive Level Cap", item_names)

    def test_item_location_parity_still_holds(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestZoneLevelerCoreLoopExclusionEnemysanityReachability(WoWTestBase):
    """Genuine regression test for the Critical finding above: reproduces
    the reviewer's real scenario by generating a zone_leveler slot with
    Enemysanity's pools left at their REAL production defaults (both
    OptionSets' own `default = valid_keys`, i.e. every type/expansion
    tier) rather than WoWTestBase.world_setup's normal zeroed-for-speed
    defaults -- deliberately overridden here since that's exactly the
    combination the reviewer showed breaks generation if Dark Portal
    Access/Northrend Passage were ever excluded again. No custom
    reachability test method is needed: WoWTestBase's automatically-run
    test_fill/test_all_state_can_reach_everything (test/bases.py) already
    fail with an "Unreachable locations" assertion if any pooled
    Enemysanity location can never be reached -- same convention
    test_quest_rewards.py/test_vendor_stock.py already rely on for their
    own full-generation reachability coverage."""
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
        "enemysanity_type_pools": {"boss", "regular"},
        "enemysanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
    }


class TestZoneLevelerZoneDataFlattened(unittest.TestCase):
    def test_barrens_area_tags_is_just_barrens(self) -> None:
        from worlds.wow import zone_leveler_content_data
        zone_data = zone_leveler_content_data.ZONES["barrens"]
        self.assertEqual(zone_data.area_tags, frozenset({"barrens"}))

    def test_barrens_no_longer_has_zone_id_or_allowed_hub_zone_ids_fields(self) -> None:
        from worlds.wow import zone_leveler_content_data
        zone_data = zone_leveler_content_data.ZONES["barrens"]
        self.assertFalse(hasattr(zone_data, "zone_id"))
        self.assertFalse(hasattr(zone_data, "allowed_hub_zone_ids"))

    def test_instance_keys_computed_from_real_entrance_data_includes_known_three(self) -> None:
        from worlds.wow import zone_leveler_content_data
        zone_data = zone_leveler_content_data.ZONES["barrens"]
        self.assertIn("wailing_caverns", zone_data.instance_keys)
        self.assertIn("razorfen_kraul", zone_data.instance_keys)
        self.assertIn("razorfen_downs", zone_data.instance_keys)
