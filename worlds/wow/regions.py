# Archipelago/worlds/wow/regions.py
from BaseClasses import Region
from .locations import create_core_loop_locations, create_filler_locations, create_rares_locations, create_golden_boar_statues_locations, create_fish_locations, create_professions_locations, create_collections_locations, create_optional_category_locations, create_achievement_locations, create_explorer_locations


def create_regions(world):
    # M2.1's core-loop content (level-ups, instance clears) is added to the
    # existing Northshire region rather than a region of its own -- these
    # checks aren't tied to a specific reachable place the way quest
    # locations are. A real region graph (which zones/instances are
    # reachable at which level) is exactly the kind of thing the M3
    # content-table compiler should derive, not something to hand-build here.
    menu = Region("Menu", world.player, world.multiworld)
    northshire = Region("Northshire", world.player, world.multiworld)

    northshire.locations += create_core_loop_locations(world, northshire)
    # Must run before create_filler_locations/create_items -- it stashes the
    # sampled rare count on `world` for items.py's create_key_hunt_item_pool
    # to read later (see create_rares_locations' own comment for why).
    northshire.locations += create_rares_locations(world, northshire)
    # Same "stash the sampled count on `world` before create_items reads it
    # back" reason as create_rares_locations above -- see
    # create_golden_boar_statues_locations' own comment (locations.py).
    northshire.locations += create_golden_boar_statues_locations(world, northshire)
    northshire.locations += create_fish_locations(world, northshire)
    northshire.locations += create_professions_locations(world, northshire)
    northshire.locations += create_collections_locations(world, northshire)
    northshire.locations += create_achievement_locations(world, northshire)
    northshire.locations += create_explorer_locations(world, northshire)

    # Universal optional-category registry (M4.5 Task 3): available in EVERY
    # game mode, unlike the four families above which are each gated to one
    # owning mode. Empty until a Group 1-4 family task registers into
    # locations._OPTIONAL_CATEGORIES.
    northshire.locations += create_optional_category_locations(world, northshire)

    northshire.locations += create_filler_locations(world, northshire)

    menu.connect(northshire)

    world.multiworld.regions += [menu, northshire]
