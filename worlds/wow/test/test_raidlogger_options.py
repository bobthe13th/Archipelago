import unittest

from ..options import GameMode, RaidloggerExpansions


class TestRaidloggerOptions(unittest.TestCase):
    def test_game_mode_has_raidlogger_value_14(self) -> None:
        self.assertEqual(GameMode.option_raidlogger, 14)

    def test_raidlogger_expansions_has_exactly_the_two_chained_values(self) -> None:
        self.assertEqual(RaidloggerExpansions.option_classic_to_tbc, 0)
        self.assertEqual(RaidloggerExpansions.option_classic_to_wotlk, 1)

    def test_raidlogger_expansions_default_is_the_full_chain(self) -> None:
        self.assertEqual(RaidloggerExpansions.default, RaidloggerExpansions.option_classic_to_wotlk)


if __name__ == "__main__":
    unittest.main()
