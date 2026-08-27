# Archipelago/worlds/wow/test/test_recipe_trainer_spell_options.py
import dataclasses
import unittest

from ..options import (
    RecipeProfessionPools, RecipeExpansionPools,
    TrainerSpellClassPools, TrainerSpellExpansionPools, WoWOptions,
)


class TestRecipeAndTrainerSpellTagOptions(unittest.TestCase):
    def test_recipe_profession_pools_default_selects_every_value(self) -> None:
        self.assertEqual(set(RecipeProfessionPools.default), set(RecipeProfessionPools.valid_keys))
        self.assertIn("cooking", RecipeProfessionPools.valid_keys)
        self.assertIn("other", RecipeProfessionPools.valid_keys)

    def test_recipe_expansion_pools_default_selects_every_value(self) -> None:
        self.assertEqual(set(RecipeExpansionPools.valid_keys), {"vanilla", "tbc", "wotlk"})
        self.assertEqual(set(RecipeExpansionPools.default), set(RecipeExpansionPools.valid_keys))

    def test_trainer_spell_class_pools_covers_every_real_wotlk_class(self) -> None:
        self.assertEqual(
            set(TrainerSpellClassPools.valid_keys),
            {"warrior", "paladin", "hunter", "rogue", "priest",
             "death_knight", "shaman", "mage", "warlock", "druid"},
        )
        self.assertEqual(set(TrainerSpellClassPools.default), set(TrainerSpellClassPools.valid_keys))

    def test_trainer_spell_expansion_pools_default_selects_every_value(self) -> None:
        self.assertEqual(set(TrainerSpellExpansionPools.default), set(TrainerSpellExpansionPools.valid_keys))

    def test_wowoptions_declares_all_four_new_fields(self) -> None:
        field_names = {f.name for f in dataclasses.fields(WoWOptions)}
        self.assertIn("recipe_profession_pools", field_names)
        self.assertIn("recipe_expansion_pools", field_names)
        self.assertIn("trainer_spell_class_pools", field_names)
        self.assertIn("trainer_spell_expansion_pools", field_names)


if __name__ == "__main__":
    unittest.main()
