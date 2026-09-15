import unittest

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
