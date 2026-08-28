# Archipelago/worlds/wow/goals.py
"""Per-mode goal<->category dependency validation (spec Sec5.4) and
completion rules. Every mode beyond Sprint is added here as content lands
for it -- see docs/m4-plan.md Group 6 for which modes are Tier 1/2/3."""
from __future__ import annotations

import math

from Options import OptionError

from . import achievements_content_data
from . import collections_content_data
from . import core_loop_content_data
from . import density
from . import fish_content_data
from . import game_mode_profile
from . import professions_content_data
from . import rares_content_data
from .locations import _OPTIONAL_CATEGORIES


def validate(world) -> None:
    """Called from generate_early, before create_regions/create_items/
    set_rules -- a bad game_mode/option combination must fail generation
    loudly here (spec Sec5.3: "fail generation with a clear message"), not
    surface later as a confusing KeyError/FillError once regions or items
    already exist."""
    _validate_filler_category_pools_nonempty(world)
    _VALIDATORS[world.options.game_mode.value](world)


def _validate_filler_category_pools_nonempty(world) -> None:
    """Mode-independent check, run before the per-mode _VALIDATORS dispatch
    below: core_loop's every-level item pool has a real, unconditional
    dependency on Filler to close its own item/location deficit in every
    game_mode, not just Sprint (create_core_loop_item_pool pads the pool
    with create_filler_item_pool(world, deficit) whenever core_loop.yaml's
    milestone granularity leaves the standard/death_knight tracks short --
    64 items on the standard track, 10 on death_knight, per items.py's own
    create_filler_item_pool docstring). An empty FillerCategoryPools
    selection has zero eligible items to draw from, so that deficit can
    never be closed -- left unchecked, this surfaces later as a raw,
    confusing Fill.FillError deep in generation instead of a clear,
    actionable message here."""
    if not world.options.filler_category_pools.value:
        raise OptionError(
            "WoW: filler_category_pools is empty -- core_loop's item pool "
            "has an unconditional dependency on Filler to close its own "
            "item/location deficit (up to 64 items on the standard track, "
            "10 on the death_knight track, per create_filler_item_pool's "
            "docstring), and an empty category selection has no eligible "
            "items to draw from. Select at least one FillerCategoryPools "
            "category."
        )


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
    # Sprint: reach level 60. M4.9: Progressive Level Cap's total pooled
    # copy count grew from 10 to 14 (core_loop.yaml, to support the
    # every-level milestone track's own level-80 ceiling: starting cap 10 +
    # 14 * step 5 = 80) -- Sprint's own goal is still level 60, not 80, so
    # this rule can no longer use "hold ALL copies" (that used to be
    # coincidentally correct only because the old total was tuned to stop
    # exactly at 60). Derive the real level-60 threshold from the same
    # constants the cap-raise math itself uses, instead of hardcoding 10 or
    # reading the total ITEMS count.
    copies_for_sprint_goal = math.ceil(
        (core_loop_content_data.SPRINT_GOAL_LEVEL - core_loop_content_data.STARTING_LEVEL_CAP)
        / core_loop_content_data.LEVEL_CAP_STEP
    )
    world.set_completion_rule(
        lambda state: state.has(
            "Progressive Level Cap", world.player, copies_for_sprint_goal
        )
    )


def _not_yet_implemented(mode_name: str):
    def _raise(world) -> None:
        raise OptionError(
            f"WoW: game_mode '{mode_name}' has no content yet in this repo -- "
            f"see docs/m4-plan.md Group 6 before enabling it."
        )
    return _raise


# Task 27's own Step 1 research found that data/sql/base/db_world's
# *_dbc.sql tables (achievement_dbc, achievement_criteria_dbc, areatable_dbc,
# and several others) are empty stub schemas in this checkout -- zero data
# rows -- and no binary .dbc client files exist in the repo either. This is
# a DIFFERENT category of deferral from _not_yet_implemented above: it is
# not that nobody has built this mode's content yet, it is that the real
# achievement/area-name data this mode's "full roster" would need to be
# extracted FROM does not exist anywhere in this checkout, matching Task 9's
# earlier "not buildable" finding for continent/city/zone gates (verified,
# not assumed) rather than a scheduling gap.
def _not_buildable(mode_name: str, reason: str):
    def _raise(world) -> None:
        raise OptionError(
            f"WoW: game_mode '{mode_name}' cannot be built in this checkout -- "
            f"{reason} See docs/m4-plan.md Task 27's outcome note."
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
    predicted = density.predict_sample_size(
        game_mode_profile.effective_check_density(world), category_weight=100, row_count=len(rares_content_data.LOCATIONS)
    )
    keys_required = world.options.key_hunt_keys_required.value
    if predicted < keys_required:
        raise OptionError(
            f"WoW: game_mode 'key_hunt' with key_hunt_keys_required={keys_required} "
            f"needs at least that many rares sampled into the pool, but "
            f"check_density={world.options.check_density.value} "
            f"would only sample {predicted} of the {len(rares_content_data.LOCATIONS)} "
            f"curated rares -- raise check_density or lower "
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


# Task 27 (Artisan, Tier 3, design spec Sec5.4): completing the goal
# requires all 3 secondary professions AND artisan_primary_professions_required
# of the 11 primary professions to reach skill 450 -- not density-sampled
# when artisan is the active mode (professions.yaml's own header comment).
def _validate_artisan(world) -> None:
    if not professions_content_data.LOCATIONS:
        raise OptionError(
            "WoW: game_mode 'artisan' has no profession skill-milestone locations in professions.yaml."
        )


def _set_completion_rule_artisan(world) -> None:
    required = world.options.artisan_primary_professions_required.value
    secondary_names = professions_content_data.SECONDARY_PROFESSION_MAX_ITEM_NAMES
    primary_names = professions_content_data.PRIMARY_PROFESSION_MAX_ITEM_NAMES
    world.set_completion_rule(
        lambda state: (
            state.has_all(secondary_names, world.player)
            and state.has_from_list_unique(primary_names, world.player, required)
        )
    )


# Task 27 (Collector, Tier 3, design spec Sec5.4): completing the goal
# requires at least collector_items_required of the 264 "Mount: <name>" /
# "Pet: <name>" items -- not density-sampled when collector is the active
# mode (collections.yaml's own header comment), same "gated on game_mode
# itself" shape as Artisan/Fishing Quest. Default (264, the full roster)
# matches Fishing Quest's has_all-everything shape exactly, per the design
# spec's own "every collectible mount AND every collectible pet" scope --
# AP item delivery isn't gated by the mount/pet's original in-game drop
# rarity, so (unlike Artisan's hard profession-slot constraint) there is no
# mechanical reason the default should require fewer than all of them. The
# option exists purely so a shorter Collector run is selectable per-seed,
# using has_from_list_unique rather than has_all so a non-default,
# lower-than-264 value still resolves correctly.
def _validate_collector(world) -> None:
    if not collections_content_data.LOCATIONS:
        raise OptionError(
            "WoW: game_mode 'collector' has no mount/pet locations in collections.yaml."
        )


def _set_completion_rule_collector(world) -> None:
    required = world.options.collector_items_required.value
    all_names = set(collections_content_data.ITEMS.keys())
    world.set_completion_rule(
        lambda state: state.has_from_list_unique(all_names, world.player, required)
    )


# M4.6 Task 7 (100% mode, M4.6 design spec Sec3): completing the goal requires
# collecting literally everything -- all 10 Progressive Level Cap copies,
# every Instance Unlock item, and every optional-category item this seed
# actually sampled. Only meaningful when at least one OptionalCategory is
# registered (locations.py's _OPTIONAL_CATEGORIES) -- with zero registered,
# "100%" would be indistinguishable from Sprint's own completion condition.
def _validate_hundred_percent(world) -> None:
    if not _OPTIONAL_CATEGORIES:
        raise OptionError(
            "WoW: game_mode 'hundred_percent' requires at least one optional "
            "category to be registered in this build -- none are (see "
            "locations.OptionalCategory registrations)."
        )


def _set_completion_rule_hundred_percent(world) -> None:
    level_cap_copies = core_loop_content_data.ITEMS["Progressive Level Cap"][1]
    instance_unlock_names = {
        f"Instance Unlock: {name}" for name in _INSTANCE_KEY_DISPLAY_NAMES.values()
    }
    sampled_names = getattr(world, "optional_category_sampled_names", set())
    remaining_names = instance_unlock_names | sampled_names
    world.set_completion_rule(
        lambda state: state.has("Progressive Level Cap", world.player, level_cap_copies)
        and state.has_all(remaining_names, world.player)
    )


# M4.9 Sec4 (Achievement Hunt, built for real): three curated tiers, all
# drawn from the SAME compiled achievements_content_data table --
# hundred_percent is every location that table exposes, ninety_nine_percent
# excludes the hand-curated EXTREMELY_HARD_ITEM_NAMES set, named_subset
# requires exactly one of ACHIEVEMENTS_BY_SUBSET's six real, category-
# derived groups. Every achievement location/item ALWAYS exists in the pool
# regardless of which tier is chosen (create_achievement_locations below) --
# only this target set (what the completion RULE requires) differs, the
# same "every location exists, only the threshold differs" shape Collector's
# collector_items_required already established.
def _achievement_hunt_target_item_names(world) -> frozenset[str]:
    tier = world.options.achievement_hunt_tier.current_key
    if tier == "named_subset":
        subset = world.options.achievement_hunt_subset.current_key
        return achievements_content_data.ACHIEVEMENTS_BY_SUBSET.get(subset, frozenset())
    all_names = frozenset(achievements_content_data.ITEMS.keys())
    if tier == "ninety_nine_percent":
        return all_names - achievements_content_data.EXTREMELY_HARD_ITEM_NAMES
    return all_names  # hundred_percent


def _validate_achievement_hunt(world) -> None:
    if not achievements_content_data.LOCATIONS:
        raise OptionError(
            "WoW: game_mode 'achievement_hunt' has no achievement locations in achievements.yaml."
        )
    target = _achievement_hunt_target_item_names(world)
    if not target:
        raise OptionError(
            f"WoW: game_mode 'achievement_hunt' with achievement_hunt_tier="
            f"'{world.options.achievement_hunt_tier.current_key}' and achievement_hunt_subset="
            f"'{world.options.achievement_hunt_subset.current_key}' resolves to an empty target "
            f"set -- nothing to complete."
        )


def _set_completion_rule_achievement_hunt(world) -> None:
    target = _achievement_hunt_target_item_names(world)
    world.set_completion_rule(lambda state: state.has_all(target, world.player))


# M4.9 Sec4 (Explorer, rebuilt for real): a single location/item pair, the
# real "World Explorer" achievement (id 46, drawn from the exact same
# compiled achievements_content_data table Achievement Hunt uses -- both
# key off the same shared OnPlayerAchievementComplete hook, per the spec),
# replacing the previous custom subzone-visit-tracker design entirely.
def _validate_explorer(world) -> None:
    if achievements_content_data.WORLD_EXPLORER_LOCATION_NAME not in achievements_content_data.LOCATIONS:
        raise OptionError(
            "WoW: game_mode 'explorer' requires the World Explorer achievement location, "
            "but it is missing from achievements.yaml."
        )


def _set_completion_rule_explorer(world) -> None:
    world.set_completion_rule(
        lambda state: state.has(achievements_content_data.WORLD_EXPLORER_ITEM_NAME, world.player)
    )


# GameMode.value -> bare option name, for every mode without real content
# yet (scheduling gap, not a data-availability problem). Mirrors
# options.py's GameMode option_* attributes exactly -- keep both in sync
# when a Group 6 task gives one of these a real implementation.
_NOT_YET_IMPLEMENTED_MODE_NAMES = {}

# GameMode.value -> (bare option name, reason) for modes that cannot be
# built in this checkout at all, because the "full roster" cannot
# be extracted from any real data source this checkout has. Gladiator is no
# longer listed here at all as of M4.9 -- it was removed from GameMode's
# Choice values entirely (options.py) rather than kept as a permanent
# hard-fail option, since a deleted enum value fails generation even more
# clearly (before goals.py's own validation ever runs) than an OptionError
# from this dispatch table did.
_NOT_BUILDABLE_MODES = {}

_VALIDATORS = {
    0: _validate_sprint,
    1: _validate_key_hunt,
    **{value: _validate_raid_instance_clear(instance_key, _INSTANCE_KEY_DISPLAY_NAMES[instance_key])
       for value, instance_key in _TIER1_RAID_INSTANCE_KEYS.items()},
    5: _validate_completionist,
    6: _validate_artisan,
    7: _validate_collector,
    8: _validate_achievement_hunt,
    10: _validate_explorer,
    11: _validate_fishing_quest,
    12: _validate_hundred_percent,  # option_hundred_percent
    **{value: _not_yet_implemented(name) for value, name in _NOT_YET_IMPLEMENTED_MODE_NAMES.items()},
    **{value: _not_buildable(name, reason) for value, (name, reason) in _NOT_BUILDABLE_MODES.items()},
}

_COMPLETION_RULES = {
    0: _set_completion_rule_sprint,
    1: _set_completion_rule_key_hunt,
    **{value: _set_completion_rule_raid_instance_clear(instance_key)
       for value, instance_key in _TIER1_RAID_INSTANCE_KEYS.items()},
    5: _set_completion_rule_completionist,
    6: _set_completion_rule_artisan,
    7: _set_completion_rule_collector,
    8: _set_completion_rule_achievement_hunt,
    10: _set_completion_rule_explorer,
    11: _set_completion_rule_fishing_quest,
    12: _set_completion_rule_hundred_percent,  # option_hundred_percent
    **{value: _not_yet_implemented(name) for value, name in _NOT_YET_IMPLEMENTED_MODE_NAMES.items()},
    **{value: _not_buildable(name, reason) for value, (name, reason) in _NOT_BUILDABLE_MODES.items()},
}
