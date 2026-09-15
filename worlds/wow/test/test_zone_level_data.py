import unittest

from .. import zone_level_data


class TestZoneLevelData(unittest.TestCase):
    def test_barrens_is_a_10_to_30_zone(self) -> None:
        self.assertEqual(zone_level_data.ZONE_ID_TO_LEVEL_RANGE[zone_level_data.ZONE_ID_BARRENS], (10, 30))

    def test_level_range_for_zone_returns_none_for_unmapped_zone(self) -> None:
        self.assertIsNone(zone_level_data.level_range_for_zone(999999))

    def test_zones_in_level_range_includes_overlapping_zones_only(self) -> None:
        zones = zone_level_data.zones_in_level_range(10, 30)
        self.assertIn(zone_level_data.ZONE_ID_BARRENS, zones)
        # A zone whose band is entirely above 30 (e.g. Molten Core's own zone,
        # a level-60 raid) must not overlap a 10-30 query.
        self.assertNotIn(zone_level_data.ZONE_ID_MOLTEN_CORE, zones)


if __name__ == "__main__":
    unittest.main()
