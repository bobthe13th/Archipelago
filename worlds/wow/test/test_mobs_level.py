import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import mobs_level


def _fake_world(mode: str):
    return SimpleNamespace(
        options=SimpleNamespace(mob_randomizer_level_mode=SimpleNamespace(current_key=mode))
    )


_FAKE_TEMPLATES = {
    1: {"minlevel": 10, "maxlevel": 12, "zone_tags": ["barrens"]},
    2: {"minlevel": 11, "maxlevel": 13, "zone_tags": ["barrens"]},
    3: {"minlevel": 50, "maxlevel": 50, "zone_tags": ["icecrown"]},
    4: {"minlevel": 5, "maxlevel": 5, "zone_tags": []},
}


class TestCandidateRows(unittest.TestCase):
    def test_vanilla_mode_returns_no_candidates(self):
        world = _fake_world("vanilla")
        with patch.object(mobs_level.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            self.assertEqual(mobs_level.candidate_rows(world), [])

    def test_zone_scaled_mode_returns_one_row_per_template_with_shift_group(self):
        world = _fake_world("zone_scaled")
        with patch.object(mobs_level.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            rows = mobs_level.candidate_rows(world)
        self.assertEqual(len(rows), 4)
        row_by_entry = {entry: payload for _table, entry, payload in rows}
        self.assertEqual(row_by_entry[1]["_shift_group"], row_by_entry[2]["_shift_group"])
        self.assertNotEqual(row_by_entry[1]["_shift_group"], row_by_entry[3]["_shift_group"])

    def test_individual_spawn_mode_gives_every_entry_its_own_shift_group(self):
        world = _fake_world("individual_spawn")
        with patch.object(mobs_level.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            rows = mobs_level.candidate_rows(world)
        shift_groups = {payload["_shift_group"] for _table, _entry, payload in rows}
        self.assertEqual(len(shift_groups), 4)  # every entry is its own group


class TestMutate(unittest.TestCase):
    def test_shared_shift_group_gets_the_same_shift(self):
        rows = [
            ("creature_template", 1, {"minlevel": 10, "maxlevel": 12, "_shift_group": "barrens"}),
            ("creature_template", 2, {"minlevel": 11, "maxlevel": 13, "_shift_group": "barrens"}),
        ]
        rng = random.Random("fixed-seed")
        result = mobs_level.mutate(rows, rng)
        result_by_entry = {entry: payload for _table, entry, payload in result}
        shift_1 = result_by_entry[1]["minlevel"] - 10
        shift_2 = result_by_entry[2]["minlevel"] - 11
        self.assertEqual(shift_1, shift_2)

    def test_preserves_min_max_spread(self):
        rows = [("creature_template", 1, {"minlevel": 10, "maxlevel": 12, "_shift_group": "x"})]
        rng = random.Random("fixed-seed")
        result = mobs_level.mutate(rows, rng)
        _table, _entry, payload = result[0]
        self.assertEqual(payload["maxlevel"] - payload["minlevel"], 2)

    def test_clamps_to_1_and_80(self):
        rows = [("creature_template", 1, {"minlevel": 1, "maxlevel": 3, "_shift_group": "x"})]
        rng = random.Random("fixed-seed")
        for _ in range(50):  # run many times to exercise both clamp directions across random shifts
            result = mobs_level.mutate(rows, rng)
            if result:
                _table, _entry, payload = result[0]
                self.assertGreaterEqual(payload["minlevel"], 1)
                self.assertLessEqual(payload["maxlevel"], 80)

    def test_no_shift_group_key_leaks_into_returned_payload(self):
        rows = [("creature_template", 1, {"minlevel": 10, "maxlevel": 12, "_shift_group": "x"})]
        rng = random.Random("fixed-seed")
        result = mobs_level.mutate(rows, rng)
        for _table, _entry, payload in result:
            self.assertNotIn("_shift_group", payload)

    def test_unchanged_rows_are_not_returned(self):
        # A shift that happens to roll to 0 for both min/max must be excluded
        # from the diff -- force this via a zero-only Random-like stub.
        class _ZeroRandom:
            def randint(self, a, b):
                return 0
        rows = [("creature_template", 1, {"minlevel": 10, "maxlevel": 12, "_shift_group": "x"})]
        result = mobs_level.mutate(rows, _ZeroRandom())
        self.assertEqual(result, [])

    def test_empty_rows_returns_empty(self):
        rng = random.Random("fixed-seed")
        self.assertEqual(mobs_level.mutate([], rng), [])
