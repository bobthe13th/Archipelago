# Archipelago/worlds/wow/core_loop_content_data.py
# HAND-CURATED, mirrors azerothcore-wotlk/modules/archipelago_wow/src/ArchipelagoCoreLoopContentTable.h
# Keep both in sync by hand -- every id below must match exactly.

STARTING_LEVEL_CAP = 10
LEVEL_CAP_STEP = 5
SPRINT_GOAL_LEVEL = 60

# name -> (AP item id, copies in the pool)
ITEMS: dict[str, tuple[int, int]] = {
    "Progressive Level Cap": (810000, 10),
    "Instance Unlock: Ragefire Chasm": (810001, 1),
    "Instance Unlock: Deadmines": (810002, 1),
    "Dark Portal Access": (810003, 1),
    "Northrend Passage": (810004, 1),
}

# level -> AP location id
LEVEL_LOCATIONS: dict[int, int] = {
    5: 710000, 10: 710001, 15: 710002, 20: 710003,
    25: 710004, 30: 710005, 35: 710006, 40: 710007,
    45: 710008, 50: 710009, 55: 710010, 60: 710011,
}

# instance key -> AP location id
INSTANCE_CLEAR_LOCATIONS: dict[str, int] = {
    "ragefire_chasm": 720000,
    "deadmines": 720001,
}
