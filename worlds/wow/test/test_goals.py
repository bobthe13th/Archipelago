# Archipelago/worlds/wow/test/test_goals.py
from Options import OptionError

from .bases import WoWTestBase


class TestGoalValidation(WoWTestBase):
    run_default_tests = False
    auto_construct = False
    # NOTE: the test option value is the Choice's bare option name ("fishing_quest"),
    # not the "option_"-prefixed class attribute name -- Choice.from_text (Options.py)
    # strips that prefix when building cls.options, and compares the lowercased input
    # directly against the stripped keys, confirmed empirically (an "option_"-prefixed
    # value raises "Could not find option ... known options are sprint" even after this
    # value existed).
    options = {"game_mode": "fishing_quest", "check_density": 0}

    def test_fishing_quest_at_zero_density_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestArtisanNotYetImplemented(WoWTestBase):
    """Every GameMode value without real content yet must still raise
    OptionError -- this is the regression guard for Task 22's "land both in
    the same commit" requirement (a new GameMode value must never become
    silently selectable before its own task lands). key_hunt used to be
    covered by this same test (Task 22-24), but Task 25 gave it real content,
    so this now uses artisan (still Group 6 Tier 3, unimplemented) instead."""
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "artisan"}

    def test_artisan_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestKeyHuntDefaultOptionsGenerate(WoWTestBase):
    """Task 25: selecting key_hunt with every other option left at default
    must actually generate, not immediately fail validation -- the specific
    bug this task's own review caught (the initial KeyHuntKeysRequired
    default of 15 exceeded what CheckDensity's own default of 25 would
    sample from the 40 curated rares, ceil(40 * 0.25) = 10)."""
    options = {"game_mode": "key_hunt"}

    def test_generates_successfully(self) -> None:
        self.assertTrue(self.constructed)


class TestKeyHuntZeroDensityFailsValidation(WoWTestBase):
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "key_hunt", "check_density": 0}

    def test_zero_density_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestKeyHuntLocationsAndItemsOnlyExistInKeyHuntMode(WoWTestBase):
    """rares.yaml is the first content family gated on game_mode itself, not
    an independent toggle -- a Sprint-mode seed must have zero rares
    locations and zero "Key Hunt: Key" items in its pool."""
    options = {"game_mode": "sprint"}

    def test_no_rare_kill_locations_or_key_items_outside_key_hunt_mode(self) -> None:
        location_names = {loc.name for loc in self.multiworld.get_locations()}
        self.assertFalse(any(name.startswith("Rare Kill:") for name in location_names))
        self.assertEqual(len(self.get_items_by_name("Key Hunt: Key")), 0)


class TestKeyHuntItemLocationParity(WoWTestBase):
    """The sampled rare-kill location count and pooled "Key Hunt: Key" item
    count must match exactly, at a non-default density so the test actually
    exercises sampling below the full 40-row ceiling."""
    options = {"game_mode": "key_hunt", "check_density": 50, "key_hunt_keys_required": 15}

    def test_sampled_location_count_matches_pooled_key_count(self) -> None:
        rare_kill_locations = [loc for loc in self.multiworld.get_locations() if loc.name.startswith("Rare Kill:")]
        key_items = self.get_items_by_name("Key Hunt: Key")
        self.assertEqual(len(rare_kill_locations), len(key_items))
        # ceil(40 * 0.50) = 20, well above key_hunt_keys_required=15, so this
        # also confirms sampling isn't silently capped at keys_required.
        self.assertEqual(len(rare_kill_locations), 20)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestKeyHuntCompletionRequiresKeysAndInstances(WoWTestBase):
    """Key Hunt's completion condition spans two unrelated item families at
    once -- collecting enough keys alone, or clearing enough raids alone,
    must each be insufficient on their own."""
    options = {
        "game_mode": "key_hunt",
        "check_density": 100,
        "key_hunt_keys_required": 5,
        "key_hunt_instances_required": 2,
    }

    def test_keys_alone_is_not_enough(self) -> None:
        state = self.multiworld.state
        keys = self.get_items_by_name("Key Hunt: Key")
        self.collect(keys[:5])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_instances_alone_is_not_enough(self) -> None:
        state = self.multiworld.state
        self.collect_by_name("Instance Unlock: Ragefire Chasm")
        self.collect_by_name("Instance Unlock: Deadmines")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_both_together_completes(self) -> None:
        state = self.multiworld.state
        keys = self.get_items_by_name("Key Hunt: Key")
        self.collect(keys[:5])
        self.collect_by_name("Instance Unlock: Ragefire Chasm")
        self.collect_by_name("Instance Unlock: Deadmines")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))

    def test_instances_required_counts_unique_raids_not_total_copies(self) -> None:
        # has_from_list_unique counts distinct item names, not total copies --
        # collecting the SAME instance unlock's only copy twice is impossible
        # in practice (there's only one), but this confirms two DIFFERENT
        # single-copy unlocks satisfy instances_required=2, not requiring a
        # higher combined count.
        state = self.multiworld.state
        keys = self.get_items_by_name("Key Hunt: Key")
        self.collect(keys[:5])
        self.collect_by_name("Instance Unlock: Molten Core")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Sunwell Plateau")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestClassicMode(WoWTestBase):
    """Task 23 (Tier 1): Classic completes on Molten Core's Instance Unlock."""
    options = {"game_mode": "classic"}

    def test_completion_requires_molten_core_unlock(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Molten Core")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestBurningCrusadeMode(WoWTestBase):
    """Task 23 (Tier 1): Burning Crusade completes on Sunwell Plateau's
    Instance Unlock."""
    options = {"game_mode": "burning_crusade"}

    def test_completion_requires_sunwell_plateau_unlock(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Sunwell Plateau")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestWrathMode(WoWTestBase):
    """Task 23 (Tier 1): Wrath completes on Icecrown Citadel's Instance
    Unlock."""
    options = {"game_mode": "wrath"}

    def test_completion_requires_icecrown_citadel_unlock(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Icecrown Citadel")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestCompletionistModeVanilla(WoWTestBase):
    """Task 24: Completionist/vanilla requires all THREE vanilla instance
    unlocks at once (Ragefire Chasm, Deadmines, Molten Core) -- the one mode
    so far whose completion rule needs more than a single item."""
    options = {"game_mode": "completionist", "completionist_expansion": "vanilla"}

    def test_completion_requires_all_three_vanilla_unlocks(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Ragefire Chasm")
        self.collect_by_name("Instance Unlock: Deadmines")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Molten Core")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestCompletionistModeTbc(WoWTestBase):
    options = {"game_mode": "completionist", "completionist_expansion": "tbc"}

    def test_completion_requires_sunwell_plateau_unlock(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Sunwell Plateau")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestCompletionistModeWotlk(WoWTestBase):
    options = {"game_mode": "completionist", "completionist_expansion": "wotlk"}

    def test_completion_requires_icecrown_citadel_unlock(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Icecrown Citadel")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestInstanceClearModeFinalBossOnly(WoWTestBase):
    """Smoke test: the option's non-default value is selectable and doesn't
    change generation-time logic at all -- InstanceClearMode only affects
    which C++ hook path records a raid clear in real play (see
    ArchipelagoInstanceScript.cpp), not anything rules.py/goals.py checks,
    so a Classic-mode seed's completion rule must still resolve identically
    regardless of this option."""
    options = {"game_mode": "classic", "instance_clear_mode": "final_boss_only"}

    def test_completion_still_requires_molten_core_unlock(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Molten Core")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))
