import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from .. import environment_creature_flavor


class TestByte0Helpers(unittest.TestCase):
    def test_extract_byte0_masks_low_byte_only(self):
        self.assertEqual(environment_creature_flavor._extract_byte0(0x12345678), 0x78)

    def test_extract_byte0_zero_value(self):
        self.assertEqual(environment_creature_flavor._extract_byte0(0), 0)

    def test_replace_byte0_preserves_upper_three_bytes(self):
        result = environment_creature_flavor._replace_byte0(0x12345678, 0xAB)
        self.assertEqual(result, 0x123456AB)

    def test_replace_byte0_on_zero_value(self):
        result = environment_creature_flavor._replace_byte0(0, 0x05)
        self.assertEqual(result, 0x05)

    def test_round_trip_preserves_upper_bytes(self):
        original = 0xDEADBE01
        byte0 = environment_creature_flavor._extract_byte0(original)
        reconstructed = environment_creature_flavor._replace_byte0(original, byte0)
        self.assertEqual(reconstructed, original)


class TestAuraWhitelist(unittest.TestCase):
    def test_whitelist_is_a_tuple_of_ints(self):
        self.assertIsInstance(environment_creature_flavor._COSMETIC_AURA_WHITELIST, tuple)
        for spell_id in environment_creature_flavor._COSMETIC_AURA_WHITELIST:
            self.assertIsInstance(spell_id, int)


def _fake_world(equipment=False, posture=False, mount=False, aura=False):
    return SimpleNamespace(options=SimpleNamespace(
        environment_randomizer_equipment_enabled=SimpleNamespace(value=equipment),
        environment_randomizer_posture_enabled=SimpleNamespace(value=posture),
        environment_randomizer_mount_enabled=SimpleNamespace(value=mount),
        environment_randomizer_aura_enabled=SimpleNamespace(value=aura),
    ))


_FAKE_EQUIPMENT = {
    1: {"id1": 100, "equipment_id": 1},
    2: {"id1": 100, "equipment_id": 2},
    3: {"id1": 200, "equipment_id": 0},
}
_FAKE_ADDONS = {
    100: {"mount": 0, "bytes1": 0x00000001, "bytes2": 0x00000000, "emote": 0, "auras": ""},
    200: {"mount": 1234, "bytes1": 0x00000002, "bytes2": 0x00000001, "emote": 5, "auras": ""},
}


def _patched_content():
    return patch.object(
        environment_creature_flavor, "creature_flavor_content_data",
        SimpleNamespace(CREATURE_EQUIPMENT=_FAKE_EQUIPMENT, CREATURE_ADDONS=_FAKE_ADDONS),
    )


class TestCandidateRows(unittest.TestCase):
    def test_all_disabled_returns_no_candidates(self):
        world = _fake_world()
        with _patched_content():
            self.assertEqual(environment_creature_flavor.candidate_rows(world), [])

    def test_equipment_only_returns_creature_rows(self):
        world = _fake_world(equipment=True)
        with _patched_content():
            rows = environment_creature_flavor.candidate_rows(world)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row[0] == "creature" for row in rows))

    def test_posture_and_mount_together_produce_one_merged_row_per_entry(self):
        world = _fake_world(posture=True, mount=True)
        with _patched_content():
            rows = environment_creature_flavor.candidate_rows(world)
        # Exactly one row per creature_template_addon candidate, not two.
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[0] == "creature_template_addon" for row in rows))
        _table, _entry, payload = rows[0]
        self.assertIn("bytes1", payload)
        self.assertIn("bytes2", payload)
        self.assertIn("mount", payload)

    def test_aura_disabled_never_appears_in_payload(self):
        world = _fake_world(posture=True)
        with _patched_content():
            rows = environment_creature_flavor.candidate_rows(world)
        for _table, _entry, payload in rows:
            self.assertNotIn("auras", payload)


class TestMutateEquipment(unittest.TestCase):
    def test_shuffles_only_within_same_template_group(self):
        rows = [
            ("creature", 1, {"id1": 100, "equipment_id": 1, "_field": "equipment"}),
            ("creature", 2, {"id1": 100, "equipment_id": 2, "_field": "equipment"}),
            ("creature", 3, {"id1": 200, "equipment_id": 0, "_field": "equipment"}),
        ]
        rng = random.Random("fixed-seed")
        result = environment_creature_flavor.mutate(rows, rng)
        # guid 3 is the only member of its group (id1=200) -- must never
        # receive an equipment_id from the id1=100 group.
        result_by_guid = {guid: payload for _t, guid, payload in result}
        if 3 in result_by_guid:
            self.assertEqual(result_by_guid[3]["equipment_id"], 0)


class TestMutatePostureByte0Only(unittest.TestCase):
    def test_only_byte0_changes_upper_bytes_preserved(self):
        rows = [
            ("creature_template_addon", 100, {"bytes1": 0xAABBCC01, "_posture_mode": "shuffle"}),
            ("creature_template_addon", 200, {"bytes1": 0x11223302, "_posture_mode": "shuffle"}),
        ]
        rng = random.Random("fixed-seed")
        result = environment_creature_flavor.mutate(rows, rng)
        result_by_entry = {entry: payload for _t, entry, payload in result}
        if 100 in result_by_entry and "bytes1" in result_by_entry[100]:
            self.assertEqual(result_by_entry[100]["bytes1"] & 0xFFFFFF00, 0xAABBCC00)
        if 200 in result_by_entry and "bytes1" in result_by_entry[200]:
            self.assertEqual(result_by_entry[200]["bytes1"] & 0xFFFFFF00, 0x11223300)


class TestMutateAuraWhitelist(unittest.TestCase):
    def test_empty_whitelist_never_assigns_aura(self):
        rows = [("creature_template_addon", 100, {"auras": "", "_aura_mode": "shuffle"})]
        rng = random.Random("fixed-seed")
        with patch.object(environment_creature_flavor, "_COSMETIC_AURA_WHITELIST", ()):
            result = environment_creature_flavor.mutate(rows, rng)
        for _t, _e, payload in result:
            self.assertNotIn("auras", payload)

    def test_populated_whitelist_only_assigns_whitelisted_ids(self):
        rows = [("creature_template_addon", 100, {"auras": "", "_aura_mode": "shuffle"})]
        rng = random.Random("fixed-seed")
        with patch.object(environment_creature_flavor, "_COSMETIC_AURA_WHITELIST", (111, 222, 333)):
            for _ in range(20):
                result = environment_creature_flavor.mutate(rows, rng)
                for _t, _e, payload in result:
                    if "auras" in payload:
                        assigned_ids = {int(x) for x in payload["auras"].split(",") if x}
                        self.assertTrue(assigned_ids.issubset({111, 222, 333}))


class TestMutateGeneral(unittest.TestCase):
    def test_no_control_keys_leak_into_returned_payload(self):
        rows = [("creature_template_addon", 100, {
            "mount": 0, "bytes1": 1, "_posture_mode": "shuffle", "_mount_mode": "shuffle",
        })]
        rng = random.Random("fixed-seed")
        result = environment_creature_flavor.mutate(rows, rng)
        for _t, _e, payload in result:
            for key in payload:
                self.assertFalse(key.startswith("_"))

    def test_empty_rows_returns_empty(self):
        rng = random.Random("fixed-seed")
        self.assertEqual(environment_creature_flavor.mutate([], rng), [])
