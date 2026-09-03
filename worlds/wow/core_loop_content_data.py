# GENERATED FILE - do not edit by hand.
# Regenerate with: python modules/archipelago_wow/tools/generate_content.py content/core_loop.yaml


LEVEL_CAP_STEP = 1
SPRINT_GOAL_LEVEL = 60

ITEMS: dict[str, tuple[int, int]] = {
    "Progressive Level Cap": (810000, 70),
    "Instance Unlock: Ragefire Chasm": (810001, 1),
    "Instance Unlock: Deadmines": (810002, 1),
    "Dark Portal Access": (810003, 1),
    "Northrend Passage": (810004, 1),
    "Instance Unlock: Molten Core": (810005, 1),
    "Instance Unlock: Sunwell Plateau": (810006, 1),
    "Instance Unlock: Icecrown Citadel": (810007, 1),
    "Instance Unlock: Wailing Caverns": (810008, 1),
    "Instance Unlock: Razorfen Kraul": (810009, 1),
    "Instance Unlock: Razorfen Downs": (810010, 1),
}

# Every item whose delivery is realm_state/unlock_instance, keyed by its
# own AP item id -- a generic map so a new instance_clear row's unlock item
# needs zero additional C++/Python code to actually unlock anything (found
# the hard way in Task 23: the 3 new raid unlock items were added to this
# content table but never wired into ArchipelagoPlayerScript.cpp's delivery
# dispatch, since that dispatch hardcoded only the original 2 dungeons'
# item ids -- receiving those items did nothing at all in real play until
# this generic map replaced the hardcoded blocks).
INSTANCE_UNLOCK_ITEM_TO_KEY: dict[int, str] = {
    810001: "ragefire_chasm",
    810002: "deadmines",
    810005: "molten_core",
    810006: "sunwell",
    810007: "icecrown_citadel",
    810008: "wailing_caverns",
    810009: "razorfen_kraul",
    810010: "razorfen_downs",
}

LEVEL_LOCATIONS_BY_TRACK: dict[str, dict[int, int]] = {
    "standard": {1: 710001, 2: 710002, 3: 710003, 4: 710004, 5: 710005, 6: 710006, 7: 710007, 8: 710008, 9: 710009, 10: 710010, 11: 710011, 12: 710012, 13: 710013, 14: 710014, 15: 710015, 16: 710016, 17: 710017, 18: 710018, 19: 710019, 20: 710020, 21: 710021, 22: 710022, 23: 710023, 24: 710024, 25: 710025, 26: 710026, 27: 710027, 28: 710028, 29: 710029, 30: 710030, 31: 710031, 32: 710032, 33: 710033, 34: 710034, 35: 710035, 36: 710036, 37: 710037, 38: 710038, 39: 710039, 40: 710040, 41: 710041, 42: 710042, 43: 710043, 44: 710044, 45: 710045, 46: 710046, 47: 710047, 48: 710048, 49: 710049, 50: 710050, 51: 710051, 52: 710052, 53: 710053, 54: 710054, 55: 710055, 56: 710056, 57: 710057, 58: 710058, 59: 710059, 60: 710060, 61: 710061, 62: 710062, 63: 710063, 64: 710064, 65: 710065, 66: 710066, 67: 710067, 68: 710068, 69: 710069, 70: 710070, 71: 710071, 72: 710072, 73: 710073, 74: 710074, 75: 710075, 76: 710076, 77: 710077, 78: 710078, 79: 710079, 80: 710080},
    "zone_leveler_barrens": {11: 712011, 12: 712012, 13: 712013, 14: 712014, 15: 712015, 16: 712016, 17: 712017, 18: 712018, 19: 712019, 20: 712020, 21: 712021, 22: 712022, 23: 712023, 24: 712024, 25: 712025, 26: 712026, 27: 712027, 28: 712028, 29: 712029, 30: 712030},
    "death_knight": {55: 711055, 56: 711056, 57: 711057, 58: 711058, 59: 711059, 60: 711060, 61: 711061, 62: 711062, 63: 711063, 64: 711064, 65: 711065, 66: 711066, 67: 711067, 68: 711068, 69: 711069, 70: 711070, 71: 711071, 72: 711072, 73: 711073, 74: 711074, 75: 711075, 76: 711076, 77: 711077, 78: 711078, 79: 711079, 80: 711080},
}

# M4.11.1 (Task 3): per-track starting Progressive Level Cap value, read
# directly from core_loop.yaml's level_cap_tracks: block -- NOT derived from
# a track's own lowest level_milestone level, since standard/death_knight both
# emit 'Reach Level N' locations below their real starting cap too (free,
# no-item-required checks), so the lowest milestone level in a track does not
# reliably equal starting_cap + 1.
STARTING_LEVEL_CAP_BY_TRACK: dict[str, int] = {
    "standard": 10,
    "zone_leveler_barrens": 10,
    "death_knight": 10,
}

# M4.11.1 (Task 3): pooled Progressive Level Cap copy count needed to reach
# a track's own level-milestone ceiling from its starting cap, at
# LEVEL_CAP_STEP == 1 (total = ceiling - starting_cap, the step==1
# simplification of ceil((ceiling - starting_cap) / LEVEL_CAP_STEP)).
LEVEL_CAP_TOTAL_BY_TRACK: dict[str, int] = {
    "standard": 70,
    "zone_leveler_barrens": 20,
    "death_knight": 70,
}

# M4.9: name for each (track, level) pair, generated directly from each
# location row's own `name` field -- same anti-hardcoded-ternary discipline
# as INSTANCE_CLEAR_LOCATION_NAMES below (Task 23 bugfix), so locations.py/
# rules.py never need to hand-format a track-specific name suffix themselves.
LEVEL_LOCATION_NAMES_BY_TRACK: dict[str, dict[int, str]] = {
    "standard": {1: "Reach Level 1", 2: "Reach Level 2", 3: "Reach Level 3", 4: "Reach Level 4", 5: "Reach Level 5", 6: "Reach Level 6", 7: "Reach Level 7", 8: "Reach Level 8", 9: "Reach Level 9", 10: "Reach Level 10", 11: "Reach Level 11", 12: "Reach Level 12", 13: "Reach Level 13", 14: "Reach Level 14", 15: "Reach Level 15", 16: "Reach Level 16", 17: "Reach Level 17", 18: "Reach Level 18", 19: "Reach Level 19", 20: "Reach Level 20", 21: "Reach Level 21", 22: "Reach Level 22", 23: "Reach Level 23", 24: "Reach Level 24", 25: "Reach Level 25", 26: "Reach Level 26", 27: "Reach Level 27", 28: "Reach Level 28", 29: "Reach Level 29", 30: "Reach Level 30", 31: "Reach Level 31", 32: "Reach Level 32", 33: "Reach Level 33", 34: "Reach Level 34", 35: "Reach Level 35", 36: "Reach Level 36", 37: "Reach Level 37", 38: "Reach Level 38", 39: "Reach Level 39", 40: "Reach Level 40", 41: "Reach Level 41", 42: "Reach Level 42", 43: "Reach Level 43", 44: "Reach Level 44", 45: "Reach Level 45", 46: "Reach Level 46", 47: "Reach Level 47", 48: "Reach Level 48", 49: "Reach Level 49", 50: "Reach Level 50", 51: "Reach Level 51", 52: "Reach Level 52", 53: "Reach Level 53", 54: "Reach Level 54", 55: "Reach Level 55", 56: "Reach Level 56", 57: "Reach Level 57", 58: "Reach Level 58", 59: "Reach Level 59", 60: "Reach Level 60", 61: "Reach Level 61", 62: "Reach Level 62", 63: "Reach Level 63", 64: "Reach Level 64", 65: "Reach Level 65", 66: "Reach Level 66", 67: "Reach Level 67", 68: "Reach Level 68", 69: "Reach Level 69", 70: "Reach Level 70", 71: "Reach Level 71", 72: "Reach Level 72", 73: "Reach Level 73", 74: "Reach Level 74", 75: "Reach Level 75", 76: "Reach Level 76", 77: "Reach Level 77", 78: "Reach Level 78", 79: "Reach Level 79", 80: "Reach Level 80"},
    "zone_leveler_barrens": {11: "Reach Level 11 (Zone Leveler)", 12: "Reach Level 12 (Zone Leveler)", 13: "Reach Level 13 (Zone Leveler)", 14: "Reach Level 14 (Zone Leveler)", 15: "Reach Level 15 (Zone Leveler)", 16: "Reach Level 16 (Zone Leveler)", 17: "Reach Level 17 (Zone Leveler)", 18: "Reach Level 18 (Zone Leveler)", 19: "Reach Level 19 (Zone Leveler)", 20: "Reach Level 20 (Zone Leveler)", 21: "Reach Level 21 (Zone Leveler)", 22: "Reach Level 22 (Zone Leveler)", 23: "Reach Level 23 (Zone Leveler)", 24: "Reach Level 24 (Zone Leveler)", 25: "Reach Level 25 (Zone Leveler)", 26: "Reach Level 26 (Zone Leveler)", 27: "Reach Level 27 (Zone Leveler)", 28: "Reach Level 28 (Zone Leveler)", 29: "Reach Level 29 (Zone Leveler)", 30: "Reach Level 30 (Zone Leveler)"},
    "death_knight": {55: "Reach Level 55 (Death Knight)", 56: "Reach Level 56 (Death Knight)", 57: "Reach Level 57 (Death Knight)", 58: "Reach Level 58 (Death Knight)", 59: "Reach Level 59 (Death Knight)", 60: "Reach Level 60 (Death Knight)", 61: "Reach Level 61 (Death Knight)", 62: "Reach Level 62 (Death Knight)", 63: "Reach Level 63 (Death Knight)", 64: "Reach Level 64 (Death Knight)", 65: "Reach Level 65 (Death Knight)", 66: "Reach Level 66 (Death Knight)", 67: "Reach Level 67 (Death Knight)", 68: "Reach Level 68 (Death Knight)", 69: "Reach Level 69 (Death Knight)", 70: "Reach Level 70 (Death Knight)", 71: "Reach Level 71 (Death Knight)", 72: "Reach Level 72 (Death Knight)", 73: "Reach Level 73 (Death Knight)", 74: "Reach Level 74 (Death Knight)", 75: "Reach Level 75 (Death Knight)", 76: "Reach Level 76 (Death Knight)", 77: "Reach Level 77 (Death Knight)", 78: "Reach Level 78 (Death Knight)", 79: "Reach Level 79 (Death Knight)", 80: "Reach Level 80 (Death Knight)"},
}

# Final whole-branch review fix (Important #1, M4.11.3 milestone final
# review): this key was hand-curated as "sunwell_plateau" in an earlier
# milestone (M4.11.1), but M4.11.3.2's instance_entrance_data.py --
# computed directly from real Map.dbc data -- names the same real instance
# "sunwell" (map id 580's own real DBC slug, no suffix embellishment). The
# other 2 instances this same milestone added (wailing_caverns,
# razorfen_kraul, razorfen_downs) already matched their own real Map.dbc
# slugs exactly, confirming "sunwell_plateau" was the one outlier, not the
# convention. Renamed to "sunwell" here (and everywhere else this file and
# goals.py use it as an internal instance_key) so
# zone_leveler_content_data.curated_instance_keys' plain `in` membership
# check against instance_entrance_data.INSTANCE_ENTRANCE_AREA_TAGS stops
# silently missing this instance. The player-facing "Clear Sunwell
# Plateau"/"Instance Unlock: Sunwell Plateau" name strings are UNCHANGED --
# only this internal dict key moved. Regenerating this GENERATED FILE from
# its real core_loop.yaml source (out of scope here -- lives under the
# azerothcore-wotlk submodule) should preserve this same "sunwell" key;
# if a future regeneration reintroduces "sunwell_plateau", the
# module-load-time guard in zone_leveler_content_data.py will raise loudly.
INSTANCE_CLEAR_LOCATIONS: dict[str, int] = {
    "ragefire_chasm": 720000,
    "deadmines": 720001,
    "wailing_caverns": 720005,
    "razorfen_kraul": 720006,
    "razorfen_downs": 720007,
    "molten_core": 720002,
    "sunwell": 720003,
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
    "wailing_caverns": "Clear Wailing Caverns",
    "razorfen_kraul": "Clear Razorfen Kraul",
    "razorfen_downs": "Clear Razorfen Downs",
    "molten_core": "Clear Molten Core",
    "sunwell": "Clear Sunwell Plateau",
    "icecrown_citadel": "Clear Icecrown Citadel",
}

# Task 23: only instances whose YAML row carries a `bosses:` sub-list
# appear here -- Ragefire Chasm/Deadmines (no bosses: list) are absent,
# not present with a single-entry list. Not consumed by the apworld as
# of Task 23 (no rules.py/goals.py logic needs per-boss creature ids),
# emitted for parity with the C++ side per this task's own Files list.
INSTANCE_BOSS_ENTRIES: dict[str, list[int]] = {
    "molten_core": [12118, 11982, 12259, 12057, 12264, 12056, 12098, 11988, 12018, 11502],
    "sunwell": [24892, 24882, 25038, 25165, 25166, 25840, 25315],
    "icecrown_citadel": [36612, 36855, 37813, 36626, 36627, 36678, 37972, 37973, 37970, 37955, 36853, 36597],
}

# Task 24 (Completionist mode): every instance_key with an `expansion:`
# field on its location row, grouped by that expansion. A row with no
# `expansion:` field (none exist as of Task 24, but the loader's schema
# still treats it as optional -- see core_loop.yaml's own header comment)
# is simply absent from every list here, not present under a None/empty key.
INSTANCES_BY_EXPANSION: dict[str, list[str]] = {
    "vanilla": ["ragefire_chasm", "deadmines", "wailing_caverns", "razorfen_kraul", "razorfen_downs", "molten_core"],
    "tbc": ["sunwell"],
    "wotlk": ["icecrown_citadel"],
}
