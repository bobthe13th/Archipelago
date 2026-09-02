import unittest

from .. import zone_leveler_content_data as zl
from .. import zone_level_data


class TestZoneLevelerContentData(unittest.TestCase):
    def test_barrens_zone_is_registered(self) -> None:
        self.assertIn("barrens", zl.ZONES)

    def test_barrens_level_range_matches_zone_level_data(self) -> None:
        # Real cross-check (final whole-branch review M5 fix, 2026-09-01):
        # this used to just hardcode (10, 30) and never actually imported
        # zone_level_data at all, despite its name -- these are two
        # independently maintained sources of truth (zone_leveler_content_data
        # is Task 12's own hand-curated data; zone_level_data is Task 13's
        # DBC-verified scaffolding, not currently consumed by any production
        # code -- see zone_level_data.py's own module docstring), so a real
        # test asserting they agree is worth having even though neither
        # reads the other at runtime.
        barrens = zl.ZONES["barrens"]
        self.assertEqual(
            (barrens.min_level, barrens.max_level),
            zone_level_data.ZONE_ID_TO_LEVEL_RANGE[zone_level_data.ZONE_ID_BARRENS],
        )
        self.assertEqual((barrens.min_level, barrens.max_level), (10, 30))

    def test_barrens_has_three_curated_instances(self) -> None:
        self.assertEqual(zl.ZONES["barrens"].instance_keys, ("wailing_caverns", "razorfen_kraul", "razorfen_downs"))

    def test_barrens_quest_names_are_all_real_zone_tagged_quest_rewards(self) -> None:
        # M4.11.3.1 (Task 5): repointed from the old scalar
        # TRIGGERS[name]["zone_id"] int comparison onto the unified
        # TAGS[name]["area"] canonical-name mechanism -- a pure reshape,
        # not a behavior change.
        from .. import quest_rewards_content_data
        area_name = zone_level_data.area_name_for_zone_id(zl.ZONES["barrens"].zone_id)
        # Final whole-branch review fix (M4.11.3.1, Finding 4b): guard
        # against a vacuous pass -- without this, a silently-empty
        # quest_reward_location_names (e.g. from Finding 4's now-fixed
        # area_name_for_zone_id silently returning None) would make the
        # loop below iterate zero times and the test would "pass" without
        # actually checking anything.
        self.assertGreater(len(zl.ZONES["barrens"].quest_reward_location_names), 0)
        for name in zl.ZONES["barrens"].quest_reward_location_names:
            self.assertIn(area_name, quest_rewards_content_data.TAGS[name].get("area", frozenset()))


if __name__ == "__main__":
    unittest.main()
