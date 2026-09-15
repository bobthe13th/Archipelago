import unittest

from .. import core_loop_content_data, instance_entrance_data
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


class TestInstanceKeyNamespacesAgree(unittest.TestCase):
    """Final whole-branch review fix (Important #1, M4.11.3 milestone final
    review): regression coverage for the silent instance-key namespace
    mismatch between core_loop_content_data.INSTANCE_CLEAR_LOCATIONS
    (hand-curated) and instance_entrance_data.INSTANCE_ENTRANCE_AREA_TAGS
    (real Map.dbc-derived). Real map id 580's own canonical DBC slug is
    "sunwell" (parse_map_names(), azerothcore-wotlk/modules/archipelago_wow/
    tools/db_extract.py); core_loop_content_data used to hand-curate the key
    "sunwell_plateau" instead -- these never matched, so
    zone_leveler_content_data.curated_instance_keys silently dropped Sunwell
    Plateau from any zone whose area_tags would reach it. Confirmed as the
    one real outlier by checking the other 3 instance keys this same
    milestone curated (wailing_caverns/razorfen_kraul/razorfen_downs), which
    already match their own real Map.dbc slugs exactly with no suffix
    embellishment -- see the other assertions below."""

    def test_sunwell_key_is_present_in_both_namespaces(self) -> None:
        self.assertIn("sunwell", core_loop_content_data.INSTANCE_CLEAR_LOCATIONS)
        self.assertIn("sunwell", instance_entrance_data.INSTANCE_ENTRANCE_AREA_TAGS)

    def test_sunwell_plateau_is_no_longer_a_key_anywhere(self) -> None:
        # Pins the actual rename, not just the presence of the corrected key
        # -- guards against a future edit re-adding "sunwell_plateau"
        # alongside "sunwell" (which would satisfy the test above but still
        # be wrong: two keys for the same real instance).
        self.assertNotIn("sunwell_plateau", core_loop_content_data.INSTANCE_CLEAR_LOCATIONS)

    def test_every_curated_instance_key_matches_its_own_real_dbc_slug_convention(self) -> None:
        # The 3 instances known-correct before this fix (M4.11.1's own
        # BarrensBeater curation) already follow "real Map.dbc slug, no
        # suffix embellishment" -- confirms this IS the convention, and that
        # "sunwell_plateau" (fixed above) was the one outlier, not a second
        # legitimate naming scheme.
        for key in ("wailing_caverns", "razorfen_kraul", "razorfen_downs"):
            self.assertIn(key, core_loop_content_data.INSTANCE_CLEAR_LOCATIONS)
            self.assertIn(key, instance_entrance_data.INSTANCE_ENTRANCE_AREA_TAGS)

    def test_every_instance_clear_locations_key_exists_in_entrance_area_tags(self) -> None:
        # The real, general form of the two tests above -- every key, not
        # just the ones this fix touched.
        missing = sorted(
            key for key in core_loop_content_data.INSTANCE_CLEAR_LOCATIONS
            if key not in instance_entrance_data.INSTANCE_ENTRANCE_AREA_TAGS
        )
        self.assertEqual(missing, [])

    def test_validation_guard_raises_loudly_on_a_deliberately_mismatched_key(self) -> None:
        # Proves the module-load-time guard (zone_leveler_content_data.
        # _validate_instance_key_namespaces) actually fires, using a
        # synthetic pair passed via its optional params -- not the real,
        # already-consistent module globals (which the test above already
        # confirms have zero mismatches, so calling the guard with no args
        # here would prove nothing about its *raising* behavior).
        with self.assertRaises(AssertionError) as ctx:
            zl._validate_instance_key_namespaces(
                instance_clear_locations={"totally_fake_instance": 999999},
                instance_entrance_area_tags={},
            )
        self.assertIn("totally_fake_instance", str(ctx.exception))

    def test_validation_guard_is_silent_when_namespaces_agree(self) -> None:
        zl._validate_instance_key_namespaces(
            instance_clear_locations={"barrens_dummy": 1},
            instance_entrance_area_tags={"barrens_dummy": frozenset({"barrens"})},
        )


if __name__ == "__main__":
    unittest.main()
