import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import environment_gameobject_visuals


def _fake_world(display_mode="vanilla", scale_mode="vanilla"):
    return SimpleNamespace(options=SimpleNamespace(
        environment_randomizer_gameobject_display_mode=SimpleNamespace(current_key=display_mode),
        environment_randomizer_gameobject_scale_mode=SimpleNamespace(current_key=scale_mode),
    ))


_FAKE_GAMEOBJECTS = {
    500: {"displayId": 100, "size": 1.0},
    501: {"displayId": 200, "size": 1.5},
}


def _patched_content():
    return patch.object(
        environment_gameobject_visuals, "gameobject_visuals_content_data",
        SimpleNamespace(GAMEOBJECTS=_FAKE_GAMEOBJECTS),
    )


# Larger pool for TestComposedPipeline below: after Pipeline A claims one
# entry, at least 4 candidates must remain so the display-id shuffle has a
# real chance of producing a non-identity permutation -- a 2-entry pool
# (like _FAKE_GAMEOBJECTS above) would leave only 1 candidate after a claim,
# and shuffling a single-element list is ALWAYS an identity no-op regardless
# of seed, which is exactly the vacuous-test trap M5.6.0/M5.6.2/M5.6.3 fell
# into. Verified below (see TestComposedPipeline) that the actual sub-seed
# this test drives through run_category() produces a genuinely non-identity
# shuffle against this specific fixture.
_FAKE_GAMEOBJECTS_LARGE = {
    500: {"displayId": 100, "size": 1.0},
    501: {"displayId": 200, "size": 1.2},
    502: {"displayId": 300, "size": 1.4},
    503: {"displayId": 400, "size": 1.6},
    504: {"displayId": 500, "size": 1.8},
}


def _patched_large_content():
    return patch.object(
        environment_gameobject_visuals, "gameobject_visuals_content_data",
        SimpleNamespace(GAMEOBJECTS=_FAKE_GAMEOBJECTS_LARGE),
    )


class TestCandidateRows(unittest.TestCase):
    def test_both_vanilla_returns_no_candidates(self):
        world = _fake_world()
        with _patched_content():
            self.assertEqual(environment_gameobject_visuals.candidate_rows(world), [])

    def test_display_only(self):
        world = _fake_world(display_mode="shuffle")
        with _patched_content():
            rows = environment_gameobject_visuals.candidate_rows(world)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[0] == "gameobject_template" for row in rows))
        _table, _entry, payload = rows[0]
        self.assertIn("displayId", payload)
        self.assertNotIn("size", payload)

    def test_display_and_scale_together_produce_one_merged_row(self):
        world = _fake_world(display_mode="shuffle", scale_mode="shuffle")
        with _patched_content():
            rows = environment_gameobject_visuals.candidate_rows(world)
        self.assertEqual(len(rows), 2)  # one row per gameobject, not two
        _table, _entry, payload = rows[0]
        self.assertIn("displayId", payload)
        self.assertIn("size", payload)


class TestMutate(unittest.TestCase):
    def test_display_shuffle_only_uses_ids_already_in_pool(self):
        rows = [
            ("gameobject_template", 500, {"displayId": 100, "_display_mode": "shuffle"}),
            ("gameobject_template", 501, {"displayId": 200, "_display_mode": "shuffle"}),
        ]
        # NOTE: seed "fixed-seed" (the brief's own example seed) produces an
        # IDENTITY shuffle of this 2-item pool ([100, 200] -> [100, 200]),
        # which would make mutate() return [] and silently skip every
        # assertion below -- exactly the vacuous-test trap called out in
        # this milestone's own history (M5.6.0/M5.6.2/M5.6.3). Verified by
        # actually running both seeds against this fixture: "fixed-seed-2"
        # produces a genuine swap ([100, 200] -> [200, 100]).
        rng = random.Random("fixed-seed-2")
        result = environment_gameobject_visuals.mutate(rows, rng)
        self.assertTrue(result, "expected a non-empty, genuinely-swapped mutation result")
        for _t, _e, payload in result:
            if "displayId" in payload:
                self.assertIn(payload["displayId"], {100, 200})

    def test_scale_shuffle_stays_within_bounds(self):
        rows = [("gameobject_template", 500, {"size": 1.0, "_scale_mode": "shuffle"})]
        rng = random.Random("fixed-seed")
        saw_non_empty = False
        for _ in range(20):
            result = environment_gameobject_visuals.mutate(rows, rng)
            if result:
                saw_non_empty = True
            for _t, _e, payload in result:
                if "size" in payload:
                    self.assertTrue(0.5 <= payload["size"] <= 2.0)
        self.assertTrue(saw_non_empty, "expected at least one reroll to actually change size")

    def test_no_control_keys_leak_into_returned_payload(self):
        rows = [("gameobject_template", 500, {"displayId": 100, "size": 1.0, "_display_mode": "shuffle", "_scale_mode": "shuffle"})]
        rng = random.Random("fixed-seed")
        result = environment_gameobject_visuals.mutate(rows, rng)
        self.assertTrue(result, "expected a non-empty mutation result (size always rerolls)")
        for _t, _e, payload in result:
            for key in payload:
                self.assertFalse(key.startswith("_"))

    def test_empty_rows_returns_empty(self):
        rng = random.Random("fixed-seed")
        self.assertEqual(environment_gameobject_visuals.mutate([], rng), [])


class TestComposedPipeline(unittest.TestCase):
    def test_claimed_row_excluded_and_survives_json_round_trip(self):
        from .. import mutation_pipeline, mutation_output
        import json

        category = mutation_pipeline.MutationCategory(
            key="environment_gameobject_visuals",
            candidate_rows=environment_gameobject_visuals.candidate_rows,
            mutate=environment_gameobject_visuals.mutate,
            invariant_rules=[],
        )
        world = _fake_world(display_mode="shuffle")
        # Use the LARGE fixture, not the 2-entry one above: claiming entry
        # 500 out of only 2 candidates would leave a single-element pool,
        # and shuffling one element is always an identity no-op -- the
        # exact vacuous trap this task must avoid. With the 5-entry pool,
        # 4 candidates remain after the claim. Verified directly (by
        # replicating mutation_pipeline's derive_sub_seed + rng.shuffle
        # against world_seed="some-seed", category
        # "environment_gameobject_visuals", attempt 0) that the resulting
        # sub-seed shuffles [200, 300, 400, 500] to [500, 400, 200, 300] --
        # every element moves, so the mutation is genuinely non-empty.
        with _patched_large_content():
            result = mutation_pipeline.run_category(category, world, "some-seed", claimed={("gameobject_template", 500)})

        self.assertTrue(result, "expected a non-empty, genuinely-shuffled mutation result")

        result_entries = {key for _table, key, _payload in result}
        self.assertNotIn(500, result_entries)

        contents = mutation_output.build_mutation_file_contents("some-seed", {"environment_gameobject_visuals": result})
        json.dumps(contents)  # proves int keys + no control keys survive serialization
