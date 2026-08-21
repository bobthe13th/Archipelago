# Archipelago/worlds/wow/locations.py
from BaseClasses import Location
from .content_data import LOCATIONS
from . import collections_content_data
from . import core_loop_content_data
from . import density
from . import filler_content_data
from . import fish_content_data
from . import professions_content_data
from . import rares_content_data
from .items import count_enabled_gates_items, count_enabled_trap_items


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
        name = core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES[instance_key]
        locations.append(WoWLocation(world.player, name, location_id, region))
    return locations


def create_filler_locations(world, region) -> list:
    # Sink locations restoring item=location parity after Group 1's gate
    # items (Task 11) and Group 3's trap items (Task 17): neither family has
    # an AP location of its own, so exactly one filler location is needed
    # per gate-or-trap item copy pooled for this generation's options. Must
    # match items.py's create_gates_item_pool + create_trap_item_pool count
    # exactly, not a fixed worst-case number -- AP's generation pipeline has
    # no generic step that pads a short itempool to match location count, so
    # every option combination needs true 1:1 parity, not just locations >=
    # items (confirmed empirically: distribute_items_restrictive raises
    # "Unable to fill all locations" when locations exceed items, the same
    # as it raises when items exceed locations). This runs during
    # create_regions, before create_items runs create_gates_item_pool/
    # create_trap_item_pool (see gen_steps ordering) -- all sides derive
    # their counts from the same options each pool function reads, which is
    # what keeps them from drifting apart despite running at different
    # pipeline stages.
    needed = count_enabled_gates_items(world) + count_enabled_trap_items(world)
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in list(filler_content_data.LOCATIONS.items())[:needed]
    ]


def create_rares_locations(world, region) -> list:
    # Task 25 (Key Hunt, Tier 2): the FIRST content family whose existence is
    # gated on which game_mode is active, not an independent toggle option --
    # rares.yaml's 40 curated rows only become real locations when game_mode
    # is key_hunt, matching items.py's create_key_hunt_item_pool's identical
    # game_mode check. Also the first real caller of Task 2's density.py
    # module anywhere in this codebase (density.sample_category, weight 100
    # since Key Hunt has no other optional category competing for the shared
    # budget) -- per this task's own Interfaces note, rares are sampled like
    # any other optional category, not hand-picked per generation.
    #
    # The sampled COUNT (not the specific rows) is stashed on `world` so
    # items.py's create_key_hunt_item_pool, which runs later during
    # create_items, pools EXACTLY this many "Key Hunt: Key" copies --
    # re-sampling independently there (like count_enabled_gates_items/
    # count_enabled_trap_items do, which are pure functions of options alone)
    # is not possible here without double-consuming world.random and risking
    # a different length if the shared DensityBudget's state ever depends on
    # a second concurrently-sampled category in a later task.
    world.key_hunt_sampled_rare_count = 0
    if world.options.game_mode != "key_hunt":
        return []

    budget = density.DensityBudget(
        check_density=world.options.check_density.value,
        hard_ceiling=world.options.max_optional_locations.value,
    )
    all_rows = list(rares_content_data.LOCATIONS.items())
    sampled = density.sample_category(budget, category_weight=100, all_rows=all_rows, rng=world.random)
    world.key_hunt_sampled_rare_count = len(sampled)
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in sampled
    ]


def create_fish_locations(world, region) -> list:
    # Task 26 (Fishing Quest): all 46 curated fish-catch locations are
    # created unconditionally whenever game_mode is fishing_quest -- NOT
    # density-sampled, unlike Key Hunt's rares (spec Sec5.4: "the set is
    # bounded and discrete... sampling it would break the completion
    # condition"). Same game_mode-gated-family shape rares.yaml established.
    if world.options.game_mode != "fishing_quest":
        return []
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in fish_content_data.LOCATIONS.items()
    ]


def create_professions_locations(world, region) -> list:
    # Task 27 (Artisan): all 84 profession skill-milestone locations are
    # created unconditionally whenever game_mode is artisan -- NOT
    # density-sampled when this mode is active, same "gated on game_mode
    # itself" shape as create_fish_locations. (professions.yaml's full
    # roster becoming eligible for sample_category as an optional category
    # in OTHER modes is a real cross-mode integration Task 27's own Step 3
    # note anticipates, but is out of scope for landing Artisan mode itself
    # -- no other mode's item pool references this family.)
    if world.options.game_mode != "artisan":
        return []
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in professions_content_data.LOCATIONS.items()
    ]


def create_collections_locations(world, region) -> list:
    # Task 27 (Collector): all 264 "learn this mount/pet" locations are
    # created unconditionally whenever game_mode is collector -- NOT
    # density-sampled, same "gated on game_mode itself" shape as
    # create_fish_locations/create_professions_locations. Unlike Artisan's
    # completion (needs every location), Collector's completion rule only
    # needs collector_items_required of the matching ITEMS to be received,
    # but every location still exists so any of the 264 can drop a check.
    if world.options.game_mode != "collector":
        return []
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in collections_content_data.LOCATIONS.items()
    ]
