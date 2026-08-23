import random
import unittest

from ..density import predict_sample_size, sample_category


class TestDensity(unittest.TestCase):
    def test_zero_density_samples_nothing(self) -> None:
        rows = [f"Mob Kill {i}" for i in range(500)]
        rng = random.Random(1)
        self.assertEqual(sample_category(0, 100, rows, rng), [])

    def test_full_density_full_weight_samples_everything(self) -> None:
        rows = [f"Rare Kill {i}" for i in range(10)]
        rng = random.Random(1)
        result = sample_category(100, 100, rows, rng)
        self.assertEqual(len(result), 10)

    def test_no_cross_category_ceiling_each_category_sampled_independently(self) -> None:
        # Regression guard for the exact thing this task removes: two
        # categories, each fully sampled at 100/100, must EACH come back
        # full -- under the old DensityBudget(hard_ceiling=15) shape this
        # would have clamped the combined total to 15 across both calls.
        rows_a = [f"A{i}" for i in range(10)]
        rows_b = [f"B{i}" for i in range(10)]
        result_a = sample_category(100, 100, rows_a, random.Random(1))
        result_b = sample_category(100, 100, rows_b, random.Random(1))
        self.assertEqual(len(result_a), 10)
        self.assertEqual(len(result_b), 10)

    def test_sampling_is_deterministic_given_the_same_rng_seed(self) -> None:
        rows = [f"Mob Kill {i}" for i in range(500)]
        result_1 = sample_category(40, 50, rows, random.Random(42))
        result_2 = sample_category(40, 50, rows, random.Random(42))
        self.assertEqual(result_1, result_2)

    def test_predict_sample_size_matches_sample_category_count(self) -> None:
        rows = [f"Row {i}" for i in range(37750)]
        predicted = predict_sample_size(100, 10, len(rows))
        sampled = sample_category(100, 10, rows, random.Random(7))
        self.assertEqual(len(sampled), predicted)

    def test_predict_sample_size_zero_when_any_factor_zero(self) -> None:
        self.assertEqual(predict_sample_size(0, 100, 1000), 0)
        self.assertEqual(predict_sample_size(100, 0, 1000), 0)
        self.assertEqual(predict_sample_size(100, 100, 0), 0)

    def test_predict_sample_size_rounds_up(self) -> None:
        # ceil(3 rows * 0.5 density * 1.0 weight) == 2, not 1
        self.assertEqual(predict_sample_size(50, 100, 3), 2)
