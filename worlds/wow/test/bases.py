# Archipelago/worlds/wow/test/bases.py
import typing

from test.bases import WorldTestBase


class WoWTestBase(WorldTestBase):
    game = "World of Warcraft WotLK"

    # M4.8.0: keep the test suite fast by default. Quest Rewards/Vendor
    # Inventories now default ON at weight=100 for REAL seeds (approved
    # design -- see options.py's QuestRewardWeight/VendorStockWeight
    # docstrings), and at check_density's own default of 25 that alone adds
    # roughly 11,000 locations (out of ~47,000 real DB-derived rows across
    # the two families) to every fill-based test that doesn't otherwise
    # constrain them -- a real, measured runtime blowup (a full `pytest
    # worlds/wow` run went from low minutes to many hours). A plain class
    # attribute default on `options` here does NOT fix this: Python class
    # attributes don't merge across inheritance, and 62 of this suite's 67
    # test classes already define their own `options = {...}` dict (many
    # literally `{}`), which fully shadows anything set here. This
    # overrides world_setup instead, MERGING a fast default UNDER whatever
    # a subclass's own options dict specifies, so a subclass's own explicit
    # value always wins.
    #
    # The merge targets quest_reward_weight/vendor_stock_weight directly
    # (NOT check_density, tried first and reverted): check_density is a
    # much older, more broadly-read option -- it also gates the completely
    # unrelated rares/fish/professions/collections families (e.g. Key
    # Hunt's own 40-row rares table), and defaulting IT to 0 broke
    # TestKeyHuntDefaultOptionsGenerate, which relies on check_density's
    # OWN real default (25) to satisfy goals.py's key_hunt validator
    # (confirmed empirically: this exact regression was caught by a real
    # full-suite run). quest_reward_weight/vendor_stock_weight are BRAND
    # NEW as of M4.8.0 -- nothing else in this codebase reads or depends on
    # either being unset vs. explicitly set, so defaulting them here is
    # safe and precisely scoped to the two families that actually caused
    # the runtime blowup: check_density and every other family's own
    # sampling behavior is completely untouched.
    #
    # One real, noticed side effect of overriding world_setup at all (not
    # of the merge logic itself): AP core's own WorldTestBase.run_default_tests
    # is a property that treats "world_setup is overridden" as reason
    # enough to run the generic test_all_state_can_reach_everything/
    # test_empty_state_can_reach_something/test_fill checks, even for a
    # class with falsy `options`. Before this file existed, 6 WoW test
    # classes with `options = {}` (or no override at all) skipped those
    # generic checks entirely; now every WoW test class runs them
    # unconditionally, since WoWTestBase itself always overrides
    # world_setup. Confirmed via a real full-suite run that this is a pure
    # coverage increase, not a regression -- every one of those 6 classes'
    # generic checks pass -- but it IS a real behavior change this file is
    # responsible for, not just a "fast defaults, nothing else changes"
    # shim.
    def world_setup(self, seed: typing.Optional[int] = None) -> None:
        original_options = self.options
        merged = dict(original_options)
        if "quest_reward_weight" not in merged:
            merged["quest_reward_weight"] = 0
        if "vendor_stock_weight" not in merged:
            merged["vendor_stock_weight"] = 0
        # M4.9: recipes/trainer_spells have NO weight_option to zero out
        # (locations.py's OptionalCategory.weight_option is None for both
        # -- per spec, every tag-matching row is included unconditionally).
        # The only way to keep this suite fast for these two families is to
        # narrow ONE of their AND'd tag dimensions to nothing by default --
        # same "opt in explicitly per test class" spirit as
        # quest_reward_weight/vendor_stock_weight above. Without this,
        # every WoWTestBase test would additionally sample the full
        # ~1,912-row recipes table and ~1,966-row trainer_spells table on
        # every single run.
        if "recipe_profession_pools" not in merged:
            merged["recipe_profession_pools"] = set()
        if "trainer_spell_class_pools" not in merged:
            merged["trainer_spell_class_pools"] = set()
        if "filler_category_pools" not in merged:
            merged["filler_category_pools"] = {"consumable", "bag", "reagent"}
        # M4.10.1: containersanity shares recipes/trainer_spells' exact
        # weight_option=None shape (every tag-matched row included
        # unconditionally). Without this default, every WoWTestBase test
        # would additionally sample/pool the full ~16,526-row
        # containersanity family on every single run. (Originally
        # ~17,594 at extraction time; narrowed by a final whole-branch
        # review fix excluding 784 permanently-unlootable rows -- see
        # extract_containersanity.py. Further narrowed to ~16,526 by
        # M4.10.2 Task 1, which carves 284 real gathering-node rows --
        # Copper Vein, Silverleaf, etc. -- out to Gathersanity's own
        # extraction.)
        if "containersanity_expansion_pools" not in merged:
            merged["containersanity_expansion_pools"] = set()
        self.options = merged
        try:
            super().world_setup(seed)
        finally:
            self.options = original_options

