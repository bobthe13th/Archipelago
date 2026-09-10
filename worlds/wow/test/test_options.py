# Archipelago/worlds/wow/test/test_options.py
import unittest


class TestContainersanityExpansionPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import ContainersanityExpansionPools
        self.assertEqual(ContainersanityExpansionPools.default, ContainersanityExpansionPools.valid_keys)

    def test_valid_keys_match_the_project_s_three_expansion_tiers(self) -> None:
        from ..options import ContainersanityExpansionPools
        self.assertEqual(set(ContainersanityExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})


class TestLootSlotCheckRepeatBehavior(unittest.TestCase):
    def test_default_is_suppress_entirely(self) -> None:
        from ..options import LootSlotCheckRepeatBehavior
        self.assertEqual(LootSlotCheckRepeatBehavior.default, LootSlotCheckRepeatBehavior.option_suppress_entirely)

    def test_all_four_modes_present(self) -> None:
        from ..options import LootSlotCheckRepeatBehavior
        for mode in ("suppress_entirely", "vanilla_item", "gold_conversion", "filler_consumable"):
            self.assertTrue(hasattr(LootSlotCheckRepeatBehavior, f"option_{mode}"))


class TestGathersanityExpansionPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import GathersanityExpansionPools
        self.assertEqual(GathersanityExpansionPools.default, GathersanityExpansionPools.valid_keys)

    def test_valid_keys_match_the_project_s_three_expansion_tiers(self) -> None:
        from ..options import GathersanityExpansionPools
        self.assertEqual(set(GathersanityExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})


class TestGathersanitySourcePools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import GathersanitySourcePools
        self.assertEqual(GathersanitySourcePools.default, GathersanitySourcePools.valid_keys)

    def test_valid_keys_match_the_six_real_sources(self) -> None:
        from ..options import GathersanitySourcePools
        self.assertEqual(
            set(GathersanitySourcePools.valid_keys),
            {"gathering_node", "skinning", "mob_herbalism", "mob_mining", "mob_engineering", "disenchant"},
        )


class TestEnemysanityTypePools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import EnemysanityTypePools
        self.assertEqual(EnemysanityTypePools.default, EnemysanityTypePools.valid_keys)

    def test_valid_keys_are_boss_and_regular(self) -> None:
        from ..options import EnemysanityTypePools
        self.assertEqual(set(EnemysanityTypePools.valid_keys), {"boss", "regular"})


class TestEnemysanityExpansionPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import EnemysanityExpansionPools
        self.assertEqual(EnemysanityExpansionPools.default, EnemysanityExpansionPools.valid_keys)

    def test_valid_keys_match_the_project_s_three_expansion_tiers(self) -> None:
        from ..options import EnemysanityExpansionPools
        self.assertEqual(set(EnemysanityExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})


class TestCraftsanityProfessionPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import CraftsanityProfessionPools
        self.assertEqual(CraftsanityProfessionPools.default, CraftsanityProfessionPools.valid_keys)

    def test_valid_keys_match_the_project_s_profession_vocabulary(self) -> None:
        from ..options import CraftsanityProfessionPools, RecipeProfessionPools
        # Same profession vocabulary as recipes/trainer_spells -- Craftsanity's
        # produced items come from the exact same spell universe.
        self.assertEqual(set(CraftsanityProfessionPools.valid_keys), set(RecipeProfessionPools.valid_keys))


class TestCraftsanityClassPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import CraftsanityClassPools
        self.assertEqual(CraftsanityClassPools.default, CraftsanityClassPools.valid_keys)

    def test_valid_keys_are_mage_and_warlock(self) -> None:
        from ..options import CraftsanityClassPools
        self.assertEqual(set(CraftsanityClassPools.valid_keys), {"mage", "warlock"})


class TestCraftsanityExpansionPools(unittest.TestCase):
    def test_default_selects_full_vocabulary(self) -> None:
        from ..options import CraftsanityExpansionPools
        self.assertEqual(CraftsanityExpansionPools.default, CraftsanityExpansionPools.valid_keys)

    def test_valid_keys_match_the_project_s_three_expansion_tiers(self) -> None:
        from ..options import CraftsanityExpansionPools
        self.assertEqual(set(CraftsanityExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})


class TestItemsanityPools(unittest.TestCase):
    def test_class_pools_default_selects_full_vocabulary(self) -> None:
        from ..options import ItemsanityClassPools
        self.assertEqual(ItemsanityClassPools.default, ItemsanityClassPools.valid_keys)

    def test_class_pools_valid_keys_match_the_real_item_class_enum(self) -> None:
        from ..options import ItemsanityClassPools
        self.assertEqual(set(ItemsanityClassPools.valid_keys), {
            "consumable", "container", "weapon", "gem", "armor", "reagent",
            "projectile", "trade_goods", "generic", "recipe", "money",
            "quiver", "quest", "key", "permanent", "misc", "glyph",
        })

    def test_quality_pools_default_selects_full_vocabulary(self) -> None:
        from ..options import ItemsanityQualityPools
        self.assertEqual(ItemsanityQualityPools.default, ItemsanityQualityPools.valid_keys)

    def test_quality_pools_valid_keys_match_the_real_item_quality_enum(self) -> None:
        from ..options import ItemsanityQualityPools
        self.assertEqual(set(ItemsanityQualityPools.valid_keys), {
            "poor", "normal", "uncommon", "rare", "epic", "legendary",
            "artifact", "heirloom",
        })

    def test_expansion_pools_default_selects_full_vocabulary(self) -> None:
        from ..options import ItemsanityExpansionPools
        self.assertEqual(ItemsanityExpansionPools.default, ItemsanityExpansionPools.valid_keys)

    def test_expansion_pools_valid_keys_match_the_project_s_three_expansion_tiers(self) -> None:
        from ..options import ItemsanityExpansionPools
        self.assertEqual(set(ItemsanityExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})


class TestItemsanityDebugItemInclusion(unittest.TestCase):
    def test_default_is_exclude_all(self) -> None:
        from ..options import ItemsanityDebugItemInclusion
        self.assertEqual(ItemsanityDebugItemInclusion.default, ItemsanityDebugItemInclusion.option_exclude_all)

    def test_three_real_values(self) -> None:
        from ..options import ItemsanityDebugItemInclusion
        self.assertEqual(ItemsanityDebugItemInclusion.option_exclude_all, 0)
        self.assertEqual(ItemsanityDebugItemInclusion.option_include_unobtainable, 1)
        self.assertEqual(ItemsanityDebugItemInclusion.option_include_all, 2)


class TestHolidaysanityStacking(unittest.TestCase):
    def test_default_is_off(self) -> None:
        from ..options import HolidaysanityStacking
        self.assertEqual(HolidaysanityStacking.default, 0)


class TestGameModeZoneLeveler(unittest.TestCase):
    def test_zone_leveler_is_a_real_game_mode_value(self) -> None:
        from ..options import GameMode
        self.assertEqual(GameMode.option_zone_leveler, 13)


class TestContainersanityChestsPerZone(unittest.TestCase):
    def test_containersanity_chests_per_zone_default_and_range(self) -> None:
        from ..options import ContainersanityChestsPerZone
        opt = ContainersanityChestsPerZone.from_any(ContainersanityChestsPerZone.default)
        self.assertEqual(opt.value, 5)
        self.assertEqual(ContainersanityChestsPerZone.range_start, 0)
        self.assertEqual(ContainersanityChestsPerZone.range_end, 15)


class TestVendorStockUtilityPools(unittest.TestCase):
    def test_default_is_empty(self) -> None:
        from ..options import VendorStockUtilityPools
        self.assertEqual(VendorStockUtilityPools.default, frozenset())

    def test_valid_keys_match_the_five_real_utility_categories(self) -> None:
        from ..options import VendorStockUtilityPools
        self.assertEqual(set(VendorStockUtilityPools.valid_keys), {
            "innkeeper", "general_goods", "food", "poison", "reagent",
        })


class TestMobRandomizerOptions(unittest.TestCase):
    def test_level_mode_defaults_to_vanilla(self):
        from ..options import MobRandomizerLevelMode
        self.assertEqual(MobRandomizerLevelMode.default, MobRandomizerLevelMode.option_vanilla)

    def test_level_mode_has_three_values(self):
        from ..options import MobRandomizerLevelMode
        self.assertEqual(
            {"vanilla", "zone_scaled", "individual_spawn"},
            set(MobRandomizerLevelMode.name_lookup.values()),
        )

    def test_spawn_mode_defaults_to_vanilla(self):
        from ..options import MobRandomizerSpawnMode
        self.assertEqual(MobRandomizerSpawnMode.default, MobRandomizerSpawnMode.option_vanilla)

    def test_spawn_mode_has_three_values(self):
        from ..options import MobRandomizerSpawnMode
        self.assertEqual(
            {"vanilla", "shuffle_groups", "shuffle_all"},
            set(MobRandomizerSpawnMode.name_lookup.values()),
        )

    def test_both_registered_on_wow_options(self):
        from ..options import WoWOptions
        self.assertIn("mob_randomizer_level_mode", WoWOptions.type_hints)
        self.assertIn("mob_randomizer_spawn_mode", WoWOptions.type_hints)


if __name__ == "__main__":
    unittest.main()
