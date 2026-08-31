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


class TestRepsanityExpansionFiltering(WoWTestBase):
    """Only repsanity_rank_tier_pools has real-generation coverage above --
    repsanity_expansion_pools has none. Set expansion_pools to {"tbc"} only
    (and rank_tier_pools to its full vocabulary, so this class isolates the
    expansion dimension exactly the way TestRepsanityRankTierFiltering
    isolates the rank_tier dimension)."""

    options = {
        "game_mode": "sprint",
        "check_density": 100,
        "vendor_stock_weight": 0,
        "repsanity_expansion_pools": {"tbc"},
        "repsanity_rank_tier_pools": {"standard", "negative"},
    }

    def test_tbc_only_includes_tbc_faction_excludes_vanilla_faction(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        self.assertIn("Reputation: The Sha'tar (Friendly)", location_names)
        self.assertNotIn("Reputation: Stormwind (Friendly)", location_names)


class TestRepsanityContentData(WoWTestBase):
    options = {"game_mode": "sprint", "check_density": 0, "vendor_stock_weight": 0}

    def test_no_location_name_contains_junk_placeholder_text(self) -> None:
        for name in repsanity_content_data.LOCATIONS:
            self.assertNotIn("Test Faction", name)

    def test_no_location_name_has_a_double_space(self) -> None:
        for name in repsanity_content_data.LOCATIONS:
            self.assertNotIn("  ", name)

    def test_aldor_rank_floor_is_unfriendly_not_hostile_or_hated(self) -> None:
        # Real-engine rank-computation fix from the M4.10.4 final review:
        # The Aldor's lowest generated location must be Unfriendly (its
        # true rank floor), not Hostile or Hated.
        self.assertIn("Reputation: The Aldor (Unfriendly)", repsanity_content_data.LOCATIONS)
        self.assertNotIn("Reputation: The Aldor (Hostile)", repsanity_content_data.LOCATIONS)
        self.assertNotIn("Reputation: The Aldor (Hated)", repsanity_content_data.LOCATIONS)

    def test_content_data_has_real_row_count(self) -> None:
        # Real count is 339, not the plan's original 561 estimate, and not
        # the 449 count Task 2's own review had reconciled either. The
        # M4.10.4 final whole-branch review found 449 still included 108
        # unobtainable DBC junk-faction locations (factions with no real,
        # player-facing standing track -- since removed via a denylist in
        # the module-repo extraction) plus 2 more rows from a rank-
        # computation bug fix (e.g. The Aldor/The Scryers' true rank floor
        # is Unfriendly, not Hated/Hostile). 449 - 108 - 2 = 339.
        self.assertEqual(len(repsanity_content_data.LOCATIONS), 339)

    def test_no_faction_has_a_location_at_its_own_starting_rank_or_below(self) -> None:
        # Stormwind (starts Neutral) must never have a Hated/Hostile/Unfriendly
        # location; this is really the same invariant extract_repsanity.py's
        # own test_stormwind_has_no_negative_rank_locations already checks at
        # the YAML-generation layer -- repeated here against the COMPILED
        # content module, so a stale/hand-edited generated file would also
        # fail this.
        for rank in ("Hated", "Hostile", "Unfriendly"):
            self.assertNotIn(f"Reputation: Stormwind ({rank})", repsanity_content_data.LOCATIONS)
