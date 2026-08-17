# Archipelago/worlds/wow/rules.py
import math

from . import core_loop_content_data


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
    for level, _location_id in core_loop_content_data.LEVEL_LOCATIONS.items():
        # Number of Progressive Level Cap copies that must already have been
        # received in order for the character to be able to gain XP up to
        # (and be able to turn in / trigger) this level's milestone check.
        copies_needed = max(0, math.ceil((level - starting_cap) / step))
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


def set_completion_rule(world):
    # Sprint: reach level 60, which (per this milestone's fixed content
    # table) requires having received all 10 Progressive Level Cap copies --
    # starting cap 10, +5 each, 10 copies reaches exactly 60.
    world.set_completion_rule(
        lambda state: state.has(
            "Progressive Level Cap", world.player, core_loop_content_data.ITEMS["Progressive Level Cap"][1]
        )
    )
