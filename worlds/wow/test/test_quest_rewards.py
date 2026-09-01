# Archipelago/worlds/wow/test/test_quest_rewards.py
import re
import unittest

from BaseClasses import Location

from .bases import WoWTestBase
from .. import quest_rewards_content_data


class TestQuestRewardsRowAlignment(unittest.TestCase):
    """items.py's create_optional_category_item_pool (M4.5 Task 3 fix) pairs
    a sampled location to its reward item by ROW INDEX, not by name --
    confirmed necessary because LOCATIONS/ITEMS use different name prefixes
    for the same row ("Quest: X Reward (#N)" vs "Quest Reward: X (#N)").
    That pairing is only correct if LOCATIONS and ITEMS are emitted in the
    same row order. Nothing else in this suite can observe an order
    mismatch -- length parity and fill would both still pass even if row 5's
    location paired with row 900's item -- so this test pins the ordering
    invariant directly by cross-checking the shared quest-id suffix "(#N)"
    both names carry."""

    def test_locations_and_items_are_row_order_aligned_by_quest_id(self) -> None:
        location_names = list(quest_rewards_content_data.LOCATIONS)
        item_names = list(quest_rewards_content_data.ITEMS)
        self.assertEqual(len(location_names), len(item_names))
        for index, (location_name, item_name) in enumerate(zip(location_names, item_names)):
            location_quest_id = re.search(r"\(#(\d+)\)$", location_name).group(1)
            item_quest_id = re.search(r"\(#(\d+)\)$", item_name).group(1)
            self.assertEqual(
                location_quest_id, item_quest_id,
                f"row {index}: location {location_name!r} (#{location_quest_id}) does not "
                f"align with item {item_name!r} (#{item_quest_id})",
            )


class TestQuestRewardsAlwaysPresentSet(unittest.TestCase):
    """ALWAYS_PRESENT is a Death-Knight-reachability safety invariant (see
    rules.py's own comments): these 19 specific Northshire/Goldshire
    starting-quest locations must be present regardless of player
    tag/weight options. Every other test in this suite either uses
    fake/mocked data or iterates ALWAYS_PRESENT dynamically, so none of
    them would notice if a future extraction bug silently shrank or
    emptied the real generated set -- the whole suite would stay green,
    self-consistently, with no signal at all. This test hardcodes the real
    quest_rewards_content_data.ALWAYS_PRESENT value directly so a
    regression here fails loudly."""

    def test_always_present_has_the_19_dk_reachability_rows(self) -> None:
        self.assertEqual(
            quest_rewards_content_data.ALWAYS_PRESENT,
            frozenset({
                "Quest: Bounty on Garrick Padfoot Reward (#6)",
                "Quest: Kobold Camp Cleanup Reward (#7)",
                "Quest: Investigate Echo Ridge Reward (#15)",
                "Quest: Brotherhood of Thieves Reward (#18)",
                "Quest: Skirmish at Echo Ridge Reward (#21)",
                "Quest: Wolves Across the Border Reward (#33)",
                "Quest: Report to Goldshire Reward (#54)",
                "Quest: A Threat Within Reward (#783)",
                "Quest: Simple Letter Reward (#3100)",
                "Quest: Consecrated Letter Reward (#3101)",
                "Quest: Encrypted Letter Reward (#3102)",
                "Quest: Hallowed Letter Reward (#3103)",
                "Quest: Glyphic Letter Reward (#3104)",
                "Quest: Tainted Letter Reward (#3105)",
                "Quest: Milly Osworth Reward (#3903)",
                "Quest: Milly's Harvest Reward (#3904)",
                "Quest: Grape Manifest Reward (#3905)",
                "Quest: Eagan Peltskinner Reward (#5261)",
                "Quest: In Favor of the Light Reward (#5623)",
            }),
        )


class TestQuestRewardsRules(WoWTestBase):
    # check_density: 100 with quest_reward_weight: 100 (explicit -- see
    # bases.py's WoWTestBase.world_setup, which now defaults BOTH
    # quest_reward_weight/vendor_stock_weight to 0 for any class that
    # doesn't state them explicitly, so "leave it unset to inherit the
    # option's own real default" no longer works and must be spelled out)
    # against quest_rewards' real rows guarantees every row -- including
    # the specific min_level=20 location this test depends on -- is sampled
    # into the pool, so this test doesn't depend on random sampling picking
    # it. Unlike the other test classes in this file (see
    # TestQuestRewardsAvailableOutsideSprint below), this one genuinely
    # needs full-table coverage for correctness, not just "a real sample"
    # -- world_setup's MultiWorld.set_seed(None) picks a fresh random seed
    # every run, so any weight below 100 would make
    # test_min_level_rule_blocks_until_level_cap_items_held's dependency on
    # one specific named location genuinely flaky (present only ~weight% of
    # runs), not just slower.
    # vendor_stock_weight: 0 -- this class has nothing to do with
    # vendor_stock; without capping it explicitly it ALSO defaults to 100
    # via check_density: 100 above, meaning this test was silently filling
    # the full ~37,750-row vendor_stock table on top of quest_rewards'
    # ~9,220 rows every run -- a combined ~47,000-row fill that made even
    # this one test class take upwards of 15+ minutes (confirmed
    # empirically). Capping only vendor_stock_weight (never
    # quest_reward_weight, which must stay at its real default -- see
    # above) removes that unrelated cost without touching this test's own
    # correctness requirement.
    options = {"game_mode": "sprint", "check_density": 100, "quest_reward_weight": 100, "vendor_stock_weight": 0}

    # "Quest: Morbent Fel Reward (#55)" has trigger.min_level == 20 in the
    # real DB-extracted content/quest_rewards.yaml (quest_id 55). With
    # core_loop's standard-track STARTING_LEVEL_CAP_BY_TRACK["standard"]=10
    # and LEVEL_CAP_STEP=1 (M4.11.1, was 5), that requires
    # ceil((20-10)/1) == 10 Progressive Level Cap copies -- picked because
    # it's a real, moderate (not 0, not extreme) min_level, not a
    # hand-picked edge case.
    _GATED_LOCATION = "Quest: Morbent Fel Reward (#55)"

    def test_min_level_rule_blocks_until_level_cap_items_held(self) -> None:
        # Any quest_reward location with min_level > 0 must require enough
        # Progressive Level Cap copies to reach that level, exactly the same
        # mechanism core_loop's own "Reach Level N" locations already use
        # (rules.py:40-52) -- reuse it rather than inventing a second rule
        # shape for the same underlying constraint.
        self.assertIn(self._GATED_LOCATION, quest_rewards_content_data.LOCATIONS)
        location = self.multiworld.get_location(self._GATED_LOCATION, self.player)
        # Structural check: this location must carry a REAL access rule, not
        # AP's own "always reachable" class default (Location.access_rule
        # defaults to `staticmethod(lambda state: True)`, so a naive
        # `is not None` check here would be vacuously true for EVERY
        # location, gated or not, and would pass before the rule is ever
        # implemented -- confirmed against BaseClasses.py's
        # DEFAULT_COLLECTION_RULE).
        self.assertIsNot(location.access_rule, Location.access_rule)

        # Behavioral check, the actual RED/GREEN evidence: unreachable with
        # too few Progressive Level Cap copies, reachable with enough.
        progressive_caps = self.get_items_by_name("Progressive Level Cap")
        self.collect(progressive_caps[:9])
        self.assertFalse(self.can_reach_location(self._GATED_LOCATION))
        self.collect(progressive_caps[9:10])
        self.assertTrue(self.can_reach_location(self._GATED_LOCATION))

    def test_at_least_one_location_is_min_level_gated(self) -> None:
        # Sanity check on the family as a whole (not just the one hand-picked
        # location above): with every one of the 3,735 real rows sampled in,
        # at least one quest_reward location must end up with a non-default
        # access rule.
        gated = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name.startswith("Quest:")
            and loc.name in quest_rewards_content_data.LOCATIONS
            and loc.access_rule is not Location.access_rule
        ]
        self.assertTrue(len(gated) > 0, "expected at least one min_level-gated quest reward location")


class TestQuestRewardsAvailableOutsideSprint(WoWTestBase):
    """Task 3's OptionalCategory registry -- and QuestRewardWeight's own
    docstring (M4.8.0, replacing the retired IncludeQuestRewards toggle) --
    both claim Quest Rewards works in EVERY game mode, not just Sprint.
    Every other test in this file only ever exercises Sprint, so
    nothing prior to this class actually ran the family, its rule (whose
    total_caps clamp assumes core_loop's Progressive Level Cap item pool is
    always 70 (M4.11.1, was 14) regardless of mode -- true because
    create_core_loop_item_pool is called unconditionally in create_items,
    but never checked from the Quest Rewards side), or its registry's interaction with an existing
    mode-owned sampler, under any other mode. Key Hunt is the sharpest case:
    it's the one other mode whose own create_rares_locations also samples
    through density and sets world.key_hunt_sampled_rare_count as a side
    effect, so this is the one place the new registry and the pre-existing
    sampler actually run side by side. WoWTestBase's default test_fill/
    test_all_state_can_reach_everything already cover full-generation
    reachability for this option combination; this class adds the parity/
    presence checks those defaults don't."""

    # quest_reward_weight: 10 (M4.8.0) -- unlike TestQuestRewardsRules above,
    # neither test in this class depends on any SPECIFIC named location
    # being sampled (just "at least one exists" / a general parity
    # invariant that holds at any sample size), so this doesn't need
    # QuestRewardWeight's own real-seed default of 100 (the full ~9,220-row
    # table) -- capping it keeps this class fast without weakening either
    # assertion. vendor_stock_weight: 0 -- this class has nothing to do
    # with vendor_stock at all, and without capping it explicitly it would
    # ALSO default to 100 via check_density: 100, silently filling the full
    # ~37,750-row table for no test-relevant reason.
    options = {
        "game_mode": "key_hunt",
        "check_density": 100,
        "quest_reward_weight": 10,
        "vendor_stock_weight": 0,
    }

    def test_quest_reward_locations_exist_in_key_hunt_mode(self) -> None:
        quest_reward_locations = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name in quest_rewards_content_data.LOCATIONS
        ]
        self.assertTrue(len(quest_reward_locations) > 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))
