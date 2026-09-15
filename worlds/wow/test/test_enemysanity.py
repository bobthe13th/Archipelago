import unittest

from .. import enemysanity_content_data
from .bases import WoWTestBase


class TestEnemysanityItemPoolMatchesLocationCount(WoWTestBase):
    """The project's own standing item/location parity invariant
    (test_vendor_stock.py's TestVendorStockItemPoolMatchesLocationCount is
    the established precedent for this exact assertion shape), exercised
    here for the first items_module=None category. Before this task's fix,
    Enemysanity's sampled locations contributed zero items to
    self.multiworld.itempool, so this assertion fails with the un-fixed
    `continue` and passes once create_filler_item_pool pads the deficit.

    Deviation from the plan's literal test code: bases.py's world_setup
    zeroes enemysanity_type_pools/enemysanity_expansion_pools by default for
    EVERY WoWTestBase test (the same test-speed default Task 4 Step 5 adds,
    mirroring containersanity/gathersanity's own established precedent --
    see test_gathersanity.py's TestGathersanityRealGenerationDisenchantOnly
    docstring: "bases.py zeroes BOTH gathersanity pools for every other test
    in the suite ... this class must set both explicitly"). The plan's
    original fixture omitted both options, which -- per that same real,
    already-shipped precedent -- would leave Enemysanity disabled and make
    this test's own "locations exist" assertion vacuously fail. Narrowed to
    type=boss AND expansion=tbc (1,086 real rows, not the full 17,430) to
    keep the run bounded, same discipline test_gathersanity.py's own
    disenchant-only narrowing applied."""

    options = {
        "game_mode": "sprint", "check_density": 100,
        "quest_reward_weight": 0, "vendor_stock_weight": 0,
        "recipe_profession_pools": set(), "trainer_spell_class_pools": set(),
        "containersanity_expansion_pools": set(),
        "gathersanity_expansion_pools": set(), "gathersanity_source_pools": set(),
        "enemysanity_type_pools": {"boss"},
        "enemysanity_expansion_pools": {"tbc"},
    }

    def test_item_pool_matches_location_count_exactly(self) -> None:
        enemysanity_locations = [
            loc for loc in self.multiworld.get_locations(self.player)
            if loc.name in enemysanity_content_data.LOCATIONS
        ]
        self.assertTrue(len(enemysanity_locations) > 0)
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


class TestEnemysanityDisabledContributesNoPadding(WoWTestBase):
    """enemysanity_type_pools/enemysanity_expansion_pools default to the
    full vocabulary (options.py) -- bases.py's test-speed defaults (Task 4
    Step 5) are what actually disable Enemysanity for every OTHER test file
    in this suite. This class intentionally does NOT override those two
    options, so it exercises the "disabled" path here specifically."""

    options = {"game_mode": "sprint"}

    def test_item_pool_still_matches_location_count_when_enemysanity_is_off(self) -> None:
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_locations()))


if __name__ == "__main__":
    unittest.main()
