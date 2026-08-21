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
# producing permanently unwinnable seeds. See the extended comment in
# locations.py's create_core_loop_locations for the (separate, still
# accepted) Death Knight reachability gap, which this fix does not change.
def set_rules(world):
    starting_cap = core_loop_content_data.STARTING_LEVEL_CAP
    step = core_loop_content_data.LEVEL_CAP_STEP
    # Death Knight characters start at level 55 via a path that bypasses the
    # level-up hook (see locations.py's create_core_loop_locations docstring),
    # so the 11 locations for level < 55 are physically unreachable for that
    # class. Gating every one of them behind the SAME copy count as level 55
    # (rather than each level's own smaller threshold) doesn't change what's
    # needed to win a seed -- Progressive Level Cap copies are fungible, only
    # the total held count matters (state.has doesn't track provenance) --
    # but it guarantees any copy the fill algorithm places on one of those 11
    # locations is logically redundant (obtainable only once nearly done),
    # forcing every ESSENTIAL copy to land somewhere DK-reachable (the 19 M2
    # quest locations, Reach Level 55/60, or either instance clear).
    level_55_copies_needed = max(0, math.ceil((55 - starting_cap) / step))
    for level, _location_id in core_loop_content_data.LEVEL_LOCATIONS.items():
        copies_needed = level_55_copies_needed if level <= 55 else max(
            0, math.ceil((level - starting_cap) / step)
        )
        location = world.get_location(f"Reach Level {level}")
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

    # M4.5 Task 6 (Quest Rewards): reuses the EXACT same "copies_needed via
    # Progressive Level Cap" math as the level-milestone loop above (this
    # function's own lines 40-52), since a quest_reward's min_level is the
    # identical underlying constraint -- can't turn in a quest that requires
    # a level you haven't reached yet -- just applied to a different content
    # family. Only meaningful when include_quest_rewards is on, since that's
    # the only time quest_rewards_content_data's locations exist in the pool
    # at all (locations.py's OptionalCategory registration).
    #
    # CLAMP (real defect found while implementing this task, not present in
    # the brief's original snippet): content/quest_rewards.yaml is DB-derived
    # and its raw min_level values run all the way up to 255 (TBC/Wrath-era
    # quests and a few sentinel/placeholder rows), while Sprint mode's own
    # item pool only ever contains a FIXED 10 "Progressive Level Cap" copies
    # (core_loop_content_data.ITEMS["Progressive Level Cap"][1] -- the same
    # count that caps out at level 60 for the "Reach Level 60"/Sprint-goal
    # locations above). An unclamped copies_needed for a min_level=255 quest
    # would demand more copies than exist anywhere in the pool, making that
    # location permanently unreachable and failing generation outright
    # (confirmed empirically: test_all_state_can_reach_everything and
    # test_fill both failed before this clamp was added). Clamping to
    # total_caps mirrors the DK-safe clamp already used for levels <= 55
    # above -- once every copy is held, every quest_reward location must be
    # reachable, regardless of how large its raw min_level is.
    if world.options.include_quest_rewards:
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
