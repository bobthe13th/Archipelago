# Archipelago/worlds/wow/test/test_gathersanity.py
import unittest
from unittest.mock import patch

from .bases import WoWTestBase
from .. import gathersanity_content_data
from ..locations import _OPTIONAL_CATEGORIES, _location_matches_pools


class TestGathersanityRowAlignment(unittest.TestCase):
    def test_locations_and_items_are_row_order_aligned(self) -> None:
        location_names = list(gathersanity_content_data.LOCATIONS)
        item_names = list(gathersanity_content_data.ITEMS)
        self.assertEqual(len(location_names), len(item_names))
        for location_name, item_name in zip(location_names, item_names):
            self.assertTrue(location_name.startswith("Gathersanity: "))
            self.assertTrue(item_name.startswith("Gathersanity Item: "))


class TestGathersanityExpansionPoolsFilterGatheringNode(unittest.TestCase):
    """M4.11.4.2 fix round 1: real regression test for the bug found by
    Task 5's own full-suite pytest run -- gathering_node's own
    zone_pool_credit rows used to carry NEITHER a "source" nor an
    "expansion" tag, so gathersanity_source_pools/gathersanity_expansion_
    pools silently never gated them at all (locations.py's
    _location_matches_pools treats a tag dimension entirely absent from a
    row's own TAGS entry as "doesn't apply, auto-pass" -- a real,
    deliberate M4.10.5 craftsanity precedent for a row missing ONE of two
    configured dimensions, which gathering_node rows previously violated by
    missing BOTH). The `source` half was fixed and regression-tested first
    (da70249, via a real generation in TestGathersanityRealGenerationDisenchantOnly
    below); this class covers the `expansion` half the same real bug
    exposed, fixed by extract_gathersanity.py's own new zone_to_maps
    accumulator (mirroring extract_containersanity.py's identical
    mechanism).

    Calls _location_matches_pools directly against REAL
    gathersanity_content_data (not a fake fixture module) with a fully
    fake, generation-free `world` object -- same types.SimpleNamespace
    pattern TestZoneLevelerTrainerSpellRowMatches (test_optional_
    categories.py) already establishes for this exact "pure function,
    real content, no real generation" shape. Deliberately NOT a
    WoWTestBase subclass: a real WoWTestBase world with
    gathersanity_source_pools unrestricted enough to keep the "source"
    dimension from blocking every match would also actually generate
    thousands of real wotlk-tagged gathering_node locations into this
    test's own multiworld, making its inherited test_fill/
    test_all_state_can_reach_everything slow at gathering_node's own real
    scale (same cost class this milestone's much larger families now
    impose on every unnarrowed WoWTestBase subclass -- see this task's own
    report). Skipping WoWTestBase entirely avoids paying that cost for a
    test that only needs a `world.options` object, never a real generated
    world.
    """

    @staticmethod
    def _fake_world(expansion_pools: set[str]):
        import types

        return types.SimpleNamespace(options=types.SimpleNamespace(
            gathersanity_source_pools=types.SimpleNamespace(value={"gathering_node"}),
            gathersanity_expansion_pools=types.SimpleNamespace(value=expansion_pools),
        ))

    def test_gathering_node_row_only_matches_its_own_real_expansion(self) -> None:
        category = next(c for c in _OPTIONAL_CATEGORIES if c.key == "gathersanity")
        world = self._fake_world({"wotlk"})

        def _real_gathering_node_row(expansion: str) -> str:
            return next(
                name for name, tags in gathersanity_content_data.TAGS.items()
                if "gathering_node" in tags.get("source", ()) and expansion in tags.get("expansion", ())
            )

        # A real gathering_node row confirmed vanilla-tagged (10,852 real
        # such rows as of this task's own regeneration -- guaranteed to
        # exist) must NOT match this fake world's own
        # gathersanity_expansion_pools={"wotlk"} selection -- before this
        # fix, it always matched regardless of this option (the bug).
        self.assertFalse(_location_matches_pools(world, category, _real_gathering_node_row("vanilla")))
        # A real gathering_node row confirmed wotlk-tagged (5,612 real such
        # rows) DOES match.
        self.assertTrue(_location_matches_pools(world, category, _real_gathering_node_row("wotlk")))


class TestGathersanityRealGenerationDisenchantOnly(WoWTestBase):
    """M4.10.2 final whole-branch review fix (I1): the whole family shipped
    with ZERO apworld-level test coverage of a real seed actually generating
    with Gathersanity live -- every other test covers either the extraction/
    compiler tooling in isolation or fake location/item modules
    (test_slot_data.py). That gap is exactly why finding C1
    (_AP_ITEM_DISPLAY_FAMILY_KEYS omitting "gathersanity", making the entire
    family a runtime no-op) survived seven individually-reviewed, individually
    passing implementation tasks.

    Mirrors TestContainersanityRealGenerationWotlkOnly's pattern
    (test_containersanity.py) exactly, narrowed to a small real subset to
    keep the run bounded: Gathersanity has no weight_option to zero out
    (locations.py's OptionalCategory.weight_option is None -- every
    tag-matched row is included unconditionally), so narrowing a tag pool is
    the only way to bound this class. Narrowed on the `source` dimension to
    `disenchant` alone -- 123 real rows, the smallest of the six sources, vs.
    2,302 for the whole family. `gathersanity_expansion_pools` is left at its
    full real default (all three tiers) so both AND'd dimensions are
    genuinely exercised; every one of the 123 disenchant rows carries
    `vanilla`, so that dimension does not further narrow the set here.
    Note bases.py zeroes BOTH gathersanity pools for every other test in the
    suite (a speed default), so this class must set both explicitly -- an
    unset expansion pool would silently yield zero locations and make every
    assertion below vacuous.
    """
    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": set(), "trainer_spell_class_pools": set(),
        "containersanity_expansion_pools": set(),
        "gathersanity_source_pools": {"disenchant"},
        "gathersanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
    }

    def _gathersanity_location_names(self) -> set:
        names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        return {n for n in names if n in gathersanity_content_data.LOCATIONS}

    def test_gathersanity_locations_exist(self) -> None:
        self.assertTrue(len(self._gathersanity_location_names()) > 0)

    def test_every_disenchant_tagged_row_is_present_no_sampling(self) -> None:
        # Direct proof of the no-check_density/weight-sampling contract: with
        # the disenchant source selected, ALL real disenchant-tagged rows must
        # be present, not just a density-sampled subset.
        #
        # M4.11.4.2 fix (round 1 update): this test's direct `tags["source"]`
        # index KeyError'd the moment iteration reached a gathering_node row
        # in this task's OWN full-suite pytest run -- when M4.11.4.2 first
        # rewrote gathering_node into real zone_pool_credit-shaped abstract
        # locations (Tasks 2/5), those rows' own tags were `{"area": [...]}`
        # only, with no "source" key at all. Fixed at the extraction layer
        # itself (extract_gathersanity.py, commit da70249): every
        # gathering_node row now carries a real "source": ["gathering_node"]
        # tag, same as every other Gathersanity source. `.get("source", ())`
        # is kept here regardless -- defensive against any future row shape
        # that again omits the key, matching this project's own established
        # "absent tag means excluded" convention, and no longer load-bearing
        # for correctness today (every real row has the key), just cheap
        # insurance.
        disenchant_rows = [
            name for name, tags in gathersanity_content_data.TAGS.items()
            if "disenchant" in tags.get("source", ())
        ]
        self.assertEqual(sorted(self._gathersanity_location_names()), sorted(disenchant_rows))

    def test_only_disenchant_tagged_rows_are_present(self) -> None:
        sampled = self._gathersanity_location_names()
        self.assertTrue(len(sampled) > 0)
        self.assertLess(len(sampled), len(gathersanity_content_data.LOCATIONS))
        for name in sampled:
            # M4.11.4.2 fix: `sampled` is already narrowed to real
            # `gathersanity_source_pools={"disenchant"}` rows (this class's
            # own options), so every name here really is disenchant-tagged --
            # this assertion is about the row's own TAGS agreeing, not a
            # scan over every row, so a direct index would be fine here in
            # isolation, but `.get` keeps this test consistent with the
            # sibling test above and equally defensive against a future
            # sourceless row shape.
            self.assertIn("disenchant", gathersanity_content_data.TAGS[name].get("source", ()))

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))

    def test_gathersanity_locations_appear_in_ap_item_display(self) -> None:
        # THE regression test for finding C1, and the one test at any level
        # that would have caught it (and would have caught M4.10.1's identical
        # containersanity occurrence): drives the REAL build_slot_data over a
        # REAL generated seed and proves real Gathersanity location ids reach
        # the emitted ap_item_display map. APItemDisplay.cpp's
        # SynthesizeAndRewireLocations iterates ONLY this map -- if a family's
        # key is missing from slot_data.py's _AP_ITEM_DISPLAY_FAMILY_KEYS,
        # nothing is ever synthesized, no loot table is ever rewritten, and no
        # check in the family can ever fire, no matter how correct every other
        # layer is. The fake-module unit tests in test_slot_data.py can only
        # ever prove the family keys they were explicitly told about; this one
        # cannot be fooled that way.
        #
        # WorldTestBase's world_setup only runs gen_steps through pre_fill, so
        # nothing is placed yet and ap_item_display would be trivially empty
        # (verified: it is). Run the real fill first, exactly as AP core's own
        # WorldTestBase.test_fill does, so this asserts against real placed
        # items rather than an empty world.
        from Fill import distribute_items_restrictive
        distribute_items_restrictive(self.multiworld)

        slot_data = self.world.fill_slot_data()
        display = slot_data["ap_item_display"]
        self.assertTrue(display)
        gathersanity_ids = {
            gathersanity_content_data.LOCATIONS[name]
            for name in self._gathersanity_location_names()
        }
        placed_gathersanity_ids = {
            loc.address for loc in self.multiworld.get_locations(self.player)
            if loc.address in gathersanity_ids and loc.item is not None
        }
        self.assertTrue(placed_gathersanity_ids)
        self.assertTrue(placed_gathersanity_ids <= set(display))


class TestProgressiveMiningHerbalismItemsRegistered(unittest.TestCase):
    """M4.11.4.2 Task 4: two new stackable progression items gate
    Gathersanity's new zone+tier abstract (zone_pool_credit) locations, the
    same "Progressive Level Cap" shape (name -> (item_id, count)) core_loop
    already established, hand-declared just outside core_loop's own
    generated 810000-810010 id block so a future core_loop regeneration can
    never collide with them."""

    def test_progressive_mining_and_herbalism_items_registered(self) -> None:
        from worlds.wow import items
        self.assertEqual(items.GATHERING_SKILL_PROGRESSION_ITEMS, {
            "Progressive Mining": (811000, 6),
            "Progressive Herbalism": (811001, 6),
        })


class TestGatheringNodeTierRuleGatesOnProgressiveItem(WoWTestBase):
    """M4.11.4.2 Task 4: a gathering_node location whose own TRIGGERS entry
    is the new "zone_pool_credit" kind (Task 2's real "<zone>|<profession>|
    <tier>" composite zone_key) must be gated on enough copies of the
    matching Progressive Mining/Herbalism item for its own tier.

    gathersanity_content_data.TRIGGERS has NOT been regenerated with any
    real "zone_pool_credit" rows yet as of this task (that's Task 5's own
    job, later in this plan) -- scanning today's real, pre-regeneration data
    for this shape would silently find zero matches, which would make an
    assertion here vacuous rather than a real RED/GREEN proof of the
    rule-gating logic. So this test monkeypatches TRIGGERS with a small
    fixture in the NEW shape instead of relying on real regenerated data --
    Task 5 verifies against the real regenerated content as part of its own
    full-suite run, which is the intended end-to-end check, not this task's.
    """
    options = {
        "game_mode": "sprint", "check_density": 0,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
    }

    def test_gathering_node_tier_rule_gates_on_progressive_item(self) -> None:
        from BaseClasses import ItemClassification
        from .. import rules
        from ..items import WoWItem

        # Reuse any real, already-present location purely as a name to hang
        # our fixture's fake zone_pool_credit trigger on -- world.get_location
        # requires a name that actually exists in this slot's multiworld, and
        # which underlying real location it is does not matter: our own code
        # unconditionally calls world.set_rule for every zone_pool_credit
        # TRIGGERS entry, so whatever rule the location started with is
        # replaced by ours below.
        target_location_name = next(iter(self.multiworld.get_locations(self.player))).name
        fake_triggers = {
            target_location_name: {
                "kind": "zone_pool_credit",
                # "expert" is index 2 (0-based) of GATHERING_SKILL_TIERS --
                # rules.py's own tier_index = index + 1 means this location
                # must require exactly 3 Progressive Mining copies.
                "zone_key": "barrens|mining|expert",
            },
        }
        with patch.object(gathersanity_content_data, "TRIGGERS", fake_triggers):
            rules.set_rules(self.world)

        location = self.multiworld.get_location(target_location_name, self.player)
        self.assertIsNotNone(location.access_rule)

        state = self.multiworld.state

        def mining_item() -> WoWItem:
            return WoWItem("Progressive Mining", ItemClassification.progression, 811000, self.player)

        # Behavioral check, the actual RED/GREEN evidence (not just a
        # not-None structural check): unreachable below 3 copies, reachable
        # at exactly 3, the "expert" tier's own real threshold.
        self.assertFalse(location.access_rule(state))
        state.collect(mining_item())
        state.collect(mining_item())
        self.assertFalse(location.access_rule(state))
        state.collect(mining_item())
        self.assertTrue(location.access_rule(state))

    def test_gathering_node_rule_setup_skips_missing_locations_safely(self) -> None:
        """M4.11.4.2 fix round 1 (real generation-time crash found by
        review): a zone_pool_credit TRIGGERS row whose name is NOT among
        this generation's own real locations (once Task 5 populates real
        data, tag/pool filtering, zone_leveler zone matching, etc. can and
        will exclude any given row from a particular generation) must not
        crash rule-setting via world.get_location's own KeyError.
        _set_rules_gathersanity_progression now iterates the real locations
        that actually exist (world.multiworld.get_locations) instead of
        TRIGGERS' own full, unfiltered dict, so a row with no matching
        location is silently skipped rather than crashing generation."""
        from .. import rules

        fake_triggers = {
            "Gathersanity: Nonexistent Location Not In This Generation": {
                "kind": "zone_pool_credit",
                "zone_key": "barrens|mining|expert",
            },
        }
        with patch.object(gathersanity_content_data, "TRIGGERS", fake_triggers):
            rules.set_rules(self.world)  # must not raise KeyError

    def test_count_gathering_skill_progression_items_matches_pool_size(self) -> None:
        """M4.11.4.2 fix round 1: locations.py's create_filler_locations
        needs count_gathering_skill_progression_items to return exactly the
        real pooled count (create_gathering_skill_progression_item_pool's
        own len()), or item/location parity breaks the moment Task 5
        populates real zone_pool_credit rows. Neither function depends on
        world.get_location/real locations existing, so this is independent
        of the two rule-gating tests above."""
        from ..items import count_gathering_skill_progression_items, create_gathering_skill_progression_item_pool

        fake_triggers = {
            "Loc 1": {"kind": "zone_pool_credit", "zone_key": "barrens|mining|expert"},
            "Loc 2": {"kind": "zone_pool_credit", "zone_key": "barrens|herbalism|apprentice"},
            # A second real node for the SAME (profession, tier) must not
            # double-count -- one Progressive Mining copy per real TIER, not
            # per real node.
            "Loc 3": {"kind": "zone_pool_credit", "zone_key": "durotar|mining|expert"},
        }
        with patch.object(gathersanity_content_data, "TRIGGERS", fake_triggers):
            count = count_gathering_skill_progression_items(self.world)
            pool = create_gathering_skill_progression_item_pool(self.world)
        self.assertEqual(count, len(pool))
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
