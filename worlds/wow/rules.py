# Archipelago/worlds/wow/rules.py
from . import core_loop_content_data


# M2: all 19 Northshire/Goldshire locations are always accessible (no
# prerequisite logic yet -- matches the real quest line's actual structure,
# where these are early low-level quests with no hard level/item gates).
# Real access-rule logic (level gates, prerequisite quests, region gating
# for later zones) is deferred to M3 when the content pool grows beyond a
# single starting zone.
#
# M2.1: the 12 level-milestone and 2 instance-clear locations are likewise
# left unconditionally accessible here -- see the extended comment in
# locations.py's create_core_loop_locations for the known Death Knight
# reachability gap this leaves unmodeled.
def set_rules(world):
    pass


def set_completion_rule(world):
    # Sprint: reach level 60, which (per this milestone's fixed content
    # table) requires having received all 10 Progressive Level Cap copies --
    # starting cap 10, +5 each, 10 copies reaches exactly 60.
    world.set_completion_rule(
        lambda state: state.has(
            "Progressive Level Cap", world.player, core_loop_content_data.ITEMS["Progressive Level Cap"][1]
        )
    )
