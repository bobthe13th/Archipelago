# Archipelago/worlds/wow/test/test_basic.py
from .bases import WoWTestBase
from .. import core_loop_content_data


class TestDefault(WoWTestBase):
    options = {}


class TestNorthshireGeneration(WoWTestBase):
    def test_all_locations_reachable(self) -> None:
        """M2: all 19 curated locations must be reachable with no items required
        (matches rules.py's no-op access rules for this milestone)."""
        self.assertTrue(len(self.multiworld.get_reachable_locations()) >= 19)

    def test_item_pool_matches_location_count(self) -> None:
        """As of M2.1, create_items always adds both M2's quest-item pool
        (19) and the core-loop item pool (14): 33 total. There is no
        per-mode item pool split yet -- Sprint is the only GameMode."""
        self.assertEqual(len(self.multiworld.itempool), 33)


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
        core_loop_location_count = 12 + 2  # 12 level milestones + 2 instance clears
        self.assertEqual(core_loop_item_count, core_loop_location_count)
