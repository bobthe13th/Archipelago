import unittest
from types import SimpleNamespace

from .. import game_mode_profile as game_mode_profile_module
from ..game_mode_profile import (
    _DEFAULT_PROFILE,
    GameModeProfile,
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

    def test_is_category_eligible_default_profile_with_no_restriction(self) -> None:
        # M4.8.0: is_category_eligible no longer reads a per-category toggle
        # option -- tag/weight filtering (locations.py) owns "will this
        # category actually contribute locations"; this function only
        # answers "is the category ALLOWED to be considered for this game
        # mode" (eligible_categories/force_all_categories).
        world = SimpleNamespace(options=SimpleNamespace(game_mode=SimpleNamespace(value=0)))
        category = SimpleNamespace(key="quest_rewards")
        self.assertTrue(is_category_eligible(world, category))

    def test_is_category_eligible_respects_eligible_categories_restriction(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(game_mode=SimpleNamespace(value=99)))
        category = SimpleNamespace(key="quest_rewards")
        original_profiles = game_mode_profile_module._PROFILES
        game_mode_profile_module._PROFILES = {99: GameModeProfile(eligible_categories={"vendor_stock"})}
        try:
            self.assertFalse(is_category_eligible(world, category))
        finally:
            game_mode_profile_module._PROFILES = original_profiles

    def test_is_category_eligible_hundred_percent_is_true(self) -> None:
        world = SimpleNamespace(options=SimpleNamespace(game_mode=SimpleNamespace(value=12)))
        category = SimpleNamespace(key="quest_rewards")
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

    def test_zone_leveler_has_a_registered_profile(self) -> None:
        profile = get_profile(13)
        self.assertIsNot(profile, _DEFAULT_PROFILE)
