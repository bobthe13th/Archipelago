import unittest

from .bases import WoWTestBase


class TestRaidloggerGoalClassicToTbc(WoWTestBase):
    options = {"game_mode": "raidlogger", "raidlogger_expansions": "classic_to_tbc"}

    def test_completion_requires_sunwell_plateau_clear_only(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Sunwell Plateau")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


class TestRaidloggerGoalClassicToWotlk(WoWTestBase):
    options = {"game_mode": "raidlogger", "raidlogger_expansions": "classic_to_wotlk"}

    def test_completion_requires_icecrown_citadel_clear_only(self) -> None:
        state = self.multiworld.state
        self.assertFalse(self.multiworld.completion_condition[self.player](state))
        self.collect_by_name("Instance Unlock: Icecrown Citadel")
        self.assertTrue(self.multiworld.completion_condition[self.player](state))


if __name__ == "__main__":
    unittest.main()
