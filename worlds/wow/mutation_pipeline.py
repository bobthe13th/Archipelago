"""M5.0 Sec3: shared generation-time mutation driver for Pipeline B. Each
of M5.1-M5.6 registers its own MutationCategory into _MUTATION_CATEGORIES
(mirroring locations.py's _OPTIONAL_CATEGORIES idiom); run_all_categories
(called from __init__.py's pre_output) drives every registered category
through candidate resolution -> AP-claimed-row exclusion
(mutation_claimed_rows.py) -> mutate -> invariant validation
(mutation_invariants.py), with an internal sub-seed retry loop (up to
MAX_ATTEMPTS) on invariant failure -- standard Archipelago generation halts
on exceptions rather than retrying, so the driver must not surface a
transient invariant failure as an immediate OptionError (Sec3)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Sequence

from Options import OptionError

from . import mutation_claimed_rows
from .mutation_invariants import InvariantRule, InvariantViolation
from .world_seed import derive_sub_seed

MAX_ATTEMPTS = 10

# A candidate/mutation row: (table_name, row_key, payload). row_key mirrors
# mutation_claimed_rows.ClaimedRow's own row_key shape for that table, so a
# plain (row[0], row[1]) membership test against claimed_rows()'s output is
# exact, never approximate.
MutationRow = tuple


@dataclass
class MutationCategory:
    """Sec3's own target shape. key must be globally unique across
    M5.1-M5.6 (used to derive this category's own sub-seed and to key its
    slot in the mutation-data file, Sec6). mutate() returns ONLY the rows
    it actually changed -- a subset of candidates, keyed by row identity
    (row[0], row[1]) -- never the full untouched candidate pool: Sec3's
    "every individual mutated mob's new level" and Sec6's "full concrete
    mutation table" both describe the mutated subset, not every candidate
    whether touched or not. Returning the full pool would bloat the
    mutation-data file and make APWorldState issue redundant SQL UPDATEs
    for rows that never changed."""
    key: str
    candidate_rows: Callable[[object], Sequence[MutationRow]]
    mutate: Callable[[Sequence[MutationRow], random.Random], Sequence[MutationRow]]
    invariant_rules: list[InvariantRule] = field(default_factory=list)


_MUTATION_CATEGORIES: list[MutationCategory] = []


def register_category(category: MutationCategory) -> None:
    """Called once at import time by each of M5.1-M5.6's own content-data
    module, mirroring locations.py's _OPTIONAL_CATEGORIES.append idiom."""
    _MUTATION_CATEGORIES.append(category)


def _row_key(row: MutationRow) -> tuple:
    table_name, row_key, _payload = row
    return (table_name, row_key)


def run_category(
    category: MutationCategory,
    world,
    world_seed: str,
    claimed: set,
) -> list[MutationRow]:
    all_candidates = list(category.candidate_rows(world))
    candidates = [row for row in all_candidates if _row_key(row) not in claimed]

    last_error: InvariantViolation | None = None
    for attempt in range(MAX_ATTEMPTS):
        sub_seed = derive_sub_seed(world_seed, category.key, attempt)
        rng = random.Random(sub_seed)
        mutation_rows = list(category.mutate(candidates, rng))
        # mutate() returns only the changed subset (see MutationCategory's
        # own docstring) -- invariant rules need the FULL post-mutation
        # picture (unmodified candidates + mutated rows) to judge "after"
        # correctly, or every untouched group would spuriously read as
        # "lost". The diff itself (mutation_rows) is still what's
        # returned/persisted -- only the invariant check sees the
        # reconstructed full state.
        mutated_keys = {_row_key(row) for row in mutation_rows}
        unmodified_candidates = [row for row in candidates if _row_key(row) not in mutated_keys]
        full_after_state = unmodified_candidates + mutation_rows
        try:
            for rule in category.invariant_rules:
                rule.check(candidates, full_after_state)
            return mutation_rows
        except InvariantViolation as exc:
            last_error = exc
            continue

    raise OptionError(
        f"World of Warcraft: Pipeline B category '{category.key}' failed its invariant "
        f"checks {MAX_ATTEMPTS} times in a row (world_seed={world_seed}): {last_error}"
    )


def run_all_categories(world, world_seed: str) -> dict[str, list[MutationRow]]:
    """Returns {category_key: mutation_rows}, one entry per registered
    category (empty list for a category left at 'vanilla'). M5.0 itself
    registers none, so this is unconditionally {} until M5.1 lands."""
    claimed = mutation_claimed_rows.claimed_rows(world)
    return {
        category.key: run_category(category, world, world_seed, claimed)
        for category in _MUTATION_CATEGORIES
    }
