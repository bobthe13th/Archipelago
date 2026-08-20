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


class TestKeyHuntNotYetImplemented(WoWTestBase):
    """Every GameMode value beyond Sprint/Classic/Burning Crusade/Wrath must
    still raise OptionError -- this is the regression guard for Task 22's
    "land both in the same commit" requirement (a new GameMode value must
    never become silently selectable before its own task lands)."""
    run_default_tests = False
    auto_construct = False
    options = {"game_mode": "key_hunt"}

    def test_key_hunt_fails_generation(self) -> None:
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
