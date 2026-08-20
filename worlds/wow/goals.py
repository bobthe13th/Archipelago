# Archipelago/worlds/wow/goals.py
"""Per-mode goal<->category dependency validation (spec Sec5.4) and
completion rules. Every mode beyond Sprint is added here as content lands
for it -- see docs/m4-plan.md Group 6 for which modes are Tier 1/2/3."""
from __future__ import annotations

from Options import OptionError

from . import core_loop_content_data


def validate(world) -> None:
    """Called from generate_early, before create_regions/create_items/
    set_rules -- a bad game_mode/option combination must fail generation
    loudly here (spec Sec5.3: "fail generation with a clear message"), not
    surface later as a confusing KeyError/FillError once regions or items
    already exist."""
    _VALIDATORS[world.options.game_mode.value](world)


def set_completion_rule_for_mode(world) -> None:
    """Replaces rules.py's old Sprint-only set_completion_rule with the same
    dispatch shape as validate() above -- called from World.set_rules() after
    set_rules(world). Every non-Sprint entry here is unreachable in practice
    (validate() already raised during generate_early for any mode without a
    real entry), but each still resolves to the same _NOT_YET_IMPLEMENTED
    raiser rather than a KeyError, in case that invariant is ever broken by a
    future refactor."""
    _COMPLETION_RULES[world.options.game_mode.value](world)


def _validate_sprint(world) -> None:
    pass  # no dependency: core-loop content always exists


def _set_completion_rule_sprint(world) -> None:
    # Sprint: reach level 60, which (per this milestone's fixed content
    # table) requires having received all 10 Progressive Level Cap copies --
    # starting cap 10, +5 each, 10 copies reaches exactly 60. Moved here
    # unchanged from rules.py's original set_completion_rule (Task 22).
    world.set_completion_rule(
        lambda state: state.has(
            "Progressive Level Cap", world.player, core_loop_content_data.ITEMS["Progressive Level Cap"][1]
        )
    )


def _not_yet_implemented(mode_name: str):
    def _raise(world) -> None:
        raise OptionError(
            f"WoW: game_mode '{mode_name}' has no content yet in this repo -- "
            f"see docs/m4-plan.md Group 6 before enabling it."
        )
    return _raise


# Task 23 (Tier 1): Classic/Burning Crusade/Wrath each gate on exactly one
# of the three raids that task added to core_loop.yaml -- Molten Core is
# Classic's own final raid, Sunwell Plateau is Burning Crusade's, Icecrown
# Citadel is Wrath's. Sharing one _validate_instance_clear_mode/
# _set_completion_rule_instance_clear pair rather than writing three nearly
# identical functions -- the only thing that varies per mode is which
# instance_key/display name to check.
_TIER1_RAID_INSTANCE_KEYS = {
    2: ("molten_core", "Molten Core"),  # classic
    3: ("sunwell_plateau", "Sunwell Plateau"),  # burning_crusade
    4: ("icecrown_citadel", "Icecrown Citadel"),  # wrath
}


def _validate_raid_instance_clear(instance_key: str, display_name: str):
    def _validate(world) -> None:
        # Mostly a placeholder for future dependency growth (per this task's
        # own Step 6 note) -- true today as long as core_loop.yaml's Task 23
        # rows exist, which create_regions always adds unconditionally (this
        # instance-clear location is not subject to check_density sampling).
        if instance_key not in core_loop_content_data.INSTANCE_CLEAR_LOCATIONS:
            raise OptionError(
                f"WoW: game_mode requires the '{display_name}' instance-clear "
                f"location, but it is missing from core_loop.yaml."
            )
    return _validate


def _set_completion_rule_raid_instance_clear(instance_key: str, display_name: str):
    def _set_rule(world) -> None:
        world.set_completion_rule(
            lambda state: state.has(f"Instance Unlock: {display_name}", world.player)
        )
    return _set_rule


# GameMode.value -> bare option name, for every mode without real content
# yet. Mirrors options.py's GameMode option_* attributes exactly -- keep
# both in sync when a Group 6 task gives one of these a real implementation.
_NOT_YET_IMPLEMENTED_MODE_NAMES = {
    1: "key_hunt",
    5: "completionist",
    6: "artisan",
    7: "collector",
    8: "achievement_hunt",
    9: "gladiator",
    10: "explorer",
    11: "fishing_quest",
}

_VALIDATORS = {
    0: _validate_sprint,
    **{
        value: _validate_raid_instance_clear(instance_key, display_name)
        for value, (instance_key, display_name) in _TIER1_RAID_INSTANCE_KEYS.items()
    },
    **{value: _not_yet_implemented(name) for value, name in _NOT_YET_IMPLEMENTED_MODE_NAMES.items()},
}

_COMPLETION_RULES = {
    0: _set_completion_rule_sprint,
    **{
        value: _set_completion_rule_raid_instance_clear(instance_key, display_name)
        for value, (instance_key, display_name) in _TIER1_RAID_INSTANCE_KEYS.items()
    },
    **{value: _not_yet_implemented(name) for value, name in _NOT_YET_IMPLEMENTED_MODE_NAMES.items()},
}
