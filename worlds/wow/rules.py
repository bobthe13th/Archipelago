# Archipelago/worlds/wow/rules.py
import math

from . import core_loop_content_data
from . import fish_content_data
from . import quest_rewards_content_data


# M2: all 19 Northshire/Goldshire locations are always accessible (no
# prerequisite logic yet -- matches the real quest line's actual structure,
# where these are early low-level quests with no hard level/item gates).
# Real access-rule logic (level gates, prerequisite quests, region gating
# for later zones) is deferred to M3 when the content pool grows beyond a
# single starting zone.
#
# M2.1 (final-review fix): the 12 level-milestone and 2 instance-clear
# locations must NOT be left unconditionally accessible -- the real C++
# server enforces genuine prerequisites (you can't gain XP past your
# current level cap without already holding enough Progressive Level Cap
# items; you can't enter Ragefire Chasm/Deadmines without already holding
# the matching Instance Unlock item). Leaving these locations rule-free let
# the fill algorithm place a required Progressive Level Cap copy on a
# milestone location that itself required already having that copy,
# producing permanently unwinnable seeds. M4.9: the separate Death Knight
# reachability gap this comment used to describe as "still accepted" is
# now resolved via a two-track split -- see locations.py's
# create_core_loop_locations for the real mechanism and its own trust-model
# caveat.
def set_rules(world):
    starting_cap = core_loop_content_data.STARTING_LEVEL_CAP
    step = core_loop_content_data.LEVEL_CAP_STEP
    # M4.9: the M2.1-era Death Knight "safety collapse" (every level < 55
    # location required the SAME copy count as level 55, so a required
    # Progressive Level Cap copy could never land somewhere DK-unreachable)
    # is retired, superseded by locations.py's own two-track split
    # (core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK["standard"] vs
    # ["death_knight"]). A death_knight_slot=True slot now only ever
    # creates the death_knight track's 55-80 locations to begin with, so
    # there is no longer any DK-unreachable "Reach Level N" location in the
    # pool for that slot to collapse away -- every location (on whichever
    # track this slot actually created) can use its own natural per-level
    # threshold.
    is_dk_slot = bool(world.options.death_knight_slot)
    track = "death_knight" if is_dk_slot else "standard"
    for level, _location_id in core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK[track].items():
        copies_needed = max(0, math.ceil((level - starting_cap) / step))
        name = core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK[track][level]
        location = world.get_location(name)
        if copies_needed > 0:
            world.set_rule(
                location,
                lambda state, count=copies_needed: state.has(
                    "Progressive Level Cap", world.player, count
                ),
            )

    world.set_rule(
        world.get_location("Clear Ragefire Chasm"),
        lambda state: state.has("Instance Unlock: Ragefire Chasm", world.player),
    )
    world.set_rule(
        world.get_location("Clear Deadmines"),
        lambda state: state.has("Instance Unlock: Deadmines", world.player),
    )

    # Task 26 (Fishing Quest, spec Sec5.4): "fish-catch locations inherit
    # normal regional access logic -- a Northrend-only fish requires
    # Northrend Passage in logic". Only meaningful when game_mode is
    # fishing_quest, since that's the only time fish.yaml's locations exist
    # in the pool at all (create_fish_locations' own game_mode check) --
    # world.get_location would KeyError for any other mode.
    if world.options.game_mode == "fishing_quest":
        for name in fish_content_data.NORTHREND_LOCATION_NAMES:
            world.set_rule(
                world.get_location(name),
                lambda state: state.has("Northrend Passage", world.player),
            )

    # M4.5 Task 6 (Quest Rewards), M4.8.0: unconditional -- include_quest_rewards
    # was removed in favor of tag/weight filtering (options.py, locations.py),
    # and this loop's own per-location `continue` guards already no-op
    # correctly when zero quest_rewards locations exist in the pool (weight
    # 0, or every tag dimension narrowed to nothing), so there's no longer a
    # single toggle to gate this on. Also now covers the 19 locations
    # migrated from the retired `quests` family (always_present, M4.8.0)
    # with zero extra code -- they're ordinary quest_rewards rows with real
    # DB-derived min_level values, so this exact clamp applies to them the
    # same as every other quest_reward.
    total_caps = core_loop_content_data.ITEMS["Progressive Level Cap"][1]
    for loc in world.multiworld.get_locations(world.player):
        if not loc.name.startswith("Quest:") or loc.name not in quest_rewards_content_data.LOCATIONS:
            continue
        trigger = quest_rewards_content_data.TRIGGERS[loc.name]
        copies_needed = min(total_caps, max(0, math.ceil((trigger["min_level"] - starting_cap) / step)))
        if copies_needed > 0:
            world.set_rule(
                loc,
                lambda state, count=copies_needed: state.has("Progressive Level Cap", world.player, count),
            )
