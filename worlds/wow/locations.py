# Archipelago/worlds/wow/locations.py
from BaseClasses import Location
from .content_data import LOCATIONS


class WoWLocation(Location):
    game = "World of Warcraft WotLK"


def create_locations(world, region) -> list:
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in LOCATIONS.items()
    ]
