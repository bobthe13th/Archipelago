# Archipelago/worlds/wow/test/test_universal_tracker.py
"""M6.2.8: real, standard Archipelago Universal Tracker (UT) integration.
interpret_slot_data is a plain per-world method UT calls by duck-typing
(confirmed real via 10 other in-repo apworld implementations -- see this
milestone's plan Global Constraints) -- there is no base-class hook or
separate UT tracker-world fork anywhere in this checkout."""
import unittest

from . import bases


class TestInterpretSlotData(bases.WoWTestBase):
    options = {}

    def test_returns_input_unchanged(self) -> None:
        """Real investigation (this milestone) found nothing in this
        apworld currently needs UT-side reinterpretation -- see the plan's
        Global Constraints for the full, source-cited reasoning. This is
        therefore, honestly, a passthrough today, matching several other
        real apworlds already in this exact checkout (worlds/messenger,
        worlds/tunic, worlds/yugioh06, worlds/osrs) that are in the
        identical position."""
        world = self.multiworld.worlds[self.player]
        sample_slot_data = {"world_seed": "abc123", "instance_clear_mode": "final_boss_only"}
        result = world.interpret_slot_data(sample_slot_data)
        self.assertEqual(result, sample_slot_data)
        self.assertIs(result, sample_slot_data)

    def test_returns_empty_dict_unchanged(self) -> None:
        world = self.multiworld.worlds[self.player]
        self.assertEqual(world.interpret_slot_data({}), {})

    def test_real_fill_slot_data_output_round_trips_through_interpret_slot_data(self) -> None:
        """The real, actual slot_data this seed's fill_slot_data() produces
        must itself survive interpret_slot_data unchanged -- not just a
        synthetic sample dict above."""
        world = self.multiworld.worlds[self.player]
        real_slot_data = world.fill_slot_data()
        self.assertEqual(world.interpret_slot_data(real_slot_data), real_slot_data)
