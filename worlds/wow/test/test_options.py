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


if __name__ == "__main__":
    unittest.main()
