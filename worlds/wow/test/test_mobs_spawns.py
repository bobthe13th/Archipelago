import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import mobs_spawns
from ..mutation_invariants import InvariantViolation


def _fake_world(mode: str):
    return SimpleNamespace(
        options=SimpleNamespace(mob_randomizer_spawn_mode=SimpleNamespace(current_key=mode))
    )


_FAKE_TEMPLATES = {
    1: {"minlevel": 10, "rank": 0, "type": 1, "ai_name": "", "script_name": "", "home_maps": [0], "shuffle_excluded": False},
    2: {"minlevel": 11, "rank": 0, "type": 1, "ai_name": "", "script_name": "", "home_maps": [0], "shuffle_excluded": False},
    3: {"minlevel": 10, "rank": 3, "type": 1, "ai_name": "", "script_name": "boss_ragnaros", "home_maps": [409], "shuffle_excluded": False},
    4: {"minlevel": 50, "rank": 0, "type": 1, "ai_name": "SmartAI", "script_name": "", "home_maps": [0], "shuffle_excluded": False},
    5: {"minlevel": 10, "rank": 0, "type": 11, "ai_name": "", "script_name": "npc_pet_pri_lightwell", "home_maps": [0], "shuffle_excluded": True},
}
_FAKE_SPAWNS = {
    100: {"template_entry": 1, "map": 0, "shuffle_excluded": False},
    101: {"template_entry": 2, "map": 0, "shuffle_excluded": False},
    102: {"template_entry": 3, "map": 409, "shuffle_excluded": False},
    103: {"template_entry": 1, "map": 0, "shuffle_excluded": True},
    104: {"template_entry": 5, "map": 0, "shuffle_excluded": False},
}


class TestClassificationForRank(unittest.TestCase):
    def test_rank_0_is_normal(self):
        self.assertEqual(mobs_spawns._classification_for_rank(0), "normal")

    def test_ranks_1_and_2_are_elite(self):
        self.assertEqual(mobs_spawns._classification_for_rank(1), "elite")
        self.assertEqual(mobs_spawns._classification_for_rank(2), "elite")

    def test_ranks_3_and_4_are_boss(self):
        self.assertEqual(mobs_spawns._classification_for_rank(3), "boss")
        self.assertEqual(mobs_spawns._classification_for_rank(4), "boss")


class TestLevelBand(unittest.TestCase):
    def test_buckets_by_five(self):
        self.assertEqual(mobs_spawns._level_band(10), 2)
        self.assertEqual(mobs_spawns._level_band(14), 2)
        self.assertEqual(mobs_spawns._level_band(15), 3)


class TestCandidateRows(unittest.TestCase):
    def test_vanilla_mode_returns_no_candidates(self):
        world = _fake_world("vanilla")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS):
            self.assertEqual(mobs_spawns.candidate_rows(world), [])

    def test_shuffle_groups_mode_returns_one_row_per_non_excluded_spawn(self):
        world = _fake_world("shuffle_groups")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            rows = mobs_spawns.candidate_rows(world)
        # 5 fake spawns total; 103 is guid-excluded and 104's template (entry
        # 5) is excluded -- both must be skipped, leaving 100/101/102.
        self.assertEqual(len(rows), 3)
        guids = {guid for _table, guid, _payload in rows}
        self.assertEqual(guids, {100, 101, 102})
        for table_name, _guid, payload in rows:
            self.assertEqual(table_name, "creature")
            self.assertEqual(payload["_shuffle_mode"], "shuffle_groups")

    def test_excluded_guid_never_produces_a_candidate(self):
        world = _fake_world("shuffle_groups")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            rows = mobs_spawns.candidate_rows(world)
        self.assertNotIn(103, {guid for _table, guid, _payload in rows})

    def test_spawn_whose_current_template_is_excluded_never_produces_a_candidate(self):
        world = _fake_world("shuffle_groups")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            rows = mobs_spawns.candidate_rows(world)
        # Spawn 104 currently hosts entry 5 (shuffle_excluded=True) -- must
        # never be reassigned away from it either (two-sided exclusion).
        self.assertNotIn(104, {guid for _table, guid, _payload in rows})


class TestMutateShuffleGroups(unittest.TestCase):
    def test_only_reassigns_within_same_band_and_classification(self):
        rows = [
            ("creature", 100, {"id": 1, "_shuffle_mode": "shuffle_groups", "_home_map": 0}),
            ("creature", 101, {"id": 2, "_shuffle_mode": "shuffle_groups", "_home_map": 0}),
        ]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            result = mobs_spawns.mutate(rows, rng)
        for _table, _guid, payload in result:
            self.assertIn(payload["id"], (1, 2))  # only entries 1/2 share (band=2, normal)

    def test_boss_only_reassigned_among_bosses(self):
        rows = [("creature", 102, {"id": 3, "_shuffle_mode": "shuffle_groups", "_home_map": 409})]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            result = mobs_spawns.mutate(rows, rng)
        # Entry 3 is the only boss-classified template in the fixture -- its
        # own group pool has exactly one member (itself), so mutate() must
        # never reassign it away (no other real candidate exists).
        self.assertEqual(result, [])

    def test_excluded_entry_never_becomes_a_candidate(self):
        # Entry 5 (shuffle_excluded=True) shares entries 1/2's (band=2,
        # normal) group but must never be chosen -- placing a Totem-type
        # template on a plain creature spawn crashes core's
        # TotemAI::TotemAI assertion (`c->IsTotem()`), since totems only
        # ever exist via the real spell-summon code path.
        rows = [("creature", 100, {"id": 1, "_shuffle_mode": "shuffle_groups", "_home_map": 0})]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            for _ in range(50):
                result = mobs_spawns.mutate(rows, rng)
                if result:
                    self.assertNotEqual(result[0][2]["id"], 5)

    def test_no_control_keys_leak_into_returned_payload(self):
        rows = [
            ("creature", 100, {"id": 1, "_shuffle_mode": "shuffle_groups", "_home_map": 0}),
            ("creature", 101, {"id": 2, "_shuffle_mode": "shuffle_groups", "_home_map": 0}),
        ]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            result = mobs_spawns.mutate(rows, rng)
        for _table, _guid, payload in result:
            self.assertNotIn("_shuffle_mode", payload)
            self.assertNotIn("_home_map", payload)


class TestMutateShuffleAll(unittest.TestCase):
    def test_excluded_entry_never_becomes_a_candidate(self):
        # Entry 5 (shuffle_excluded=True, home_maps=[0]) must never be
        # chosen for any spawn, scripted-pool or clean-pool alike -- same
        # TotemAI assertion risk as shuffle_groups.
        rows = [("creature", 100, {"id": 1, "_shuffle_mode": "shuffle_all", "_home_map": 0})]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            for _ in range(50):
                result = mobs_spawns.mutate(rows, rng)
                if result:
                    self.assertNotEqual(result[0][2]["id"], 5)

    def test_scripted_template_never_becomes_a_candidate_off_its_home_map(self):
        # Entry 3 (script_name="boss_ragnaros", home_maps=[409]) must never
        # be assigned to a spawn on map 0.
        rows = [("creature", 100, {"id": 1, "_shuffle_mode": "shuffle_all", "_home_map": 0})]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            for _ in range(50):
                result = mobs_spawns.mutate(rows, rng)
                if result:
                    self.assertNotEqual(result[0][2]["id"], 3)

    def test_clean_template_can_land_anywhere(self):
        # Entry 4 (ai_name="SmartAI", home_maps=[0]) is SCRIPTED (per the
        # conservative rule -- any non-empty AIName counts, even SmartAI-only)
        # and must never appear on map 409's spawn.
        rows = [("creature", 102, {"id": 3, "_shuffle_mode": "shuffle_all", "_home_map": 409})]
        rng = random.Random("fixed-seed")
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES):
            for _ in range(50):
                result = mobs_spawns.mutate(rows, rng)
                if result:
                    self.assertNotEqual(result[0][2]["id"], 4)


class TestSpawnGroupInvariantRule(unittest.TestCase):
    def test_passes_when_every_group_still_present(self):
        rule = mobs_spawns.SpawnGroupInvariantRule()
        candidates = [("creature", 100, {"id": 1, "_shuffle_mode": "shuffle_groups", "_home_map": 0})]
        after = [("creature", 100, {"id": 2})]
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS):
            rule.check(candidates, after)  # must not raise (both entries 1/2 share (map=0, band=2, normal))

    def test_raises_when_a_group_disappears_from_its_map(self):
        rule = mobs_spawns.SpawnGroupInvariantRule()
        candidates = [("creature", 102, {"id": 3, "_shuffle_mode": "shuffle_groups", "_home_map": 409})]
        after = [("creature", 102, {"id": 1})]  # map 409's own boss group now has zero bosses
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS):
            with self.assertRaises(InvariantViolation):
                rule.check(candidates, after)

    def test_no_op_for_shuffle_all_mode(self):
        rule = mobs_spawns.SpawnGroupInvariantRule()
        candidates = [("creature", 102, {"id": 3, "_shuffle_mode": "shuffle_all", "_home_map": 409})]
        after = [("creature", 102, {"id": 1})]  # would violate the shuffle_groups claim, but mode is shuffle_all
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", _FAKE_SPAWNS):
            rule.check(candidates, after)  # must not raise

    def test_no_op_for_empty_candidates(self):
        rule = mobs_spawns.SpawnGroupInvariantRule()
        rule.check([], [])  # must not raise

    def test_no_crash_on_orphan_spawn_missing_from_templates(self):
        rule = mobs_spawns.SpawnGroupInvariantRule()
        # guid 999 points at template entry 9999, which does not exist in
        # CREATURE_TEMPLATES -- must be skipped gracefully, never a bare
        # KeyError (which mutation_pipeline.run_category's own
        # `except InvariantViolation` would NOT catch, aborting generation
        # outright instead of retrying).
        candidates = [("creature", 999, {"id": 9999, "_shuffle_mode": "shuffle_groups", "_home_map": 0})]
        after = [("creature", 999, {"id": 9999})]
        with patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_TEMPLATES", _FAKE_TEMPLATES), \
             patch.object(mobs_spawns.mobs_snapshot_content_data, "CREATURE_SPAWNS", {999: {"template_entry": 9999, "map": 0, "shuffle_excluded": False}}):
            rule.check(candidates, after)  # must not raise KeyError (or anything else)
