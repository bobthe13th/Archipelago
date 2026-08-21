# Archipelago/worlds/wow/regions.py
from BaseClasses import Region
from .locations import create_locations, create_core_loop_locations, create_filler_locations, create_rares_locations, create_fish_locations


def create_regions(world):
    # M2.1's core-loop content (level-ups, instance clears) is added to the
    # existing Northshire region rather than a region of its own -- these
    # checks aren't tied to a specific reachable place the way quest
    # locations are. A real region graph (which zones/instances are
    # reachable at which level) is exactly the kind of thing the M3
    # content-table compiler should derive, not something to hand-build here.
    menu = Region("Menu", world.player, world.multiworld)
    northshire = Region("Northshire", world.player, world.multiworld)

    northshire.locations += create_locations(world, northshire)
    northshire.locations += create_core_loop_locations(world, northshire)
    # Must run before create_filler_locations/create_items -- it stashes the
    # sampled rare count on `world` for items.py's create_key_hunt_item_pool
    # to read later (see create_rares_locations' own comment for why).
    northshire.locations += create_rares_locations(world, northshire)
    northshire.locations += create_fish_locations(world, northshire)
    northshire.locations += create_filler_locations(world, northshire)

    menu.connect(northshire)

    world.multiworld.regions += [menu, northshire]
