import random
import unittest
from types import SimpleNamespace

from Options import OptionError

from .. import mutation_invariants
from .. import mutation_pipeline
from ..mutation_invariants import InvariantRule, InvariantViolation
from ..world_seed import derive_world_seed


class _AlwaysPassRule(InvariantRule):
    name = "always_pass"

    def check(self, candidate_rows, mutation_rows):
        return None


class _AlwaysFailRule(InvariantRule):
    name = "always_fail"

    def check(self, candidate_rows, mutation_rows):
        raise InvariantViolation("synthetic failure")


class _FailFirstNAttemptsRule(InvariantRule):
    name = "fail_first_n"

    def __init__(self, fail_count):
        self.fail_count = fail_count
        self.calls = 0

    def check(self, candidate_rows, mutation_rows):
        self.calls += 1
        if self.calls <= self.fail_count:
            raise InvariantViolation(f"synthetic failure #{self.calls}")


def _identity_mutate(rows, rng):
    return list(rows)


class TestRunCategory(unittest.TestCase):
    def setUp(self):
        self.world = SimpleNamespace(player=1, multiworld=SimpleNamespace(get_locations=lambda player: []))
        self.world_seed = derive_world_seed("12345", "Alice")

    def test_passing_category_returns_mutation_rows_on_first_attempt(self):
        category = mutation_pipeline.MutationCategory(
            key="test_category",
            candidate_rows=lambda world: [("creature_template", 1, {"level": 10})],
            mutate=_identity_mutate,
            invariant_rules=[_AlwaysPassRule()],
        )
        result = mutation_pipeline.run_category(category, self.world, self.world_seed, claimed=set())
        self.assertEqual(result, [("creature_template", 1, {"level": 10})])

    def test_claimed_rows_are_excluded_before_mutate_runs(self):
        seen_candidates = []

        def spy_mutate(rows, rng):
            seen_candidates.append(list(rows))
            return list(rows)

        category = mutation_pipeline.MutationCategory(
            key="test_category",
            candidate_rows=lambda world: [
                ("creature_template", 1, {}),
                ("creature_template", 2, {}),
            ],
            mutate=spy_mutate,
            invariant_rules=[],
        )
        mutation_pipeline.run_category(
            category, self.world, self.world_seed, claimed={("creature_template", 1)}
        )
        self.assertEqual(seen_candidates, [[("creature_template", 2, {})]])

    def test_retries_up_to_max_attempts_then_raises_option_error(self):
        rule = _AlwaysFailRule()
        category = mutation_pipeline.MutationCategory(
            key="test_category",
            candidate_rows=lambda world: [("creature_template", 1, {})],
            mutate=_identity_mutate,
            invariant_rules=[rule],
        )
        with self.assertRaises(OptionError) as ctx:
            mutation_pipeline.run_category(category, self.world, self.world_seed, claimed=set())
        self.assertIn("test_category", str(ctx.exception))
        self.assertIn(str(mutation_pipeline.MAX_ATTEMPTS), str(ctx.exception))

    def test_succeeds_after_retrying_a_transient_failure(self):
        rule = _FailFirstNAttemptsRule(fail_count=3)
        category = mutation_pipeline.MutationCategory(
            key="test_category",
            candidate_rows=lambda world: [("creature_template", 1, {})],
            mutate=_identity_mutate,
            invariant_rules=[rule],
        )
        result = mutation_pipeline.run_category(category, self.world, self.world_seed, claimed=set())
        self.assertEqual(result, [("creature_template", 1, {})])
        self.assertEqual(rule.calls, 4)  # 3 failures + 1 success

    def test_unmodified_candidates_count_toward_invariant_after_state(self):
        # mutate() returns ONLY the row it actually changed. An untouched
        # candidate (row 2 here) must still count as "present after" for
        # CountingInvariantRule via the driver's own unmodified-candidate
        # carry-forward -- otherwise a category that only ever mutates a
        # SUBSET of its candidates would spuriously fail its own
        # invariant on every attempt (see MutationCategory's docstring).
        def mutate_only_row_1(rows, rng):
            return [("creature_template", 1, {"level": 99})]

        rule = mutation_invariants.CountingInvariantRule(
            name="zone_has_creature", group_key=lambda row: row[1]
        )
        category = mutation_pipeline.MutationCategory(
            key="test_category",
            candidate_rows=lambda world: [
                ("creature_template", 1, {"level": 10}),
                ("creature_template", 2, {"level": 20}),
            ],
            mutate=mutate_only_row_1,
            invariant_rules=[rule],
        )
        result = mutation_pipeline.run_category(category, self.world, self.world_seed, claimed=set())
        # Only row 1 was actually mutated -- row 2 is untouched and must
        # NOT appear in the returned diff, but must also not have caused
        # a spurious invariant failure (it counted toward the "after"
        # state internally, inside run_category, not in this assertion).
        self.assertEqual(result, [("creature_template", 1, {"level": 99})])

    def test_sub_seed_derivation_is_deterministic_across_runs(self):
        seen_rngs = []

        def capture_rng_mutate(rows, rng):
            seen_rngs.append(rng.random())
            return list(rows)

        category = mutation_pipeline.MutationCategory(
            key="test_category",
            candidate_rows=lambda world: [("creature_template", 1, {})],
            mutate=capture_rng_mutate,
            invariant_rules=[],
        )
        mutation_pipeline.run_category(category, self.world, self.world_seed, claimed=set())
        mutation_pipeline.run_category(category, self.world, self.world_seed, claimed=set())
        self.assertEqual(seen_rngs[0], seen_rngs[1])


class TestRunAllCategories(unittest.TestCase):
    def test_empty_registry_returns_empty_dict(self):
        original = mutation_pipeline._MUTATION_CATEGORIES
        mutation_pipeline._MUTATION_CATEGORIES = []
        try:
            world = SimpleNamespace(player=1, multiworld=SimpleNamespace(get_locations=lambda player: []))
            result = mutation_pipeline.run_all_categories(world, derive_world_seed("1", "Alice"))
            self.assertEqual(result, {})
        finally:
            mutation_pipeline._MUTATION_CATEGORIES = original

    def test_register_category_adds_to_registry(self):
        original = mutation_pipeline._MUTATION_CATEGORIES
        mutation_pipeline._MUTATION_CATEGORIES = []
        try:
            category = mutation_pipeline.MutationCategory(
                key="test_category", candidate_rows=lambda world: [], mutate=_identity_mutate, invariant_rules=[]
            )
            mutation_pipeline.register_category(category)
            self.assertIn(category, mutation_pipeline._MUTATION_CATEGORIES)
        finally:
            mutation_pipeline._MUTATION_CATEGORIES = original
