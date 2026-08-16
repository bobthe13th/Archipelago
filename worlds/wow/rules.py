# Archipelago/worlds/wow/rules.py
# M2: all 19 Northshire/Goldshire locations are always accessible (no
# prerequisite logic yet -- matches the real quest line's actual structure,
# where these are early low-level quests with no hard level/item gates).
# Real access-rule logic (level gates, prerequisite quests, region gating
# for later zones) is deferred to M3 when the content pool grows beyond a
# single starting zone.
def set_rules(world):
    pass
