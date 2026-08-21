# Archipelago/worlds/wow/test/test_goals.py
from Options import OptionError

from .bases import WoWTestBase


class TestFishingQuestNotSampledByDensity(WoWTestBase):
    """Task 26: unlike Key Hunt's rares, fish.yaml is explicitly NOT
    density-sampled (spec Sec5.4: "the set is bounded and discrete... which
    makes it a tractable completion goal" -- sampling it would break the
    completion condition). This test used to assert the OPPOSITE
    (check_density: 0 fails generation) back when fishing_quest was still
    not-yet-implemented (Task 22-25); now that it has real content, density
    must have zero effect on it -- all 46 fish locations/items always exist
    at any check_density, including 0."""
    options = {"game_mode": "fishing_quest", "check_density": 0}

    def test_generates_successfully_even_at_zero_density(self) -> None:
        self.assertTrue(self.constructed)

    def test_all_46_fish_locations_and_items_still_exist(self) -> None:
        fish_locations = [loc for loc in self.multiworld.get_locations() if loc.name.startswith("Fish Catch:")]
        self.assertEqual(len(fish_locations), 46)
        from .. import fish_content_data
        for name in fish_content_data.ITEMS:
            self.assertEqual(len(self.get_items_by_name(name)), 1)


class TestGladiatorNotBuildable(WoWTestBase):
    """Gladiator is a DIFFERENT deferral category from the not-yet-implemented
    swap chain above (key_hunt -> artisan -> collector, each retired once its
    own task shipped real content) -- Task 27's own hook research found
    arena-rating tiers have no safe push hook (OnBeforeArenaTeamMemberUpdate
    fires before the engine's own ArenaTeam::GetRatingMod computes the actual
    rating change, so the post-match rating can't be predicted from that
    hook without blindly reimplementing untestable internal engine math) and
    battleground-objective events (flag captures, etc.) aren't exposed via
    any generic ScriptMgr hook at all, only hardcoded inside each
    Battleground subclass -- matching achievement_hunt/explorer's
    not_buildable category (verified, not assumed) rather than a scheduling
    gap. Resolved 2026-08-20 per explicit user direction: same hard-failure
    treatment as achievement_hunt/explorer."""
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "gladiator"}

    def test_gladiator_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestAchievementHuntNotBuildable(WoWTestBase):
    """achievement_hunt and explorer are a DIFFERENT deferral category from
    the above -- Task 27's own research found this checkout's
    data/sql/base/db_world/*_dbc.sql tables (achievement_dbc,
    achievement_criteria_dbc, areatable_dbc, ...) are empty stub schemas
    with zero real data, and no binary .dbc client files exist in the repo
    either, so there is no real achievement/subzone name data anywhere to
    build a "full roster" from -- matching Task 9's earlier "not buildable"
    finding for continent/city/zone gates. This must keep failing even
    after every OTHER Tier-3 mode has real content, unlike
    TestCollectorNotYetImplemented above."""
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "achievement_hunt"}

    def test_achievement_hunt_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestExplorerNotBuildable(WoWTestBase):
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "explorer"}

    def test_explorer_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestArtisanDefaultOptionsGenerate(WoWTestBase):
    """Task 27: selecting artisan with every other option left at default
    must actually generate."""
    options = {"game_mode": "artisan"}

    def test_generates_successfully(self) -> None:
        self.assertTrue(self.constructed)


class TestArtisanItemLocationParity(WoWTestBase):
    options = {"game_mode": "artisan"}

    def test_all_84_locations_and_items_exist(self) -> None:
        profession_locations = [loc for loc in self.multiworld.get_locations() if loc.name.startswith("Profession:")]
        self.assertEqual(len(profession_locations), 84)
        from .. import professions_content_data
        for name in professions_content_data.ITEMS:
            self.assertEqual(len(self.get_items_by_name(name)), 1)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestArtisanCompletionRequiresSecondariesAndPrimaries(WoWTestBase):
    """Completion needs all 3 secondary professions AND N of the 11 primary
    professions -- either alone must not be enough."""
    options = {"game_mode": "artisan", "artisan_primary_professions_required": 2}

    def test_secondaries_alone_is_not_enough(self) -> None:
        state = self.multiworld.state
        self.collect_by_name("Skill Milestone: First Aid 450")
        self.collect_by_name("Skill Milestone: Cooking 450")
        self.collect_by_name("Skill Milestone: Fishing 450")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_two_primaries_alone_is_not_enough(self) -> None:
        state = self.multiworld.state
        self.collect_by_name("Skill Milestone: Alchemy 450")
        self.collect_by_name("Skill Milestone: Blacksmithing 450")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_all_secondaries_plus_two_primaries_completes(self) -> None:
        state = self.multiworld.state
        self.collect_by_name("Skill Milestone: First Aid 450")
        self.collect_by_name("Skill Milestone: Cooking 450")
        self.collect_by_name("Skill Milestone: Fishing 450")
        self.collect_by_name("Skill Milestone: Alchemy 450")
        self.collect_by_name("Skill Milestone: Blacksmithing 450")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestCollectorDefaultOptionsGenerate(WoWTestBase):
    """Task 27: selecting collector with every other option left at default
    must actually generate."""
    options = {"game_mode": "collector"}

    def test_generates_successfully(self) -> None:
        self.assertTrue(self.constructed)


class TestCollectorItemLocationParity(WoWTestBase):
    options = {"game_mode": "collector"}

    def test_all_264_locations_and_items_exist(self) -> None:
        collection_locations = [loc for loc in self.multiworld.get_locations() if loc.name.startswith("Learn ")]
        self.assertEqual(len(collection_locations), 264)
        from .. import collections_content_data
        for name in collections_content_data.ITEMS:
            self.assertEqual(len(self.get_items_by_name(name)), 1)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestCollectorCompletionRequiresConfiguredThreshold(WoWTestBase):
    """Completion needs at least collector_items_required distinct
    mounts/pets received -- fewer than that must not be enough, and exactly
    that many (any combination) must complete."""
    options = {"game_mode": "collector", "collector_items_required": 2}

    def test_one_item_is_not_enough(self) -> None:
        state = self.multiworld.state
        self.collect_by_name("Mount: Horn of the Timber Wolf")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_two_items_completes(self) -> None:
        state = self.multiworld.state
        self.collect_by_name("Mount: Horn of the Timber Wolf")
        self.collect_by_name("Pet: Cat Carrier (Bombay)")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


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


class TestFishingQuestItemLocationParity(WoWTestBase):
    options = {"game_mode": "fishing_quest"}

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestFishingQuestCompletionRequiresAllFortySixFish(WoWTestBase):
    """Task 26: completion needs ALL 46 distinct "Fish: <name>" items --
    collecting all but one must not be enough."""
    options = {"game_mode": "fishing_quest"}

    def test_all_but_one_is_not_enough(self) -> None:
        from .. import fish_content_data
        state = self.multiworld.state
        names = list(fish_content_data.ITEMS.keys())
        for name in names[:-1]:
            self.collect_by_name(name)
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name(names[-1])
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestFishingQuestNorthrendAccessRule(WoWTestBase):
    """Task 26 (spec Sec5.4): "fish-catch locations inherit normal regional
    access logic -- a Northrend-only fish requires Northrend Passage in
    logic." Mirrors TestCoreLoopAccessRules' pattern -- a Northrend-tagged
    fish location must be unreachable without Northrend Passage, and a
    non-Northrend one must not require it."""
    options = {"game_mode": "fishing_quest"}

    def test_northrend_fish_location_requires_northrend_passage(self) -> None:
        self.assertFalse(self.can_reach_location("Fish Catch: Glacial Salmon"))
        self.collect_by_name("Northrend Passage")
        self.assertTrue(self.can_reach_location("Fish Catch: Glacial Salmon"))

    def test_non_northrend_fish_location_does_not_require_northrend_passage(self) -> None:
        self.assertTrue(self.can_reach_location("Fish Catch: Raw Longjaw Mud Snapper"))
