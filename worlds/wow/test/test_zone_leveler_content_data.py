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

    def test_barrens_instance_keys_include_the_three_originally_curated_instances(self) -> None:
        # M4.11.3.3: instance_keys is now computed from real
        # instance-entrance reachability data (Task 1's own
        # _instance_keys_reachable_from) instead of a hand-typed tuple --
        # independently verified as genuine, correct WorldMapArea.dbc
        # geometry (Task 1's own review): a real 3-zone border-overlap
        # wedge (barrens/thousand_needles/dustwallow_marsh) also puts
        # dire_maul/maraudon/onyxia_s_lair's real entrances within reach
        # from Barrens, growing the set beyond the original 3. Subset
        # check, not exact-equality, since the wider set is real and
        # correct, not a regression to narrow away.
        instance_keys = zl.ZONES["barrens"].instance_keys
        for key in ("wailing_caverns", "razorfen_kraul", "razorfen_downs"):
            self.assertIn(key, instance_keys)

    def test_barrens_instance_keys_are_the_real_verified_wider_set(self) -> None:
        # Pins the real, independently-verified full set (Task 1's own
        # review, 2026-09-02) -- dire_maul/maraudon/onyxia_s_lair's real
        # entrances genuinely resolve into Barrens' own area_tags via the
        # same barrens/thousand_needles/dustwallow_marsh border-overlap
        # wedge, confirmed against live areatrigger/areatrigger_teleport
        # positions, not a defect to narrow away.
        self.assertEqual(
            zl.ZONES["barrens"].instance_keys,
            ("dire_maul", "maraudon", "onyxia_s_lair", "razorfen_downs", "razorfen_kraul", "wailing_caverns"),
        )

    def test_barrens_quest_names_are_all_real_zone_tagged_quest_rewards(self) -> None:
        # M4.11.3.1 (Task 5): repointed from the old scalar
        # TRIGGERS[name]["zone_id"] int comparison onto the unified
        # TAGS[name]["area"] canonical-name mechanism -- a pure reshape,
        # not a behavior change. M4.11.3.3: ZoneLevelerZoneData no longer
        # carries a zone_id field at all (Task 1's flattening) -- reads
        # area_tags directly instead of resolving it via zone_level_data.
        from .. import quest_rewards_content_data
        area_tags = zl.ZONES["barrens"].area_tags
        # Final whole-branch review fix (M4.11.3.1, Finding 4b): guard
        # against a vacuous pass -- without this, a silently-empty
        # quest_reward_location_names would make the loop below iterate
        # zero times and the test would "pass" without actually checking
        # anything.
        self.assertGreater(len(zl.ZONES["barrens"].quest_reward_location_names), 0)
        for name in zl.ZONES["barrens"].quest_reward_location_names:
            self.assertTrue(quest_rewards_content_data.TAGS[name].get("area", frozenset()) & area_tags)


if __name__ == "__main__":
    unittest.main()
