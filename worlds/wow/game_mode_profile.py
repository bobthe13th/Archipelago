"""Per-game-mode content-eligibility and density-override registry (M4.6).
Generalizes the dispatch-table pattern goals.py already uses for
_VALIDATORS/_COMPLETION_RULES, but for "is this optional category even
eligible in this mode" and "what density applies in this mode" instead of
goal validation/completion. A separate module from locations.py/items.py to
avoid the circular-import shape items.py already documents and works around
when it needs locations.py's _OPTIONAL_CATEGORIES at call time, not import
time.

Every GameMode value not listed in _PROFILES resolves to _DEFAULT_PROFILE,
identical to every existing mode's behavior today -- adding a new mode here
is additive only. Barrensanity (M4.7) and WotLK Raiding Progression (M4.8)
each add one _PROFILES entry when their own milestone lands; neither needs
this module's shape to change."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GameModeProfile:
    force_all_categories: bool = False
    force_max_density: bool = False
    eligible_categories: Optional[set[str]] = None  # None = every registered category eligible


_PROFILES: dict[int, GameModeProfile] = {
    12: GameModeProfile(force_all_categories=True, force_max_density=True),  # hundred_percent
}
_DEFAULT_PROFILE = GameModeProfile()


def get_profile(game_mode_value: int) -> GameModeProfile:
    return _PROFILES.get(game_mode_value, _DEFAULT_PROFILE)


def is_category_eligible(world, category) -> bool:
    """Whether `category` is ALLOWED to be considered at all for the
    current game mode (GameModeProfile.eligible_categories/
    force_all_categories) -- NOT whether it will actually contribute any
    locations. As of M4.8.0, "will it contribute locations" is entirely
    owned by tag/weight filtering (locations.py's _location_matches_pools +
    density.sample_category), since there is no longer a single per-category
    boolean toggle to read (OptionalCategory dropped its old toggle_option
    field -- see the M4.8.0 plan's Global Constraints for why this function
    still exists as a separate, narrower check rather than being inlined
    away)."""
    profile = get_profile(world.options.game_mode.value)
    if profile.eligible_categories is not None and category.key not in profile.eligible_categories:
        return False
    return True


def effective_check_density(world) -> int:
    profile = get_profile(world.options.game_mode.value)
    return 100 if profile.force_max_density else world.options.check_density.value
