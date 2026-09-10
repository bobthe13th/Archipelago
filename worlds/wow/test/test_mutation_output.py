import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from .. import mutation_output


class TestBuildMutationFileContents(unittest.TestCase):
    def test_includes_world_seed_and_categories(self):
        result = mutation_output.build_mutation_file_contents(
            "abc123", {"mobs": [("creature_template", 1, {"level": 30})]}
        )
        self.assertEqual(result["world_seed"], "abc123")
        self.assertEqual(result["categories"], {"mobs": [["creature_template", 1, {"level": 30}]]})

    def test_empty_pipeline_result_produces_empty_categories(self):
        result = mutation_output.build_mutation_file_contents("abc123", {})
        self.assertEqual(result["categories"], {})


class TestWriteMutationFile(unittest.TestCase):
    def test_writes_slot_name_mutations_json_into_output_directory(self):
        world = SimpleNamespace(player_name="Alice")
        with tempfile.TemporaryDirectory() as output_directory:
            mutation_output.write_mutation_file(
                world, output_directory, "abc123", {"mobs": [("creature_template", 1, {"level": 30})]}
            )
            path = os.path.join(output_directory, "Alice_mutations.json")
            self.assertTrue(os.path.isfile(path))
            with open(path, encoding="utf-8") as f:
                contents = json.load(f)
            self.assertEqual(contents["world_seed"], "abc123")
            self.assertEqual(contents["categories"]["mobs"], [["creature_template", 1, {"level": 30}]])
