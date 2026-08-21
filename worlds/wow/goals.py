# Archipelago/worlds/wow/goals.py
"""Per-mode goal<->category dependency validation (spec Sec5.4) and
completion rules. Every mode beyond Sprint is added here as content lands
for it -- see docs/m4-plan.md Group 6 for which modes are Tier 1/2/3."""
from __future__ import annotations

from Options import OptionError

from . import core_loop_content_data
from . import density
from . import fish_content_data
from . import rares_content_data


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


# Every instance_key core_loop.yaml defines, mapped to the display name its
# "Instance Unlock: <name>" item uses -- shared by Task 23's Tier-1 modes
# below and Task 24's Completionist mode, rather than each re-deriving it
# from instance_key via an ad-hoc string transform.
_INSTANCE_KEY_DISPLAY_NAMES = {
    "ragefire_chasm": "Ragefire Chasm",
    "deadmines": "Deadmines",
    "molten_core": "Molten Core",
    "sunwell_plateau": "Sunwell Plateau",
    "icecrown_citadel": "Icecrown Citadel",
}

# Task 23 (Tier 1): Classic/Burning Crusade/Wrath each gate on exactly one
# of the three raids that task added to core_loop.yaml -- Molten Core is
# Classic's own final raid, Sunwell Plateau is Burning Crusade's, Icecrown
# Citadel is Wrath's. Sharing one _validate_instance_clear_mode/
# _set_completion_rule_instance_clear pair rather than writing three nearly
# identical functions -- the only thing that varies per mode is which
# instance_key/display name to check.
_TIER1_RAID_INSTANCE_KEYS = {
    2: "molten_core",  # classic
    3: "sunwell_plateau",  # burning_crusade
    4: "icecrown_citadel",  # wrath
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


def _set_completion_rule_raid_instance_clear(instance_key: str):
    display_name = _INSTANCE_KEY_DISPLAY_NAMES[instance_key]

    def _set_rule(world) -> None:
        world.set_completion_rule(
            lambda state: state.has(f"Instance Unlock: {display_name}", world.player)
        )
    return _set_rule


# Task 24 (Completionist mode, design spec Sec5.4): requires clearing every
# instance_clear location tagged with the chosen expansion
# (completionist_expansion option -- vanilla/tbc/wotlk). Unlike Tier-1's
# single-raid modes, this can require more than one Instance Unlock item at
# once (vanilla currently has three: Ragefire Chasm, Deadmines, Molten
# Core), so it uses state.has_all rather than a single state.has.
def _validate_completionist(world) -> None:
    expansion = world.options.completionist_expansion.current_key
    instance_keys = core_loop_content_data.INSTANCES_BY_EXPANSION.get(expansion, [])
    if not instance_keys:
        raise OptionError(
            f"WoW: game_mode 'completionist' with completionist_expansion "
            f"'{expansion}' has no instance-clear locations tagged with "
            f"that expansion in core_loop.yaml."
        )


def _set_completion_rule_completionist(world) -> None:
    expansion = world.options.completionist_expansion.current_key
    instance_keys = core_loop_content_data.INSTANCES_BY_EXPANSION[expansion]
    item_names = {f"Instance Unlock: {_INSTANCE_KEY_DISPLAY_NAMES[key]}" for key in instance_keys}
    world.set_completion_rule(
        lambda state: state.has_all(item_names, world.player)
    )


# Task 25 (Key Hunt, Tier 2, design spec Sec5.4): completing the goal needs
# BOTH key_hunt_keys_required "Key Hunt: Key" items AND
# key_hunt_instances_required distinct raids/dungeons cleared -- the first
# mode whose completion condition spans two independently-sized, unrelated
# item families at once.
def _validate_key_hunt(world) -> None:
    # Reuses density.predict_sample_size (the same deterministic size math
    # sample_category itself uses) rather than waiting for create_regions to
    # have actually sampled rares.yaml's rows -- generate_early (where this
    # runs) happens BEFORE create_regions in AP's generation lifecycle, so
    # the real sampled count doesn't exist yet at this point.
    budget = density.DensityBudget(
        check_density=world.options.check_density.value,
        hard_ceiling=world.options.max_optional_locations.value,
    )
    predicted = density.predict_sample_size(budget, category_weight=100, row_count=len(rares_content_data.LOCATIONS))
    keys_required = world.options.key_hunt_keys_required.value
    if predicted < keys_required:
        raise OptionError(
            f"WoW: game_mode 'key_hunt' with key_hunt_keys_required={keys_required} "
            f"needs at least that many rares sampled into the pool, but "
            f"check_density={world.options.check_density.value} / "
            f"max_optional_locations={world.options.max_optional_locations.value} "
            f"would only sample {predicted} of the {len(rares_content_data.LOCATIONS)} "
            f"curated rares -- raise check_density/max_optional_locations or lower "
            f"key_hunt_keys_required."
        )


def _set_completion_rule_key_hunt(world) -> None:
    keys_required = world.options.key_hunt_keys_required.value
    instances_required = world.options.key_hunt_instances_required.value
    all_instance_unlock_names = {f"Instance Unlock: {name}" for name in _INSTANCE_KEY_DISPLAY_NAMES.values()}
    world.set_completion_rule(
        lambda state: (
            state.has("Key Hunt: Key", world.player, keys_required)
            and state.has_from_list_unique(all_instance_unlock_names, world.player, instances_required)
        )
    )


# Task 26 (Fishing Quest, Tier 2, design spec Sec5.4): completing the goal
# requires ALL 46 "Fish: <name>" items -- the fish set is bounded/discrete
# and NOT density-sampled (unlike Key Hunt's rares), so there is no
# "satisfiable at this density" check analogous to Key Hunt's validator; the
# validator here is a placeholder for future dependency growth, same shape
# as _validate_raid_instance_clear.
def _validate_fishing_quest(world) -> None:
    if not fish_content_data.LOCATIONS:
        raise OptionError(
            "WoW: game_mode 'fishing_quest' has no fish-catch locations in fish.yaml."
        )


def _set_completion_rule_fishing_quest(world) -> None:
    all_fish_names = set(fish_content_data.ITEMS.keys())
    world.set_completion_rule(
        lambda state: state.has_all(all_fish_names, world.player)
    )


# GameMode.value -> bare option name, for every mode without real content
# yet. Mirrors options.py's GameMode option_* attributes exactly -- keep
# both in sync when a Group 6 task gives one of these a real implementation.
_NOT_YET_IMPLEMENTED_MODE_NAMES = {
    6: "artisan",
    7: "collector",
    8: "achievement_hunt",
    9: "gladiator",
    10: "explorer",
}

_VALIDATORS = {
    0: _validate_sprint,
    1: _validate_key_hunt,
    **{value: _validate_raid_instance_clear(instance_key, _INSTANCE_KEY_DISPLAY_NAMES[instance_key])
       for value, instance_key in _TIER1_RAID_INSTANCE_KEYS.items()},
    5: _validate_completionist,
    11: _validate_fishing_quest,
    **{value: _not_yet_implemented(name) for value, name in _NOT_YET_IMPLEMENTED_MODE_NAMES.items()},
}

_COMPLETION_RULES = {
    0: _set_completion_rule_sprint,
    1: _set_completion_rule_key_hunt,
    **{value: _set_completion_rule_raid_instance_clear(instance_key)
       for value, instance_key in _TIER1_RAID_INSTANCE_KEYS.items()},
    5: _set_completion_rule_completionist,
    11: _set_completion_rule_fishing_quest,
    **{value: _not_yet_implemented(name) for value, name in _NOT_YET_IMPLEMENTED_MODE_NAMES.items()},
}
