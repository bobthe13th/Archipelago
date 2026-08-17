# GENERATED FILE - do not edit by hand.
# Regenerate with: python modules/archipelago_wow/tools/generate_content.py content/core_loop.yaml


STARTING_LEVEL_CAP = 10
LEVEL_CAP_STEP = 5
SPRINT_GOAL_LEVEL = 60

ITEMS: dict[str, tuple[int, int]] = {
    "Progressive Level Cap": (810000, 10),
    "Instance Unlock: Ragefire Chasm": (810001, 1),
    "Instance Unlock: Deadmines": (810002, 1),
    "Dark Portal Access": (810003, 1),
    "Northrend Passage": (810004, 1),
}

LEVEL_LOCATIONS: dict[int, int] = {
    5: 710000,
    10: 710001,
    15: 710002,
    20: 710003,
    25: 710004,
    30: 710005,
    35: 710006,
    40: 710007,
    45: 710008,
    50: 710009,
    55: 710010,
    60: 710011,
}

INSTANCE_CLEAR_LOCATIONS: dict[str, int] = {
    "ragefire_chasm": 720000,
    "deadmines": 720001,
}
