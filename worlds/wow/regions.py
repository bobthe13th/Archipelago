# Archipelago/worlds/wow/regions.py
from BaseClasses import Region
from .locations import create_locations


def create_regions(world):
    menu = Region("Menu", world.player, world.multiworld)
    northshire = Region("Northshire", world.player, world.multiworld)

    northshire.locations += create_locations(world, northshire)

    menu.connect(northshire)

    world.multiworld.regions += [menu, northshire]
