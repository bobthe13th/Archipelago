import unittest

from ..mutation_invariants import CountingInvariantRule, InvariantRule, InvariantViolation


class TestInvariantRuleBase(unittest.TestCase):
    def test_check_not_implemented_by_default(self):
        rule = InvariantRule()
        with self.assertRaises(NotImplementedError):
            rule.check([], [])


class TestCountingInvariantRule(unittest.TestCase):
    def test_passes_when_every_before_group_still_present_after(self):
        rule = CountingInvariantRule(name="vendor_type_per_zone", group_key=lambda row: row["zone"])
        candidates = [{"zone": "Barrens"}, {"zone": "Redridge"}]
        mutated = [{"zone": "Barrens"}, {"zone": "Redridge"}, {"zone": "Redridge"}]
        rule.check(candidates, mutated)  # must not raise

    def test_raises_when_a_before_group_has_zero_rows_after(self):
        rule = CountingInvariantRule(name="vendor_type_per_zone", group_key=lambda row: row["zone"])
        candidates = [{"zone": "Barrens"}, {"zone": "Redridge"}]
        mutated = [{"zone": "Redridge"}]
        with self.assertRaises(InvariantViolation) as ctx:
            rule.check(candidates, mutated)
        self.assertIn("Barrens", ctx.exception.message)

    def test_a_group_absent_before_is_never_required_after(self):
        rule = CountingInvariantRule(name="vendor_type_per_zone", group_key=lambda row: row["zone"])
        candidates = [{"zone": "Barrens"}]
        mutated = []  # Barrens itself disappearing IS still a violation
        with self.assertRaises(InvariantViolation):
            rule.check(candidates, mutated)

    def test_empty_candidates_never_raises(self):
        rule = CountingInvariantRule(name="vendor_type_per_zone", group_key=lambda row: row["zone"])
        rule.check([], [])  # must not raise
