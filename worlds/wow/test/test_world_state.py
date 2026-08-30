import unittest
from unittest.mock import Mock

from ..world_state import species_expansion_tags


class TestSpeciesExpansionTags(unittest.TestCase):
    def test_returns_vanilla_default_map_when_pipeline_b_has_not_run(self) -> None:
        world = Mock(spec=[])  # no pipeline_b_species_expansion_tags attribute at all
        result = species_expansion_tags(world)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        # Every value is a frozenset of real expansion-tag strings.
        for tags in result.values():
            self.assertIsInstance(tags, frozenset)
            self.assertTrue(tags.issubset({"vanilla", "tbc", "wotlk"}))

    def test_returns_pipeline_b_mutated_map_when_present(self) -> None:
        world = Mock(spec=[])
        world.pipeline_b_species_expansion_tags = {448: frozenset({"wotlk"})}
        result = species_expansion_tags(world)
        self.assertEqual(result, {448: frozenset({"wotlk"})})

    def test_vanilla_default_is_keyed_by_real_creature_entries_not_location_names(self) -> None:
        from .. import enemysanity_content_data
        world = Mock(spec=[])
        result = species_expansion_tags(world)
        # Every key must be a real creature_entry drawn from TRIGGERS, not a
        # location name string -- confirms the name->entry re-keying step
        # actually ran rather than accidentally passing TAGS through as-is.
        real_entries = {t["creature_entry"] for t in enemysanity_content_data.TRIGGERS.values()}
        self.assertTrue(set(result.keys()).issubset(real_entries))


class TestNothingBypassesTheSharedInterface(unittest.TestCase):
    def test_no_other_file_reads_the_private_vanilla_map_directly(self) -> None:
        import pathlib
        import re

        wow_dir = pathlib.Path(__file__).parent.parent
        offenders = []
        for path in wow_dir.rglob("*.py"):
            if path.name in ("world_state.py", "test_world_state.py"):
                continue
            text = path.read_text(encoding="utf-8")
            if re.search(r"_VANILLA_SPECIES_EXPANSION_TAGS", text):
                offenders.append(str(path))
        self.assertEqual(offenders, [], f"files reading the private map directly, must call species_expansion_tags() instead: {offenders}")


if __name__ == "__main__":
    unittest.main()
