"""Category-agnostic check-density/sampling model (design spec §5.3).

One global check_density (0-100) plus a per-category proportional weight
decide how many rows of a given optional location category are sampled from
the full candidate set. A shared DensityBudget enforces a hard ceiling on the
running total across every category sampled against it in one generation, so
adding a new category later (a new content-table family, a new goal's
location set) never needs its own bespoke balancing code -- it calls
sample_category with its own weight and gets the same treatment as every
existing category.
"""
from __future__ import annotations

import math
import random


class DensityBudget:
    """One instance per world generation. check_density and hard_ceiling are
    resolved once from options at generation start; every category's
    sample_category call shares this same budget so the ceiling is a true
    cross-category total, not a per-category one."""

    def __init__(self, check_density: int, hard_ceiling: int) -> None:
        if not 0 <= check_density <= 100:
            raise ValueError(f"check_density must be 0-100, got {check_density}")
        if hard_ceiling < 0:
            raise ValueError(f"hard_ceiling must be >= 0, got {hard_ceiling}")
        self.check_density = check_density
        self.hard_ceiling = hard_ceiling
        self._consumed = 0

    def remaining(self) -> int:
        return max(0, self.hard_ceiling - self._consumed)

    def consume(self, n: int) -> None:
        self._consumed += n


def sample_category(budget: DensityBudget, category_weight: int, all_rows: list, rng: random.Random) -> list:
    """Sample this category's rows per the shared budget's check_density and
    this category's own weight (0-100, proportional -- not normalized against
    other categories' weights, since categories are toggled independently),
    then clamp to whatever of the hard ceiling remains. Order-independent:
    calling categories in a different order changes which category "wins" the
    last few ceiling slots, never how many total rows come out for a given
    call sequence with the same rng draws consumed in the same order.
    """
    if budget.check_density == 0 or category_weight == 0 or not all_rows:
        return []

    wanted = math.ceil(len(all_rows) * (budget.check_density / 100) * (category_weight / 100))
    wanted = min(wanted, len(all_rows), budget.remaining())
    if wanted <= 0:
        return []

    sampled = rng.sample(all_rows, wanted)
    budget.consume(len(sampled))
    return sampled
