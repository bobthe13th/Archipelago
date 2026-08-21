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


class TestQuestRewardsRules(WoWTestBase):
    # check_density: 100, max_optional_locations: 5000 against quest_rewards'
    # 3,735 real rows guarantees every row -- including the specific
    # min_level=20 location this test depends on -- is sampled into the
    # pool, so this test doesn't depend on random sampling picking it.
    options = {"game_mode": "sprint", "include_quest_rewards": True, "check_density": 100, "max_optional_locations": 5000}

    # "Quest: Morbent Fel Reward (#55)" has trigger.min_level == 20 in the
    # real DB-extracted content/quest_rewards.yaml (quest_id 55). With
    # core_loop's STARTING_LEVEL_CAP=10 and LEVEL_CAP_STEP=5, that requires
    # ceil((20-10)/5) == 2 Progressive Level Cap copies -- picked because
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
        self.collect(progressive_caps[:1])
        self.assertFalse(self.can_reach_location(self._GATED_LOCATION))
        self.collect(progressive_caps[1:2])
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
    """Task 3's OptionalCategory registry -- and IncludeQuestRewards' own
    docstring -- both claim Quest Rewards works in EVERY game mode, not just
    Sprint. Every other test in this file only ever exercises Sprint, so
    nothing prior to this class actually ran the family, its rule (whose
    total_caps clamp assumes core_loop's Progressive Level Cap item pool is
    always 10 regardless of mode -- true because create_core_loop_item_pool
    is called unconditionally in create_items, but never checked from the
    Quest Rewards side), or its registry's interaction with an existing
    mode-owned sampler, under any other mode. Key Hunt is the sharpest case:
    it's the one other mode whose own create_rares_locations also samples
    through density and sets world.key_hunt_sampled_rare_count as a side
    effect, so this is the one place the new registry and the pre-existing
    sampler actually run side by side. WoWTestBase's default test_fill/
    test_all_state_can_reach_everything already cover full-generation
    reachability for this option combination; this class adds the parity/
    presence checks those defaults don't."""

    options = {
        "game_mode": "key_hunt",
        "include_quest_rewards": True,
        "check_density": 100,
        "max_optional_locations": 5000,
    }

    def test_quest_reward_locations_exist_in_key_hunt_mode(self) -> None:
        quest_reward_locations = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name in quest_rewards_content_data.LOCATIONS
        ]
        self.assertTrue(len(quest_reward_locations) > 0)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))
