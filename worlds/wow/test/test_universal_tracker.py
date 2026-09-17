# Archipelago/worlds/wow/test/test_universal_tracker.py
"""M6.2.8: real, standard Archipelago Universal Tracker (UT) integration.
interpret_slot_data is a plain per-world method UT calls by duck-typing
(confirmed real via 10 other in-repo apworld implementations -- see this
milestone's plan Global Constraints) -- there is no base-class hook or
separate UT tracker-world fork anywhere in this checkout."""
import pathlib
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


class TestPipelineBSiloRuleHolds(unittest.TestCase):
    """M6.2.8: interpret_slot_data's own no-op reasoning (Task 1) depends
    entirely on the real, current fact that this apworld's reachability
    logic (rules.py/locations.py/items.py) never consumes Pipeline B's
    mutation output -- the master spec's "silo rule." This is a durable
    regression guard, not a one-time investigation note: if a future
    change makes any of these three files reference Pipeline B's mutation
    machinery, this test fails loudly, forcing that change's author to
    also revisit interpret_slot_data's own reasoning and this milestone's
    manual verification checklist -- rather than silently reopening a
    UT-desync risk this milestone closed."""

    _WOW_DIR = pathlib.Path(__file__).resolve().parent.parent
    _REACHABILITY_FILES = ("rules.py", "locations.py", "items.py")
    _PIPELINE_B_MARKERS = (
        "mutation_pipeline",
        "_pipeline_b_result",
        "_pipeline_b_day_night",
        "mobs_spawns",
        "mobs_level",
        "day_night",
        "environment_weather",
        "environment_creature_flavor",
        "environment_gameobject_visuals",
        "environment_model_scale_name",
    )

    def test_reachability_logic_never_references_pipeline_b_mutation_output(self) -> None:
        for filename in self._REACHABILITY_FILES:
            source = (self._WOW_DIR / filename).read_text(encoding="utf-8")
            for marker in self._PIPELINE_B_MARKERS:
                self.assertNotIn(
                    marker, source,
                    f"{filename} now references Pipeline B marker {marker!r} -- this breaks the "
                    "silo-rule assumption WoWWorld.interpret_slot_data's own no-op reasoning depends "
                    "on (M6.2.8 plan Global Constraints). If this is a deliberate, reviewed change "
                    "(e.g. M5.2 faction/reputation shuffle landing with real reachability impact), "
                    "update interpret_slot_data's docstring, add the real slot_data mirroring per "
                    "docs/testing/m6.2.8-manual-verification-checklist.md's Future Extension "
                    "Contract, and update this test's own marker list/reasoning to match -- do not "
                    "just widen or delete this assertion."
                )
