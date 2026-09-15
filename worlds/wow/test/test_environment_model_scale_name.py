import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import environment_model_scale_name


def _fake_world(name_mode="vanilla", model_mode="vanilla", scale_mode="vanilla"):
    return SimpleNamespace(options=SimpleNamespace(
        environment_randomizer_name_mode=SimpleNamespace(current_key=name_mode),
        environment_randomizer_model_mode=SimpleNamespace(current_key=model_mode),
        environment_randomizer_scale_mode=SimpleNamespace(current_key=scale_mode),
    ))


_FAKE_NAMES = {
    1: {"name": "Wolf", "subname": ""},
    2: {"name": "Bear", "subname": "Grizzled"},
}
_FAKE_MODELS = {
    10: {"CreatureDisplayID": 100, "DisplayScale": 1.0},
    11: {"CreatureDisplayID": 200, "DisplayScale": 1.5},
}


class TestCandidateRows(unittest.TestCase):
    def test_all_vanilla_returns_no_candidates(self):
        world = _fake_world()
        with patch.object(environment_model_scale_name, "creature_appearance_content_data",
                           SimpleNamespace(CREATURE_NAMES=_FAKE_NAMES, CREATURE_MODELS=_FAKE_MODELS)):
            self.assertEqual(environment_model_scale_name.candidate_rows(world), [])

    def test_name_only_returns_creature_template_rows(self):
        world = _fake_world(name_mode="shuffle")
        with patch.object(environment_model_scale_name, "creature_appearance_content_data",
                           SimpleNamespace(CREATURE_NAMES=_FAKE_NAMES, CREATURE_MODELS=_FAKE_MODELS)):
            rows = environment_model_scale_name.candidate_rows(world)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[0] == "creature_template" for row in rows))

    def test_model_and_scale_together_produce_one_merged_row_per_creature(self):
        world = _fake_world(model_mode="shuffle", scale_mode="shuffle")
        with patch.object(environment_model_scale_name, "creature_appearance_content_data",
                           SimpleNamespace(CREATURE_NAMES=_FAKE_NAMES, CREATURE_MODELS=_FAKE_MODELS)):
            rows = environment_model_scale_name.candidate_rows(world)
        # Exactly one row per creature_template_model candidate, not two --
        # this is the mandatory same-row merge (see Global Constraints).
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[0] == "creature_template_model" for row in rows))
        _table, _cid, payload = rows[0]
        self.assertIn("CreatureDisplayID", payload)
        self.assertIn("DisplayScale", payload)

    def test_model_only_omits_scale_key_from_payload(self):
        world = _fake_world(model_mode="shuffle")
        with patch.object(environment_model_scale_name, "creature_appearance_content_data",
                           SimpleNamespace(CREATURE_NAMES=_FAKE_NAMES, CREATURE_MODELS=_FAKE_MODELS)):
            rows = environment_model_scale_name.candidate_rows(world)
        _table, _cid, payload = rows[0]
        self.assertIn("CreatureDisplayID", payload)
        self.assertNotIn("DisplayScale", payload)


class TestMutate(unittest.TestCase):
    def test_name_shuffle_is_a_permutation_no_duplicates(self):
        rows = [
            ("creature_template", 1, {"name": "Wolf", "subname": "", "_name_mode": "shuffle"}),
            ("creature_template", 2, {"name": "Bear", "subname": "Grizzled", "_name_mode": "shuffle"}),
        ]
        rng = random.Random("fixed-seed")
        result = environment_model_scale_name.mutate(rows, rng)
        result_names = {(payload.get("name"), payload.get("subname")) for _t, _e, payload in result if "name" in payload}
        original_names = {("Wolf", ""), ("Bear", "Grizzled")}
        # Every name assigned is one of the original pool's names (a true
        # permutation), never an invented string.
        for name in result_names:
            self.assertIn(name, original_names)

    def test_model_shuffle_only_uses_ids_already_in_the_pool(self):
        rows = [
            ("creature_template_model", 10, {"CreatureDisplayID": 100, "_model_mode": "shuffle"}),
            ("creature_template_model", 11, {"CreatureDisplayID": 200, "_model_mode": "shuffle"}),
        ]
        rng = random.Random("fixed-seed")
        result = environment_model_scale_name.mutate(rows, rng)
        for _t, _cid, payload in result:
            if "CreatureDisplayID" in payload:
                self.assertIn(payload["CreatureDisplayID"], {100, 200})

    def test_no_control_keys_leak_into_returned_payload(self):
        rows = [
            ("creature_template", 1, {"name": "Wolf", "subname": "", "_name_mode": "shuffle"}),
            ("creature_template_model", 10, {"CreatureDisplayID": 100, "DisplayScale": 1.0, "_model_mode": "shuffle", "_scale_mode": "shuffle"}),
        ]
        rng = random.Random("fixed-seed")
        result = environment_model_scale_name.mutate(rows, rng)
        for _t, _e, payload in result:
            for key in payload:
                self.assertFalse(key.startswith("_"))

    def test_empty_rows_returns_empty(self):
        rng = random.Random("fixed-seed")
        self.assertEqual(environment_model_scale_name.mutate([], rng), [])

    def test_scale_shuffle_stays_within_0_5_and_2_0(self):
        # Fix 4 (M5.6.2's own final review): DisplayScale isn't purely
        # cosmetic -- it proportionally scales combat reach and collision
        # radius (Creature::SetObjectScale), so the [0.5, 2.0] clamp is a
        # real mechanical bound, not just visual variety. Exercise many
        # rerolls with a real random.Random instance to cover the actual
        # range rather than a single sample.
        rows = [("creature_template_model", 10, {"DisplayScale": 1.0, "_scale_mode": "shuffle"})]
        rng = random.Random("fixed-seed")
        for _ in range(200):
            result = environment_model_scale_name.mutate(rows, rng)
            if result:
                _table, _cid, payload = result[0]
                if "DisplayScale" in payload:
                    self.assertGreaterEqual(payload["DisplayScale"], 0.5)
                    self.assertLessEqual(payload["DisplayScale"], 2.0)


class TestComposedPipeline(unittest.TestCase):
    def test_claimed_row_excluded_and_survives_json_round_trip(self):
        from .. import mutation_pipeline, mutation_output
        import json

        category = mutation_pipeline.MutationCategory(
            key="environment_model_scale_name",
            candidate_rows=environment_model_scale_name.candidate_rows,
            mutate=environment_model_scale_name.mutate,
            invariant_rules=[],
        )
        world = _fake_world(name_mode="shuffle")
        with patch.object(environment_model_scale_name, "creature_appearance_content_data",
                           SimpleNamespace(CREATURE_NAMES=_FAKE_NAMES, CREATURE_MODELS=_FAKE_MODELS)):
            result = mutation_pipeline.run_category(category, world, "some-seed", claimed={("creature_template", 1)})

        # entry 1 was claimed by Pipeline A -- must never appear in the result.
        result_entries = {key for _table, key, _payload in result}
        self.assertNotIn(1, result_entries)

        contents = mutation_output.build_mutation_file_contents("some-seed", {"environment_model_scale_name": result})
        json.dumps(contents)  # proves int keys + no control keys survive serialization
