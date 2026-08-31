# Archipelago/worlds/wow/test/test_repsanity.py
from .bases import WoWTestBase
from .. import repsanity_content_data


class TestRepsanityRealGeneration(WoWTestBase):
    """repsanity_expansion_pools and repsanity_rank_tier_pools default to
    empty (bases.py's test-speed default, Task 4's fix) -- must be set to
    non-empty values here so this class's real-generation assertions aren't
    vacuously false. Tag filtering uses AND logic: both dimensions must match,
    so an empty rank_tier_pools would zero out all repsanity locations
    regardless of expansion_pools."""

    options = {
        "game_mode": "sprint", "check_density": 100, "vendor_stock_weight": 0,
        "repsanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
        "repsanity_rank_tier_pools": {"standard", "negative"},
    }

    def test_real_seed_includes_a_standard_rank_location(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Reputation: Stormwind (Friendly)", location_names)

    def test_real_seed_includes_a_negative_rank_location(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Reputation: Bloodsail Buccaneers (Hostile)", location_names)

    def test_real_seed_never_includes_a_factions_own_starting_rank(self) -> None:
        # Bloodsail Buccaneers starts at Hated (its own starting rank) --
        # Hated is never a checkable location for it. Stormwind starts at
        # Neutral -- Neutral is never a checkable location for it either
        # (its first checkable rank is Friendly, per extract_repsanity.py's
        # range(starting_rank + 1, 8)).
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Reputation: Bloodsail Buccaneers (Hated)", location_names)
        self.assertNotIn("Reputation: Stormwind (Neutral)", location_names)


class TestRepsanityRankTierFiltering(WoWTestBase):
    """Same repsanity_expansion_pools default-empty issue as above --
    without it, repsanity_rank_tier_pools=standard would still yield zero
    locations (AND'd dimensions), making test_excluding_negative_tier_...
    pass for the wrong reason (nothing present at all, not real filtering)."""

    options = {
        "game_mode": "sprint",
        "check_density": 100,
        "vendor_stock_weight": 0,
        "repsanity_expansion_pools": {"vanilla", "tbc", "wotlk"},
        "repsanity_rank_tier_pools": {"standard"},
    }

    def test_excluding_negative_tier_removes_negative_rank_locations(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertNotIn("Reputation: Bloodsail Buccaneers (Hostile)", location_names)
        self.assertIn("Reputation: Stormwind (Friendly)", location_names)


class TestRepsanityContentData(WoWTestBase):
    options = {"game_mode": "sprint", "check_density": 0, "vendor_stock_weight": 0}

    def test_content_data_has_real_row_count(self) -> None:
        # Real count is 449, not the plan's original 561 estimate -- see
        # Task 2's ledgered ruling/review: the plan's Global Constraints
        # prose assumed 5 checkable ranks per faction including Neutral,
        # but the real extraction algorithm (range(starting_rank + 1, 8))
        # excludes a faction's own starting rank, so the ~93 factions that
        # start at Neutral only yield 4 checkable ranks each. Independently
        # reconciled: 93 non-curated factions x 4 + 12 curated
        # negative-capable factions' real extra ranks = 449.
        self.assertEqual(len(repsanity_content_data.LOCATIONS), 449)

    def test_no_faction_has_a_location_at_its_own_starting_rank_or_below(self) -> None:
        # Stormwind (starts Neutral) must never have a Hated/Hostile/Unfriendly
        # location; this is really the same invariant extract_repsanity.py's
        # own test_stormwind_has_no_negative_rank_locations already checks at
        # the YAML-generation layer -- repeated here against the COMPILED
        # content module, so a stale/hand-edited generated file would also
        # fail this.
        for rank in ("Hated", "Hostile", "Unfriendly"):
            self.assertNotIn(f"Reputation: Stormwind ({rank})", repsanity_content_data.LOCATIONS)
