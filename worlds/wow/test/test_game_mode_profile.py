import unittest
from types import SimpleNamespace

from ..game_mode_profile import (
    _DEFAULT_PROFILE,
    effective_check_density,
    get_profile,
    is_category_eligible,
)


class TestGameModeProfile(unittest.TestCase):
    def test_get_profile_returns_default_for_unregistered_mode(self) -> None:
        self.assertIs(get_profile(0), _DEFAULT_PROFILE)  # sprint
        self.assertIs(get_profile(1), _DEFAULT_PROFILE)  # key_hunt

    def test_get_profile_returns_hundred_percent_profile(self) -> None:
        profile = get_profile(12)
        self.assertTrue(profile.force_all_categories)
        self.assertTrue(profile.force_max_density)

    def test_is_category_eligible_default_profile_respects_toggle_off(self) -> None:
        world = SimpleNamespace(
            options=SimpleNamespace(game_mode=SimpleNamespace(value=0), include_quest_rewards=False)
        )
        category = SimpleNamespace(key="quest_rewards", toggle_option="include_quest_rewards")
        self.assertFalse(is_category_eligible(world, category))

    def test_is_category_eligible_default_profile_respects_toggle_on(self) -> None:
        world = SimpleNamespace(
            options=SimpleNamespace(game_mode=SimpleNamespace(value=0), include_quest_rewards=True)
        )
        category = SimpleNamespace(key="quest_rewards", toggle_option="include_quest_rewards")
        self.assertTrue(is_category_eligible(world, category))

    def test_is_category_eligible_hundred_percent_forces_true_regardless_of_toggle(self) -> None:
        world = SimpleNamespace(
            options=SimpleNamespace(game_mode=SimpleNamespace(value=12), include_quest_rewards=False)
        )
        category = SimpleNamespace(key="quest_rewards", toggle_option="include_quest_rewards")
        self.assertTrue(is_category_eligible(world, category))

    def test_effective_check_density_passes_through_for_default_profile(self) -> None:
        world = SimpleNamespace(
            options=SimpleNamespace(game_mode=SimpleNamespace(value=0), check_density=SimpleNamespace(value=42))
        )
        self.assertEqual(effective_check_density(world), 42)

    def test_effective_check_density_forces_100_for_hundred_percent(self) -> None:
        world = SimpleNamespace(
            options=SimpleNamespace(game_mode=SimpleNamespace(value=12), check_density=SimpleNamespace(value=0))
        )
        self.assertEqual(effective_check_density(world), 100)
