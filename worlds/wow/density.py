"""Category-agnostic check-density/sampling model (design spec §5.3).

One check_density (0-100) plus a per-category proportional weight decide how
many rows of a given optional location category are sampled from the full
candidate set. As of M4.6 there is no cross-category ceiling: each category's
sample_category call is independent. A game mode that wants a different
effective density (e.g. 100%'s forced-max) resolves that through
game_mode_profile.effective_check_density, not through this module.
"""
from __future__ import annotations

import math
import random


def predict_sample_size(check_density: int, category_weight: int, row_count: int) -> int:
    """Deterministic size math only -- no ceiling, no rng. Used both by
    sample_category (to compute how many rows to draw) and by any
    generation-time validator that needs to know a category's predicted
    count before create_regions has actually sampled it."""
    if check_density == 0 or category_weight == 0 or row_count == 0:
        return 0
    return math.ceil(row_count * (check_density / 100) * (category_weight / 100))


def sample_category(check_density: int, category_weight: int, all_rows: list, rng: random.Random) -> list:
    """Sample this category's rows: check_density (0-100, global or
    game-mode-forced) times this category's own weight (0-100, proportional
    -- not normalized against other categories' weights). No cross-category
    ceiling as of M4.6 -- each category is sampled independently of every
    other category's own draw."""
    wanted = predict_sample_size(check_density, category_weight, len(all_rows))
    return rng.sample(all_rows, wanted) if wanted > 0 else []
