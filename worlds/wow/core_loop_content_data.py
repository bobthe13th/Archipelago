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
    "Instance Unlock: Molten Core": (810005, 1),
    "Instance Unlock: Sunwell Plateau": (810006, 1),
    "Instance Unlock: Icecrown Citadel": (810007, 1),
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
    "molten_core": 720002,
    "sunwell_plateau": 720003,
    "icecrown_citadel": 720004,
}

# Task 23 bugfix: locations.py's create_core_loop_locations previously
# hardcoded a 2-way name ternary over INSTANCE_CLEAR_LOCATIONS' keys --
# adding this family's 3rd+ instance_key broke it (every non-Ragefire key
# collided on the literal string "Clear Deadmines", a real duplicate-
# location crash caught by this task's own apworld test run). This map,
# generated directly from each location row's own `name` field, replaces
# that ternary generically for any future instance_clear row.
INSTANCE_CLEAR_LOCATION_NAMES: dict[str, str] = {
    "ragefire_chasm": "Clear Ragefire Chasm",
    "deadmines": "Clear Deadmines",
    "molten_core": "Clear Molten Core",
    "sunwell_plateau": "Clear Sunwell Plateau",
    "icecrown_citadel": "Clear Icecrown Citadel",
}

# Task 23: only instances whose YAML row carries a `bosses:` sub-list
# appear here -- Ragefire Chasm/Deadmines (no bosses: list) are absent,
# not present with a single-entry list. Not consumed by the apworld as
# of Task 23 (no rules.py/goals.py logic needs per-boss creature ids),
# emitted for parity with the C++ side per this task's own Files list.
INSTANCE_BOSS_ENTRIES: dict[str, list[int]] = {
    "molten_core": [12118, 11982, 12259, 12057, 12264, 12056, 12098, 11988, 12018, 11502],
    "sunwell_plateau": [24892, 24882, 25038, 25165, 25166, 25840, 25315],
    "icecrown_citadel": [36612, 36855, 37813, 36626, 36627, 36678, 37972, 37973, 37970, 37955, 36853, 36597],
}
