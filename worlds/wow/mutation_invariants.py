"""M5.0 Sec5: pluggable, structural/counting invariant-rule registry. Each
Pipeline B category (M5.1-M5.6) supplies its own list of InvariantRule
instances to mutation_pipeline.py's driver; this module defines the shared
interface plus one generic, reusable implementation (CountingInvariantRule)
covering Sec5's own worked examples ("every zone that had >=1 vendor of
type X before mutation still has >=1 after", "no level bracket loses 100%
of its reputation vendors") without each category re-implementing its own
counting loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable, Sequence


class InvariantViolation(Exception):
    """Raised by InvariantRule.check when a mutation result fails
    validation. Caught by mutation_pipeline.py's retry loop -- never
    escapes to the apworld's own pre_output/generate_output caller
    directly (that only happens after every retry attempt is exhausted,
    as an OptionError -- see mutation_pipeline.py)."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvariantRule:
    """Base interface. check(candidate_rows, mutation_rows) raises
    InvariantViolation on failure, returns None on success.
    candidate_rows is this category's own AP-claimed-row-excluded
    candidate pool (the "before" state); mutation_rows is what this
    attempt's mutate() produced (the "after" state)."""
    name: str = "invariant_rule"

    def check(self, candidate_rows: Sequence[object], mutation_rows: Sequence[object]) -> None:
        raise NotImplementedError


@dataclass(kw_only=True)
class CountingInvariantRule(InvariantRule):
    """Groups candidate_rows and mutation_rows by group_key; any group
    present (>=1 row) in candidate_rows but absent (0 rows) from
    mutation_rows is a violation. Deliberately generic over what "a row"
    and "a group" mean -- a concrete category supplies its own group_key
    (a zone name, a (zone, vendor_type) tuple, a level bracket, ...)."""
    name: str
    group_key: Callable[[object], Hashable]

    def check(self, candidate_rows: Sequence[object], mutation_rows: Sequence[object]) -> None:
        before: set[Hashable] = {self.group_key(row) for row in candidate_rows}
        after: set[Hashable] = {self.group_key(row) for row in mutation_rows}
        lost = before - after
        if lost:
            raise InvariantViolation(
                f"{self.name}: {len(lost)} group(s) present before mutation have zero "
                f"matching rows after: {sorted(map(str, lost))[:5]}"
            )
