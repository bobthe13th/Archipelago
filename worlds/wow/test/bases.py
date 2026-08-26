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
    # the runtime blowup, leaving check_density and every other family
    # completely untouched.
    def world_setup(self, seed: typing.Optional[int] = None) -> None:
        original_options = self.options
        merged = dict(original_options)
        if "quest_reward_weight" not in merged:
            merged["quest_reward_weight"] = 0
        if "vendor_stock_weight" not in merged:
            merged["vendor_stock_weight"] = 0
        self.options = merged
        try:
            super().world_setup(seed)
        finally:
            self.options = original_options
