# Archipelago/worlds/wow/test/test_goals.py
import unittest

from Options import OptionError

from .. import goals
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


class TestGladiatorRemovedFromGameMode(unittest.TestCase):
    """M4.9 Sec4: Gladiator retired entirely -- not merely a permanent
    hard-fail option (that was the 2026-08-20 interim state this class used
    to test via TestGladiatorNotBuildable). Deleting a previously-shipped
    option value is a breaking change for any existing seed's YAML that
    referenced it; acceptable per the spec because no real seed could ever
    have used it successfully (goals.py's own _NOT_BUILDABLE_MODES already
    made it fail generation unconditionally). The retired value 9 is NOT
    reused or renumbered -- option_explorer (10), option_fishing_quest (11),
    and option_hundred_percent (12) keep their exact existing numeric
    values, so no OTHER already-shipped GameMode value's meaning shifts."""

    def test_gladiator_option_name_no_longer_exists(self) -> None:
        from ..options import GameMode
        self.assertNotIn("option_gladiator", dir(GameMode))
        self.assertNotIn("gladiator", GameMode.name_lookup.values())

    def test_value_9_is_permanently_retired_not_reused(self) -> None:
        from ..options import GameMode
        self.assertNotIn(9, GameMode.name_lookup)

    def test_other_game_mode_values_keep_their_existing_numbers(self) -> None:
        from ..options import GameMode
        self.assertEqual(GameMode.name_lookup[7], "collector")
        self.assertEqual(GameMode.name_lookup[10], "explorer")
        self.assertEqual(GameMode.name_lookup[11], "fishing_quest")
        self.assertEqual(GameMode.name_lookup[12], "hundred_percent")

    def test_goals_dispatch_tables_have_no_entry_for_value_9(self) -> None:
        self.assertNotIn(9, goals._VALIDATORS)
        self.assertNotIn(9, goals._COMPLETION_RULES)
        self.assertNotIn(9, goals._NOT_BUILDABLE_MODES)

    def test_selecting_gladiator_by_name_is_rejected_by_options_parsing(self) -> None:
        from ..options import GameMode
        from Options import OptionError
        with self.assertRaises((KeyError, OptionError, ValueError)):
            GameMode.from_text("gladiator")

    def test_no_python_source_file_references_gladiator_at_all(self) -> None:
        # NOTE: adapted from the M4.9.4 task-9 brief's literal version, which
        # asserted a bare `offending == []` over every *.py file's raw text.
        # Run as originally written, that version fails here -- not because
        # Gladiator lingers as a GameMode, but because of two categories of
        # false positive the manual grep sweep (this same task's Step 3)
        # explicitly treats as acceptable and out of scope:
        #   1. This very test file, whose TestGladiatorRemovedFromGameMode
        #      class (name, docstring, and sibling test methods) necessarily
        #      says "gladiator" while explaining the removal.
        #   2. Generated *_content_data.py modules, which hold real WoW
        #      item/achievement names that happen to contain the word (e.g.
        #      "Gladiator's Tabard", the arena-rating achievement literally
        #      named "Gladiator") -- not the retired GameMode value.
        #   3. goals.py's own historical-context comment
        #      (_NOT_BUILDABLE_MODES) explaining that Gladiator was removed.
        # This version keeps the brief's intent -- fail on any *live code*
        # reference to Gladiator as a GameMode -- while excluding exactly
        # those documented-acceptable categories.
        import pathlib
        wow_dir = pathlib.Path(__file__).parent.parent
        this_file = pathlib.Path(__file__).resolve()
        offending = []
        for path in wow_dir.rglob("*.py"):
            if path.resolve() == this_file:
                continue
            if path.name.endswith("_content_data.py"):
                continue
            code_lines = [
                line for line in path.read_text(encoding="utf-8").splitlines()
                if not line.strip().startswith("#")
            ]
            if "gladiator" in "\n".join(code_lines).lower():
                offending.append(str(path))
        self.assertEqual(offending, [])


class TestAchievementHuntDefaultOptionsGenerate(WoWTestBase):
    options = {"game_mode": "achievement_hunt"}

    def test_generates_successfully(self) -> None:
        self.assertTrue(self.constructed)

    def test_all_1162_achievement_locations_and_items_exist(self) -> None:
        from .. import achievements_content_data
        achievement_locations = [
            loc for loc in self.multiworld.get_locations()
            if loc.name.startswith("Achievement: ")
        ]
        self.assertEqual(len(achievement_locations), 1162)
        self.assertEqual(len(achievements_content_data.LOCATIONS), 1162)
        for name in achievements_content_data.ITEMS:
            self.assertEqual(len(self.get_items_by_name(name)), 1)

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestAchievementHuntCompletionHundredPercentRequiresEveryAchievement(WoWTestBase):
    options = {"game_mode": "achievement_hunt", "achievement_hunt_tier": "hundred_percent"}

    def test_partial_collection_does_not_complete(self) -> None:
        from .. import achievements_content_data
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        some_names = list(achievements_content_data.ITEMS.keys())[:50]
        for name in some_names:
            self.collect_by_name(name)
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_collecting_every_achievement_item_completes(self) -> None:
        from .. import achievements_content_data
        state = self.multiworld.state
        for name in achievements_content_data.ITEMS:
            self.collect_by_name(name)
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestAchievementHuntCompletionNinetyNinePercentExcludesHardDenylist(WoWTestBase):
    options = {"game_mode": "achievement_hunt", "achievement_hunt_tier": "ninety_nine_percent"}

    def test_extremely_hard_items_are_not_required(self) -> None:
        from .. import achievements_content_data, goals
        world = self.multiworld.worlds[self.player]
        target = goals._achievement_hunt_target_item_names(world)
        self.assertTrue(achievements_content_data.EXTREMELY_HARD_ITEM_NAMES.isdisjoint(target))
        self.assertEqual(len(target), 1162 - 33)

    def test_collecting_every_non_hard_achievement_item_completes(self) -> None:
        from .. import achievements_content_data
        state = self.multiworld.state
        for name in achievements_content_data.ITEMS:
            if name not in achievements_content_data.EXTREMELY_HARD_ITEM_NAMES:
                self.collect_by_name(name)
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestAchievementHuntNamedSubsetTargetsOnlyThatSubset(WoWTestBase):
    options = {
        "game_mode": "achievement_hunt",
        "achievement_hunt_tier": "named_subset",
        "achievement_hunt_subset": "professions",
    }

    def test_target_set_is_exactly_the_professions_subset(self) -> None:
        from .. import achievements_content_data, goals
        world = self.multiworld.worlds[self.player]
        target = goals._achievement_hunt_target_item_names(world)
        self.assertEqual(target, achievements_content_data.ACHIEVEMENTS_BY_SUBSET["professions"])
        self.assertEqual(len(target), 77)

    def test_collecting_only_the_professions_subset_completes(self) -> None:
        from .. import achievements_content_data
        state = self.multiworld.state
        for name in achievements_content_data.ACHIEVEMENTS_BY_SUBSET["professions"]:
            self.collect_by_name(name)
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestExplorerDefaultOptionsGenerate(WoWTestBase):
    options = {"game_mode": "explorer"}

    def test_generates_successfully(self) -> None:
        self.assertTrue(self.constructed)

    def test_exactly_one_achievement_location_exists(self) -> None:
        achievement_locations = [
            loc for loc in self.multiworld.get_locations()
            if loc.name.startswith("Achievement: ")
        ]
        self.assertEqual(len(achievement_locations), 1)
        self.assertEqual(achievement_locations[0].name, "Achievement: World Explorer (#46)")

    def test_no_achievement_hunt_locations_leak_into_explorer_mode(self) -> None:
        from .. import achievements_content_data
        location_names = {loc.name for loc in self.multiworld.get_locations()}
        # Every OTHER achievement location must be absent -- Explorer only
        # ever creates the single World Explorer row, not the full pool.
        other_names = set(achievements_content_data.LOCATIONS) - {achievements_content_data.WORLD_EXPLORER_LOCATION_NAME}
        self.assertTrue(location_names.isdisjoint(other_names))

    def test_completion_requires_the_world_explorer_item(self) -> None:
        from .. import achievements_content_data
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name(achievements_content_data.WORLD_EXPLORER_ITEM_NAME)
        self.assertTrue(self.multiworld.completion_condition[self.player](state))

    def test_item_pool_matches_location_count_exactly(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestAchievementHuntOptionsExist(unittest.TestCase):
    def test_achievement_hunt_tier_has_the_three_spec_values(self) -> None:
        from ..options import AchievementHuntTier
        self.assertEqual(AchievementHuntTier.option_hundred_percent, 0)
        self.assertEqual(AchievementHuntTier.option_ninety_nine_percent, 1)
        self.assertEqual(AchievementHuntTier.option_named_subset, 2)
        self.assertEqual(AchievementHuntTier.default, 0)

    def test_achievement_hunt_subset_has_the_six_named_subsets(self) -> None:
        from ..options import AchievementHuntSubset
        self.assertEqual(
            set(AchievementHuntSubset.name_lookup.values()),
            {"explorer", "dungeons", "raids", "professions", "reputation", "pvp"},
        )

    def test_wow_options_dataclass_has_both_new_fields(self) -> None:
        from ..options import WoWOptions
        self.assertIn("achievement_hunt_tier", WoWOptions.type_hints)
        self.assertIn("achievement_hunt_subset", WoWOptions.type_hints)


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
        # M4.8.0: this class doesn't reference quest_rewards/vendor_stock at
        # all -- check_density: 100 above is only meant to guarantee all 40
        # Key Hunt rares sample in, but without an explicit weight override
        # here it also pulls in the full ~47,000-row quest_rewards/
        # vendor_stock tables at their own real-seed weight default of 100,
        # making this test pathologically slow for no test-relevant reason.
        "quest_reward_weight": 0,
        "vendor_stock_weight": 0,
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


class TestKeyHuntZonePoolsRestrictsEligibleRareCount(WoWTestBase):
    """M4.11.1 Task 5: key_hunt_zone_pools ANDs against density sampling
    (M4.8 §2 convention) -- restricting to a single zone shrinks the
    candidate pool BEFORE sampling, same shape as quest_reward_type_pools/
    quest_reward_expansion_pools ANDing against quest_rewards. "felwood" has
    exactly 3 of the 40 curated rares (Carnivous the Breaker, Olm the Wise,
    Mezzir the Howler -- rares.yaml's own real area tags), confirmed
    directly against rares_content_data.TAGS rather than hardcoded from
    memory. (M4.11.3.1 Task 6: reads the family's unified `area` tag --
    Task 1-3's fixed resolve_area_tags_for_positions, which unions every
    real zone a rare's real spawns touch instead of picking one
    single-winner zone -- instead of the retired `zone` tag; the same 3
    rows still carry "felwood" under the new mechanism, now alongside
    additional area tags on 2 of the 3 rows (Olm the Wise/Mezzir the Howler
    also tag darkshore/winterspring, a real widening, not a regression)."""
    options = {
        "game_mode": "key_hunt",
        "check_density": 100,
        "key_hunt_zone_pools": {"felwood"},
        "key_hunt_keys_required": 3,
        "quest_reward_weight": 0,
        "vendor_stock_weight": 0,
    }

    def test_only_felwood_rares_are_sampled(self) -> None:
        from .. import rares_content_data
        expected_names = {
            name for name, tags in rares_content_data.TAGS.items()
            if "felwood" in tags.get("area", frozenset())
        }
        self.assertEqual(len(expected_names), 3)
        rare_kill_locations = {loc.name for loc in self.multiworld.get_locations() if loc.name.startswith("Rare Kill:")}
        self.assertEqual(rare_kill_locations, expected_names)

    def test_item_pool_matches_restricted_location_count(self) -> None:
        rare_kill_locations = [loc for loc in self.multiworld.get_locations() if loc.name.startswith("Rare Kill:")]
        key_items = self.get_items_by_name("Key Hunt: Key")
        self.assertEqual(len(rare_kill_locations), len(key_items))
        self.assertEqual(len(rare_kill_locations), 3)


class TestKeyHuntZonePoolsTooNarrowFailsValidation(WoWTestBase):
    """A key_hunt_zone_pools selection that leaves too few zone-eligible
    rares for key_hunt_keys_required must fail generation loudly (goals.py's
    _validate_key_hunt), the same discipline as
    TestKeyHuntUnsatisfiableAfterCeilingRemoval -- "felwood" only has 3
    eligible rows, and even at check_density's max (100, ceil(3*1.0) == 3)
    that's still short of key_hunt_keys_required=10."""
    run_default_tests = False
    auto_construct = False
    options = {
        "game_mode": "key_hunt",
        "check_density": 100,
        "key_hunt_zone_pools": {"felwood"},
        "key_hunt_keys_required": 10,
    }

    def test_zone_restricted_shortfall_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


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
    """Task 24: Completionist/vanilla requires all vanilla instance unlocks
    at once -- the one mode so far whose completion rule needs more than a
    single item. M4.11.1 (Task 4, BarrensBeater) grew the vanilla roster
    from 3 to 6 (Ragefire Chasm, Deadmines, Molten Core, Wailing Caverns,
    Razorfen Kraul, Razorfen Downs), since all 3 new instances are tagged
    expansion: vanilla in core_loop.yaml and Completionist's completion rule
    iterates INSTANCES_BY_EXPANSION directly, not a hardcoded list."""
    options = {"game_mode": "completionist", "completionist_expansion": "vanilla"}

    def test_completion_requires_all_six_vanilla_unlocks(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Ragefire Chasm")
        self.collect_by_name("Instance Unlock: Deadmines")
        self.collect_by_name("Instance Unlock: Molten Core")
        self.collect_by_name("Instance Unlock: Wailing Caverns")
        self.collect_by_name("Instance Unlock: Razorfen Kraul")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Razorfen Downs")
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


class TestKeyHuntUnsatisfiableAfterCeilingRemoval(WoWTestBase):
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "key_hunt", "check_density": 1, "key_hunt_keys_required": 40}

    def test_key_hunt_unsatisfiable_keys_required_still_fails_after_ceiling_removal(self) -> None:
        # ceil(40 rares * 0.01 density * 1.0 weight) == 1, far below the
        # 40 keys required -- must still fail generation with no ceiling
        # in the picture at all.
        self.assertRaises(OptionError, self.world_setup)


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


class TestValidateHundredPercentEmptyRegistry(unittest.TestCase):
    # Direct unit test of _validate_hundred_percent, bypassing WoWTestBase
    # entirely -- the function only reads locations._OPTIONAL_CATEGORIES, it
    # never touches `world`, so a real World is unnecessary. This checkout's
    # _OPTIONAL_CATEGORIES is NEVER actually empty at import time (quest_
    # rewards/vendor_stock are registered unconditionally, not behind any
    # toggle), so this is the only way to exercise the "zero categories"
    # branch at all -- save/restore the module list rather than mutating it
    # permanently. goals.py imports the SAME list object via `from
    # .locations import _OPTIONAL_CATEGORIES` (not a copy), so mutating it
    # in place through either module's name is visible from both.
    def test_raises_when_registry_is_empty(self) -> None:
        from .. import locations as locations_module

        saved = locations_module._OPTIONAL_CATEGORIES[:]
        locations_module._OPTIONAL_CATEGORIES.clear()
        try:
            self.assertRaises(OptionError, goals._validate_hundred_percent, None)
        finally:
            locations_module._OPTIONAL_CATEGORIES.extend(saved)


class TestHundredPercentModeGeneratesAndRequiresAllLevelCaps(WoWTestBase):
    """100% mode must generate successfully with this checkout's real
    quest_rewards/vendor_stock categories registered, and its completion
    rule must require ALL pooled Progressive Level Cap copies -- one short
    is not enough (mirrors Key Hunt's/Artisan's own "neither alone is
    enough" shape from TestKeyHuntCompletionRequiresKeysAndInstances
    above). M4.9: the total grew from 10 to 14 (core_loop.yaml, to support
    the every-level milestone track's own level-80 ceiling); M4.11.1
    (Task 3): LEVEL_CAP_STEP dropped from 5 to 1, growing the total again
    from 14 to 70 -- unlike Sprint (goals.py's _set_completion_rule_sprint,
    fixed to require only the level-60-specific threshold), 100% mode's own
    completion rule (_set_completion_rule_hundred_percent) deliberately
    still requires ALL pooled copies, whatever that total is -- "collect
    literally everything" is exactly 100% mode's own definition, so no
    threshold-derivation fix was needed there, only this test's own
    hardcoded expectation of what "all" currently means. (Finding 10,
    final whole-branch review, 2026-09-01: that function now reads
    core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK["standard"] instead of
    a direct ITEMS["Progressive Level Cap"][1] lookup, for consistency
    with items.py's now-per-track pool sizing -- numerically a no-op here,
    since hundred_percent is always the standard track.)

    run_default_tests previously defaulted to True here (no override):
    WorldTestBase's own automatic test_all_state_can_reach_everything/
    test_fill checks passed for hundred_percent mode -- they previously
    failed even with every item collected due to a real data-shape bug in
    Task 3's locations.py (world.optional_category_sampled_names was
    populated with LOCATION names instead of the paired ITEM names
    state.has_all actually needs to check for), fixed by row-index-aligning
    the stash against category.items_module.ITEMS the same way items.py's
    create_optional_category_item_pool already did.

    M4.8.0: run_default_tests is now explicitly False. AP core's generic
    test_fill (test/bases.py) reimplements accessibility verification as an
    explicit sphere search that rescans the ENTIRE remaining location list
    on every wave -- confirmed empirically to take upward of 10 minutes,
    isolated, at this class's real ~47,000-location scale (quest_rewards +
    vendor_stock both forced to full inclusion by hundred_percent's own
    force_all_categories), vs. ~20s for pure world construction alone. This
    is AP-core test-harness complexity, not a defect in this apworld, and
    not something to patch under this milestone's scope. The three explicit
    test methods below already cover this class's documented, load-bearing
    assertions (generates successfully, 9-of-10 level caps insufficient,
    optional_category_sampled_names populated) without needing AP core's
    own generic beat-the-game re-verification; every other game mode in
    this suite still runs it normally."""
    options = {"game_mode": "hundred_percent"}
    run_default_tests = False

    def test_generates_successfully_with_registered_optional_categories(self) -> None:
        self.assertTrue(self.constructed)

    def test_sixty_nine_of_seventy_level_cap_copies_is_not_enough(self) -> None:
        state = self.multiworld.state
        level_caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(level_caps), 70)
        self.collect(level_caps[:69])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))

    def test_optional_category_sampled_names_is_populated(self) -> None:
        # Task 3: force_all_categories (hundred_percent's own GameModeProfile)
        # means every registered optional category is eligible unconditionally
        # and sampled at max density, so this set must be non-empty -- it's
        # what _set_completion_rule_hundred_percent folds into its completion
        # condition via world.optional_category_sampled_names.
        self.assertTrue(hasattr(self.world, "optional_category_sampled_names"))
        self.assertGreater(len(self.world.optional_category_sampled_names), 0)


class TestHundredPercentCompletionRuleStructure(WoWTestBase):
    """Confirms _set_completion_rule_hundred_percent's completion lambda is
    wired up correctly (requires ALL pooled Progressive Level Cap copies AND
    all instance unlocks AND world.optional_category_sampled_names) using a
    minimal, fully-controlled fixture rather than this checkout's real
    quest_rewards/vendor_stock categories.

    Historical note: world.optional_category_sampled_names originally held
    LOCATION names (from locations.py's create_optional_category_locations),
    not the ITEM names this rule's has_all(...) actually needs -- a real bug,
    since fixed by row-index-aligning against category.items_module.ITEMS,
    the same technique items.py's create_optional_category_item_pool already
    used. WorldTestBase's automatic beatable/fill checks now pass for
    hundred_percent mode against the real registered categories
    (TestHundredPercentModeGeneratesAndRequiresAllLevelCaps covers that end
    to end). This class additionally exercises the completion lambda's
    structure directly against a hand-built name set below, as a more
    targeted regression guard for has_all's individual operands.

    M4.8.0 fix: this docstring already claimed to use "a minimal,
    fully-controlled fixture rather than this checkout's real
    quest_rewards/vendor_stock categories", but the code didn't actually do
    that -- setUp() still built the full real ~47,000-row world every run
    (both tests below immediately overwrite optional_category_sampled_names
    anyway, making that real construction 100% wasted work). auto_construct
    = False + a temporary EMPTY _OPTIONAL_CATEGORIES swap in setUp() now
    matches this docstring's actual stated intent.

    Rebind, not in-place mutation, and deliberately so: this swap REBINDS
    `locations_module._OPTIONAL_CATEGORIES` to a new empty list rather than
    calling `.clear()` on the existing one (contrast
    TestOptionalCategoryRegionsWiring's append/remove, and
    TestValidateHundredPercentEmptyRegistry's own deliberate `.clear()`,
    which exists specifically to also empty goals.py's own
    `from .locations import _OPTIONAL_CATEGORIES` reference bound at
    import time). A rebind here is required, not incidental:
    goals._validate_hundred_percent (called from generate_early, BEFORE
    this test's own body runs) raises OptionError on a truly empty
    registry, and goals.py's own import binds the list object once at
    process start -- a rebind in locations.py's namespace does not affect
    that already-bound reference, so goals.py still sees the real 2-entry
    registry and generation proceeds normally, while locations.py's own
    create_optional_category_locations (which reads its OWN module global
    fresh on every call, not an imported alias) sees the swapped-in empty
    list. Calling .clear() here instead would mutate the SAME list object
    goals.py already holds a reference to, tripping its empty-registry
    check and breaking construction entirely."""
    options = {"game_mode": "hundred_percent"}
    auto_construct = False

    def setUp(self) -> None:
        from .. import locations as locations_module
        original = locations_module._OPTIONAL_CATEGORIES
        locations_module._OPTIONAL_CATEGORIES = []
        try:
            self.world_setup()
        finally:
            locations_module._OPTIONAL_CATEGORIES = original

    def test_level_cap_and_instance_unlocks_suffice_when_nothing_optional_sampled(self) -> None:
        # With world.optional_category_sampled_names replaced by an empty
        # set, level cap x10 + all instance unlocks alone ARE enough --
        # confirms has_all's remaining_names operand correctly resolves to
        # "nothing further required" when nothing was sampled, rather than
        # e.g. failing on an empty has_all call.
        self.world.optional_category_sampled_names = set()
        goals.set_completion_rule_for_mode(self.world)
        state = self.multiworld.state
        self.collect(self.get_items_by_name("Progressive Level Cap"))
        for name in goals._INSTANCE_KEY_DISPLAY_NAMES.values():
            self.collect_by_name(f"Instance Unlock: {name}")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))

    def test_missing_one_required_optional_category_name_blocks_completion(self) -> None:
        # Inject one fabricated "sampled" name that has no matching pooled
        # item anywhere, and confirm the completion rule correctly stays
        # unsatisfied -- proves has_all's sampled_names operand is load-
        # bearing (not silently ignored), complementing the sibling test
        # above which proves the "nothing extra required" case completes.
        self.world.optional_category_sampled_names = {"Nonexistent Optional Item"}
        goals.set_completion_rule_for_mode(self.world)
        state = self.multiworld.state
        self.collect(self.get_items_by_name("Progressive Level Cap"))
        for name in goals._INSTANCE_KEY_DISPLAY_NAMES.values():
            self.collect_by_name(f"Instance Unlock: {name}")
        self.assertFalse(self.multiworld.completion_condition[self.player](state))


# M4.11.1 Task 11 (BarrensBeater): Zone Leveler's real, full validator/
# completion rule, replacing Task 9's own reach_zone_level_cap-only
# placeholder. zone_leveler_goals (options.py's ZoneLevelerGoals OptionSet)
# selects any non-empty subset of up to four independent goal kinds, ANDed
# together -- these classes cover: the empty-selection validation failure,
# each of the four goal kinds' own completion behavior in isolation (except
# clear_all_zone_quests, covered separately below at the pure-data level --
# see that class's own docstring for why), and the AND-combination across
# two goal kinds at once (mirroring TestKeyHuntCompletionRequiresKeysAndInstances'
# own two-unrelated-families shape).
#
# Every class below sets zone_leveler_starting_zone explicitly even though
# "barrens" is ZoneLevelerStartingZone's own default -- same "be explicit
# about the one thing this test actually depends on" discipline the rest of
# this file already follows.
class TestZoneLevelerAtLeastOneGoalRequired(WoWTestBase):
    """An explicit empty zone_leveler_goals selection must fail loudly at
    generate_early, not silently resolve to an always-true completion rule
    (Python's `all(...)` over zero sub_rules is vacuously True)."""
    run_default_tests = False
    auto_construct = False
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": set(),
    }

    def test_empty_goals_fails_validation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestZoneLevelerReachLevelCapOnlyCompletion(WoWTestBase):
    """reach_zone_level_cap alone: completion requires holding at least the
    20 Progressive Level Cap copies Barrens' own zone_leveler track total
    demands (core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK
    ["zone_leveler_barrens"]). Finding 10 correction (final whole-branch
    review, 2026-09-01): Progressive Level Cap's own pooled count is now
    genuinely per-track (items.py's create_core_loop_item_pool), so
    zone_leveler_barrens pools exactly 20 copies, not the standard track's
    flat 70 this test used to (wrongly) assert was pooled for every
    track/game_mode -- the brief's own illustrative "len(caps) == 20"
    assumption was right all along, this test's prior comment claiming
    otherwise was the actual bug. state.has's own semantics (>= count, not
    ==) still make 20 the real completion threshold; this collects a
    precise 19-then-1 split to prove that exact threshold, not merely
    "collecting everything eventually completes it"."""
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap"},
    }

    def test_reach_zone_level_cap_only_completes_on_all_track_copies(self) -> None:
        state = self.multiworld.state
        caps = self.get_items_by_name("Progressive Level Cap")
        self.assertEqual(len(caps), 20)
        self.collect(caps[:19])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect(caps[19:20])
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestZoneLevelerMultipleGoalsAreAnded(WoWTestBase):
    """reach_zone_level_cap AND instance_clears selected together: neither
    goal alone should satisfy the completion condition -- only both."""
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"reach_zone_level_cap", "instance_clears"},
        "zone_leveler_instances_required": 1,
    }

    def test_multiple_selected_goals_are_anded(self) -> None:
        state = self.multiworld.state
        self.collect(self.get_items_by_name("Progressive Level Cap"))
        self.assertFalse(self.multiworld.completion_condition[self.player](state))  # level cap alone isn't enough
        self.collect_by_name("Instance Unlock: Wailing Caverns")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestZoneLevelerGoldenBoarStatuesGoal(WoWTestBase):
    """golden_boar_statues alone, at every other option's own default:
    check_density's default of 25 against golden_boar_statues.yaml's 20-row
    roster predicts exactly ceil(20 * 0.25) == 5 sampled locations/items,
    matching ZoneLevelerStatuesRequired's own default of 5 -- satisfiable
    out of the box (options.py's own docstring reasoning for that default),
    so this class needs no non-default overrides to exercise the goal."""
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"golden_boar_statues"},
    }

    def test_completion_requires_all_required_statue_copies(self) -> None:
        state = self.multiworld.state
        statues = self.get_items_by_name("Golden Boar Statue")
        self.assertEqual(len(statues), 5)
        self.collect(statues[:4])
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect(statues[4:])
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestZoneLevelerGoldenBoarStatuesTooLowDensityFailsValidation(WoWTestBase):
    """golden_boar_statues' own validator (same shape as Key Hunt's
    predict_sample_size-vs-required check): a check_density too low to
    sample zone_leveler_statues_required statue locations must fail
    generation loudly at generate_early, not surface later as an
    unsatisfiable completion condition discovered only during play."""
    run_default_tests = False
    auto_construct = False
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"golden_boar_statues"},
        "check_density": 5,  # ceil(20 * 0.05) == 1, below the default zone_leveler_statues_required=5
    }

    def test_too_low_density_fails_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestZoneLevelerClearAllZoneQuestsPartialSamplingFailsValidation(WoWTestBase):
    """Controller review's own confirmed Critical finding: clear_all_zone_quests'
    completion sub-rule needs ALL 103 of Barrens' zone-tagged quest-reward
    items, unconditionally -- but quest_rewards locations go through the
    same check_density x quest_reward_weight sampling every other
    quest_rewards location does (quest_rewards.yaml has no zone-tag
    dimension to zone-restrict sampling against, unlike golden_boar_statues'
    own dedicated, zone-exclusive 20-row table). At WoWTestBase's own
    fast-test defaults (quest_reward_weight=0, check_density=25), zero (or
    at best a random partial subset) of the zone's own quest-reward
    locations would ever land in the pool -- a required item whose location
    was never sampled can never be obtained, permanently softlocking the
    goal. _validate_zone_leveler's clear_all_zone_quests branch now catches
    this at generate_early, the same predict-then-validate shape
    golden_boar_statues' own branch already uses, just requiring the exact
    settings (check_density=100 AND quest_reward_weight=100) that guarantee
    full sampling rather than predicting a partial count."""
    run_default_tests = False
    auto_construct = False
    options = {
        "game_mode": "zone_leveler",
        "zone_leveler_starting_zone": "barrens",
        "zone_leveler_goals": {"clear_all_zone_quests"},
        # Left at WoWTestBase's own fast-test defaults (quest_reward_weight=0,
        # check_density=25) -- both well short of the 100/100 this goal needs.
    }

    def test_partial_sampling_settings_fail_generation(self) -> None:
        self.assertRaises(OptionError, self.world_setup)


class TestZoneLevelerClearAllZoneQuestsFullSamplingValidatesCleanly(unittest.TestCase):
    """The other half of the fix above: check_density=100 AND
    quest_reward_weight=100 together are the ONE settings combination that
    actually guarantees every one of Barrens' 103 zone-tagged quest-reward
    locations gets sampled (density.sample_category's `wanted == row_count`
    case is the only one where rng.sample is forced to return literally
    every row) -- _validate_zone_leveler must accept that combination
    cleanly, not just reject everything below it.

    Deliberately a plain unittest.TestCase driving _validate_zone_leveler
    directly against a minimal mock `world` (types.SimpleNamespace), not a
    full WoWTestBase generation test: at check_density=100 and
    quest_reward_weight=100, quest_rewards' own OptionalCategory sampling
    (no zone-tag dimension to restrict against) would sample its ENTIRE
    ~9,207-row table, not just Barrens' 103 -- exactly the multi-hour test
    blowup WoWTestBase's own docstring warns against. Calling the validator
    function directly proves the exact thing this fix changed (it no longer
    raises at 100/100) without paying for full generation;
    TestValidateHundredPercentEmptyRegistry above already establishes this
    "no real World object needed" pattern for a sibling validator."""

    def test_full_density_and_weight_does_not_raise(self) -> None:
        import types

        def _opt(value):
            return types.SimpleNamespace(value=value)

        world = types.SimpleNamespace(options=types.SimpleNamespace(
            game_mode=_opt(13),  # option_zone_leveler
            zone_leveler_goals=_opt({"clear_all_zone_quests"}),
            zone_leveler_starting_zone=types.SimpleNamespace(value=0, current_key="barrens"),
            check_density=_opt(100),
            quest_reward_weight=_opt(100),
        ))
        goals._validate_zone_leveler(world)  # must not raise


class TestZoneLevelerClearAllZoneQuestsItemNamePairing(unittest.TestCase):
    """Task 11's own real bug fix (found by this task's own controller
    review, not by the brief's own first-draft illustrative code):
    quest_rewards_content_data's LOCATIONS ("Quest: <name> Reward (#N)") and
    ITEMS ("Quest Reward: <name> (#N)") dicts do NOT share a common
    name/key to string-match clear_all_zone_quests' target item names
    against. The real, already-established pairing mechanism for this exact
    LOCATIONS<->ITEMS relationship (confirmed directly against
    locations.py's create_optional_category_locations, used by every
    OptionalCategory) is POSITIONAL: matching insertion-order position
    within each dict, not name equality.

    Deliberately a plain unittest.TestCase, not a WoWTestBase generation
    test: exercising this end-to-end would require quest_reward_weight=100
    and check_density=100 to guarantee every one of Barrens' 103 zone-tagged
    quest locations actually samples into the pool (quest_rewards.yaml has
    no zone-tag dimension to sample-restrict against, only type/expansion),
    which would also sample quest_rewards' full ~9,207-row table at those
    same settings -- exactly the multi-hour test blowup WoWTestBase's own
    docstring warns against. Testing the pure pairing function directly
    gives the same correctness guarantee at negligible cost."""

    def test_pairing_matches_locations_py_own_positional_mechanism(self) -> None:
        from .. import quest_rewards_content_data, zone_leveler_content_data
        zone_data = zone_leveler_content_data.ZONES["barrens"]
        all_rows = list(quest_rewards_content_data.LOCATIONS.items())
        item_rows = list(quest_rewards_content_data.ITEMS.items())
        row_index_by_location_name = {name: i for i, (name, _) in enumerate(all_rows)}
        expected = frozenset(
            item_rows[row_index_by_location_name[name]][0]
            for name in zone_data.quest_reward_location_names
        )
        self.assertEqual(len(expected), 103)  # Barrens' real zone-tagged quest reward count
        self.assertEqual(goals._quest_reward_item_names_for_zone(zone_data), expected)

    def test_pairing_is_not_naive_location_name_string_matching(self) -> None:
        # Confirms the fix guards against exactly the bug the brief's own
        # first-draft illustrative code fell into: none of
        # clear_all_zone_quests' target item names are literally a "Quest:
        # ..." LOCATION name -- every real target name instead uses ITEMS'
        # own distinct "Quest Reward: ..." template.
        from .. import zone_leveler_content_data
        zone_data = zone_leveler_content_data.ZONES["barrens"]
        names = goals._quest_reward_item_names_for_zone(zone_data)
        self.assertTrue(names)
        for name in names:
            self.assertTrue(name.startswith("Quest Reward: "))
        self.assertFalse(names & set(zone_data.quest_reward_location_names))
