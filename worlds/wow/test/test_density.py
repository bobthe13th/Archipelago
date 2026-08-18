import random
import unittest

from ..density import DensityBudget, sample_category


class TestDensityBudget(unittest.TestCase):
    def test_zero_density_samples_nothing(self) -> None:
        budget = DensityBudget(check_density=0, hard_ceiling=1000)
        rows = [{"name": f"Mob Kill {i}"} for i in range(500)]
        rng = random.Random(1)
        result = sample_category(budget, category_weight=50, all_rows=rows, rng=rng)
        self.assertEqual(result, [])

    def test_full_density_full_weight_samples_everything_under_ceiling(self) -> None:
        budget = DensityBudget(check_density=100, hard_ceiling=1000)
        rows = [{"name": f"Rare Kill {i}"} for i in range(10)]
        rng = random.Random(1)
        result = sample_category(budget, category_weight=100, all_rows=rows, rng=rng)
        self.assertEqual(len(result), 10)

    def test_hard_ceiling_caps_total_across_multiple_categories(self) -> None:
        budget = DensityBudget(check_density=100, hard_ceiling=15)
        rows_a = [{"name": f"A{i}"} for i in range(10)]
        rows_b = [{"name": f"B{i}"} for i in range(10)]
        rng = random.Random(1)
        result_a = sample_category(budget, category_weight=100, all_rows=rows_a, rng=rng)
        result_b = sample_category(budget, category_weight=100, all_rows=rows_b, rng=rng)
        self.assertEqual(len(result_a) + len(result_b), 15)

    def test_sampling_is_deterministic_given_the_same_rng_seed(self) -> None:
        rows = [{"name": f"Mob Kill {i}"} for i in range(500)]
        budget_1 = DensityBudget(check_density=40, hard_ceiling=1000)
        budget_2 = DensityBudget(check_density=40, hard_ceiling=1000)
        result_1 = sample_category(budget_1, category_weight=50, all_rows=rows, rng=random.Random(42))
        result_2 = sample_category(budget_2, category_weight=50, all_rows=rows, rng=random.Random(42))
        self.assertEqual([r["name"] for r in result_1], [r["name"] for r in result_2])


if __name__ == "__main__":
    unittest.main()
