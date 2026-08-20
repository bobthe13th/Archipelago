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
