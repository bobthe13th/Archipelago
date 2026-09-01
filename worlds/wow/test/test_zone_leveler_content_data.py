import unittest

from .. import zone_leveler_content_data as zl


class TestZoneLevelerContentData(unittest.TestCase):
    def test_barrens_zone_is_registered(self) -> None:
        self.assertIn("barrens", zl.ZONES)

    def test_barrens_level_range_matches_zone_level_data(self) -> None:
        barrens = zl.ZONES["barrens"]
        self.assertEqual((barrens.min_level, barrens.max_level), (10, 30))

    def test_barrens_has_three_curated_instances(self) -> None:
        self.assertEqual(zl.ZONES["barrens"].instance_keys, ("wailing_caverns", "razorfen_kraul", "razorfen_downs"))

    def test_barrens_quest_names_are_all_real_zone_tagged_quest_rewards(self) -> None:
        from .. import quest_rewards_content_data
        for name in zl.ZONES["barrens"].quest_reward_location_names:
            self.assertEqual(quest_rewards_content_data.TRIGGERS[name]["zone_id"], zl.ZONES["barrens"].zone_id)


if __name__ == "__main__":
    unittest.main()
