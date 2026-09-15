"""M5.6.1: Day/night cycle resolution -- not an M5.0 MutationCategory (no
world-DB row backs the client's day/night clock; see design spec Sec4 and
this plan's Global Constraints). Resolved once at generation time into a
plain dict, written into the mutation-data file's own new top-level
"day_night" key by mutation_output.py -- read at boot by APWorldState.cpp,
independent of the category apply/restore machinery entirely."""
from __future__ import annotations


def resolve_day_night(world) -> dict:
    mode = world.options.environment_randomizer_day_night_mode.current_key
    speed_percent = float(world.options.environment_randomizer_day_night_speed_percent.value)
    return {"mode": mode, "speed_percent": speed_percent}
