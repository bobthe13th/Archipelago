# Archipelago/worlds/wow/locations.py
from BaseClasses import Location
from .content_data import LOCATIONS
from . import core_loop_content_data


class WoWLocation(Location):
    game = "World of Warcraft WotLK"


def create_locations(world, region) -> list:
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in LOCATIONS.items()
    ]


def create_core_loop_locations(world, region) -> list:
    # KNOWN ACCEPTED LIMITATION (M2.1): Death Knight characters on this
    # server start at level 55 via Player::Create, a path that does not
    # dispatch the C++ level-up hook (Player::GiveLevel) which drives these
    # location checks. That means the 11 "Reach Level N" checks for N in
    # 5..55 can never fire for a Death Knight -- only "Reach Level 60" is
    # reachable for that class (DK does level up normally, via GiveLevel,
    # from 55 to 60). This is a real in-game reachability gap, but it is
    # NOT visible to Archipelago's logic layer: rules.py attaches no access
    # rule to these locations (or any WoW location), Sprint mode has no
    # notion of character class as state, and there is no per-class option
    # in M2.1's options.py, so every location here is modeled as
    # unconditionally reachable and generation will not fail or warn about
    # it. The Sprint win condition itself only requires collecting all 10
    # "Progressive Level Cap" copies (see rules.py), not checking any
    # specific location, so the goal remains reachable for every class in
    # the logic model. The residual risk is purely experiential: if a
    # Progressive Level Cap copy is filled into one of the 11 DK-unreachable
    # milestone locations, a real Death Knight player could not obtain that
    # copy in actual gameplay. Modeling player class as generation-time
    # state (e.g. an option that excludes low-level milestones for DK
    # slots) is out of scope here -- it's deferred alongside the other
    # per-class/per-mode work called out in options.py's GameMode docstring.
    locations = []
    for level, location_id in core_loop_content_data.LEVEL_LOCATIONS.items():
        locations.append(WoWLocation(world.player, f"Reach Level {level}", location_id, region))
    for instance_key, location_id in core_loop_content_data.INSTANCE_CLEAR_LOCATIONS.items():
        name = "Clear Ragefire Chasm" if instance_key == "ragefire_chasm" else "Clear Deadmines"
        locations.append(WoWLocation(world.player, name, location_id, region))
    return locations
