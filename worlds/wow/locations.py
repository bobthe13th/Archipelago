# Archipelago/worlds/wow/locations.py
from dataclasses import dataclass
from typing import Optional

from BaseClasses import Location
from . import achievements_content_data
from . import collections_content_data
from . import containersanity_content_data
from . import core_loop_content_data
from . import craftsanity_content_data
from . import density
from . import enemysanity_content_data
from . import filler_content_data
from . import fish_content_data
from . import game_mode_profile
from . import gathersanity_content_data
from . import golden_boar_statues_content_data
from . import itemsanity_content_data
from . import professions_content_data
from . import quest_rewards_content_data
from . import rares_content_data
from . import recipes_content_data
from . import repsanity_content_data
from . import trainer_spells_content_data
from . import vendor_stock_content_data
from . import zone_leveler_content_data
from .items import (
    core_loop_item_surplus,
    count_enabled_gates_items,
    count_enabled_holidaysanity_items,
    count_enabled_trap_items,
)


class WoWLocation(Location):
    game = "World of Warcraft WotLK"


@dataclass
class OptionalCategory:
    """One entry per DB-derived optional-location family available in EVERY
    game mode. M4.9: weight_option becomes Optional -- None means this
    category has NO check_density/weight sampling stage at all (Learned
    Recipes, Trainer Spells & Abilities): every tag-matching row is
    included unconditionally, per spec. A str value keeps the M4.8
    tag-filter-then-weight-sample behavior (Quest Rewards, Vendor
    Inventories)."""
    key: str
    tag_options: dict[str, str]      # tag dimension -> WoWOptions OptionSet field name
    locations_module: object         # exposes .LOCATIONS/.TAGS/.ALWAYS_PRESENT
    items_module: Optional[object]   # exposes .ITEMS: dict[str, tuple[int, int]]; None if items live elsewhere
    weight_option: Optional[str] = None  # WoWOptions Range field name, or None -- see class docstring


_OPTIONAL_CATEGORIES: list[OptionalCategory] = []

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="quest_rewards",
    tag_options={"type": "quest_reward_type_pools", "expansion": "quest_reward_expansion_pools"},
    weight_option="quest_reward_weight",
    locations_module=quest_rewards_content_data,
    items_module=quest_rewards_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="vendor_stock",
    tag_options={"expansion": "vendor_stock_expansion_pools"},
    weight_option="vendor_stock_weight",
    locations_module=vendor_stock_content_data,
    items_module=vendor_stock_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="recipes",
    tag_options={"profession": "recipe_profession_pools", "expansion": "recipe_expansion_pools"},
    locations_module=recipes_content_data,
    items_module=recipes_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="trainer_spells",
    tag_options={"class": "trainer_spell_class_pools", "expansion": "trainer_spell_expansion_pools"},
    locations_module=trainer_spells_content_data,
    items_module=trainer_spells_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="containersanity",
    tag_options={"expansion": "containersanity_expansion_pools"},
    locations_module=containersanity_content_data,
    items_module=containersanity_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="gathersanity",
    tag_options={"expansion": "gathersanity_expansion_pools", "source": "gathersanity_source_pools"},
    locations_module=gathersanity_content_data,
    items_module=gathersanity_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="enemysanity",
    tag_options={"type": "enemysanity_type_pools", "expansion": "enemysanity_expansion_pools"},
    locations_module=enemysanity_content_data,
    items_module=None,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="repsanity",
    tag_options={"expansion": "repsanity_expansion_pools", "rank_tier": "repsanity_rank_tier_pools"},
    locations_module=repsanity_content_data,
    items_module=None,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="craftsanity",
    tag_options={"profession": "craftsanity_profession_pools", "class": "craftsanity_class_pools", "expansion": "craftsanity_expansion_pools"},
    locations_module=craftsanity_content_data,
    items_module=craftsanity_content_data,
))

_OPTIONAL_CATEGORIES.append(OptionalCategory(
    key="itemsanity",
    tag_options={
        "class": "itemsanity_class_pools",
        "quality": "itemsanity_quality_pools",
        "expansion": "itemsanity_expansion_pools",
    },
    locations_module=itemsanity_content_data,
    items_module=itemsanity_content_data,
))


def _location_matches_pools(world, category: OptionalCategory, name: str) -> bool:
    """AND across dimensions, OR within a dimension's own selected values
    (spec §2). A category with zero tag_options entries (none exist as of
    M4.8.0, but the loop below degrades correctly to "always matches" if
    one ever does) still requires locations_module.TAGS[name] to resolve --
    every export_tags family unconditionally emits a TAGS entry per
    location (Task 1), so this never KeyErrors for a real family.
    M4.10.5: craftsanity has items with either 'profession' or 'class' tags
    but not both -- if a location's tags dict lacks a dimension entirely,
    that dimension doesn't apply to this location, so it's skipped (treated
    as an automatic pass), not defaulted to an empty set (which would
    always fail regardless of player selection)."""
    tags = category.locations_module.TAGS[name]
    for dimension, option_name in category.tag_options.items():
        if dimension not in tags:
            continue
        selected = getattr(world.options, option_name).value
        if not (tags[dimension] & selected):
            return False
    return True


def create_optional_category_locations(world, region) -> list:
    created = []
    profile = game_mode_profile.get_profile(world.options.game_mode.value)
    force_all = profile.force_all_categories
    if force_all and not hasattr(world, "optional_category_sampled_names"):
        world.optional_category_sampled_names = set()
    check_density = game_mode_profile.effective_check_density(world)

    for category in _OPTIONAL_CATEGORIES:
        all_rows = list(category.locations_module.LOCATIONS.items())
        item_rows = list(category.items_module.ITEMS.items()) if category.items_module is not None else None
        row_index_by_location_name = (
            {name: i for i, (name, _) in enumerate(all_rows)} if item_rows is not None else None
        )

        def _stash(name: str) -> None:
            # 100%'s stash needs ITEM names, not location names -- see the
            # prior version of this comment (unchanged reasoning, M4.6/M4.7).
            if force_all and item_rows is not None:
                item_name = item_rows[row_index_by_location_name[name]][0]
                world.optional_category_sampled_names.add(item_name)

        # always_present locations (M4.8's exemption mechanism, spec §2a):
        # bypass BOTH the tag-filter stage AND the density/weight sample
        # entirely -- unconditionally created regardless of is_category_eligible,
        # tag selection, or weight, since this project's DK-reachability
        # guarantee (rules.py) depends on these being present no matter what
        # a player selects for this category.
        always_present_names = getattr(category.locations_module, "ALWAYS_PRESENT", frozenset())
        for name, location_id in all_rows:
            if name in always_present_names:
                created.append(WoWLocation(world.player, name, location_id, region))
                _stash(name)

        if not game_mode_profile.is_category_eligible(world, category):
            continue

        candidates = [
            (name, location_id) for name, location_id in all_rows
            if name not in always_present_names and (force_all or _location_matches_pools(world, category, name))
        ]
        if category.weight_option is None:
            # M4.9: no check_density/weight sampling stage at all for this
            # category -- every tag-matched candidate is included
            # unconditionally, regardless of force_all/check_density.
            sampled = candidates
        else:
            category_weight = 100 if force_all else getattr(world.options, category.weight_option).value
            sampled = density.sample_category(check_density, category_weight, candidates, world.random)
        for name, location_id in sampled:
            created.append(WoWLocation(world.player, name, location_id, region))
            _stash(name)
    return created


def create_core_loop_locations(world, region) -> list:
    # M4.9: every-level granularity (was every 5th level) with a real
    # per-class track split, replacing the M2.1 "KNOWN ACCEPTED
    # LIMITATION" this function used to document here. Death Knight
    # characters on this server still start at level 55 via Player::Create,
    # a path that does not dispatch the C++ level-up hook
    # (Player::GiveLevel) the sub-55 "Reach Level N" locations depend on --
    # but going to every-level granularity would have grown that gap
    # roughly 5x (11 unreachable locations -> ~54) if the content stayed a
    # single universal track. Instead, core_loop.yaml now defines TWO
    # tracks (LEVEL_LOCATIONS_BY_TRACK in core_loop_content_data.py,
    # mirroring INSTANCES_BY_EXPANSION's grouping precedent): "standard"
    # (every class except Death Knight, levels 1-80) and "death_knight"
    # (Death Knight only, levels 55-80, matching the class's real starting
    # level). death_knight_slot (options.py) is this world's own
    # generation-time signal for which track to instantiate -- a
    # DK-flagged slot gets ONLY the death_knight track's locations, so
    # there is no longer any DK-unreachable "Reach Level N" location in the
    # pool at all for that slot. This is a trust model, not a runtime
    # guarantee: nothing enforces that a death_knight_slot=True player
    # actually plays a Death Knight in-game (or vice versa) -- see
    # death_knight_slot's own options.py docstring for why that's an
    # accepted, documented limitation identical in shape to
    # starting_choice/combo_unlocks_scope's existing "honor your own
    # option" trust model, not a new kind of gap.
    # M4.11.1 (Task 9): zone_leveler is a third, distinct track family --
    # unlike standard/death_knight (which both draw from the SAME
    # INSTANCE_CLEAR_LOCATIONS, every one of core_loop's 8 instances), a
    # zone_leveler slot only ever creates the SELECTED zone's own curated
    # instance-clear locations (Barrens' own 3, not all 8), per
    # zone_leveler_content_data.ZONES[zone_key].instance_keys. This mirrors
    # the standard/death_knight split's own "one exclusive content set per
    # slot" shape, just gated on game_mode instead of death_knight_slot.
    if world.options.game_mode == "zone_leveler":
        zone_key = world.options.zone_leveler_starting_zone.current_key
        track = f"zone_leveler_{zone_key}"
        locations = []
        for level, location_id in core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK[track].items():
            name = core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK[track][level]
            locations.append(WoWLocation(world.player, name, location_id, region))
        zone_data = zone_leveler_content_data.ZONES[zone_key]
        for instance_key in zone_data.instance_keys:
            location_id = core_loop_content_data.INSTANCE_CLEAR_LOCATIONS[instance_key]
            name = core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES[instance_key]
            locations.append(WoWLocation(world.player, name, location_id, region))
        return locations

    is_dk_slot = bool(world.options.death_knight_slot)
    track = "death_knight" if is_dk_slot else "standard"
    locations = []
    for level, location_id in core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK[track].items():
        name = core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK[track][level]
        locations.append(WoWLocation(world.player, name, location_id, region))
    for instance_key, location_id in core_loop_content_data.INSTANCE_CLEAR_LOCATIONS.items():
        name = core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES[instance_key]
        locations.append(WoWLocation(world.player, name, location_id, region))
    return locations


def create_filler_locations(world, region) -> list:
    # Sink locations restoring item=location parity after Group 1's gate
    # items (Task 11), Group 3's trap items (Task 17), and M4.10.7's
    # Holidaysanity items: none of these three families has an AP location
    # of its own, so exactly one filler location is needed per gate-,
    # trap-, or holidaysanity-item copy pooled for this generation's
    # options. Must match items.py's create_gates_item_pool +
    # create_trap_item_pool + create_holidaysanity_item_pool count exactly,
    # not a fixed worst-case number -- AP's generation pipeline has
    # no generic step that pads a short itempool to match location count, so
    # every option combination needs true 1:1 parity, not just locations >=
    # items (confirmed empirically: distribute_items_restrictive raises
    # "Unable to fill all locations" when locations exceed items, the same
    # as it raises when items exceed locations). This runs during
    # create_regions, before create_items runs create_gates_item_pool/
    # create_trap_item_pool/create_holidaysanity_item_pool (see gen_steps
    # ordering) -- all sides derive their counts from the same options each
    # pool function reads, which is what keeps them from drifting apart
    # despite running at different pipeline stages.
    #
    # M4.11.1 (Task 3): core_loop_item_surplus adds a 4th term -- a
    # death_knight_slot generation's own core-loop item count (80, flat
    # and track-independent since LEVEL_CAP_STEP dropped to 1) now exceeds
    # its own 34-location core-loop floor by 46, a real surplus with no
    # family of its own to live in (the standard track's own 88-location
    # floor still absorbs its 80 items with room to spare, so this term is
    # always 0 there). Same "no AP location of its own" sink-location role
    # as the three terms above, just for an item surplus rather than a
    # whole optional family. (M4.11.1 Task 4, BarrensBeater, grew both the
    # item count and both tracks' core-loop floors by 3 in lockstep --
    # 77->80 items, 31->34 death_knight floor, 85->88 standard floor -- so
    # the surplus itself is unchanged at 46/0.)
    needed = (
        count_enabled_gates_items(world)
        + count_enabled_trap_items(world)
        + count_enabled_holidaysanity_items(world)
        + core_loop_item_surplus(world)
    )
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
    # module anywhere in this codebase (density.sample_category, weight 100)
    # -- per this task's own Interfaces note, rares are sampled like any
    # other optional category, not hand-picked per generation. (As of M4.6,
    # every category -- including this one -- samples independently at its
    # own weight/density; there is no shared cross-category ceiling to
    # compete for.)
    #
    # The sampled COUNT (not the specific rows) is stashed on `world` so
    # items.py's create_key_hunt_item_pool, which runs later during
    # create_items, pools EXACTLY this many "Key Hunt: Key" copies --
    # re-sampling independently there (like count_enabled_gates_items/
    # count_enabled_trap_items do, which are pure functions of options alone)
    # is not possible here without double-consuming world.random and
    # risking a different result.
    world.key_hunt_sampled_rare_count = 0
    if world.options.game_mode != "key_hunt":
        return []

    # M4.11.1 Task 5: key_hunt_zone_pools ANDs against density sampling (M4.8
    # §2 tag-dimension convention) -- a row is a candidate only if its own
    # `zone` tag intersects the player's selection; the unrestricted default
    # (every zone this checkout's 40 curated rares span) makes this identical
    # to Key Hunt's pre-M4.11.1 unfiltered behavior.
    selected_zones = world.options.key_hunt_zone_pools.value
    all_rows = [
        (name, location_id) for name, location_id in rares_content_data.LOCATIONS.items()
        if rares_content_data.TAGS[name].get("zone", frozenset()) & selected_zones
    ]
    sampled = density.sample_category(
        game_mode_profile.effective_check_density(world), category_weight=100, all_rows=all_rows, rng=world.random,
    )
    world.key_hunt_sampled_rare_count = len(sampled)
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in sampled
    ]


def create_golden_boar_statues_locations(world, region) -> list:
    # M4.11.1 Task 10 (Zone Leveler's Barrens flagship, golden_boar_statues
    # goal): structurally identical to create_rares_locations above --
    # game_mode-gated (zone_leveler here, key_hunt there) AND, unlike rares,
    # ALSO gated on whether golden_boar_statues is one of the selected
    # zone_leveler_goals (a slot can play Zone Leveler with this specific
    # goal deselected, in which case the family contributes zero locations/
    # items, same "N goals ANDed together" shape ZoneLevelerGoals'
    # docstring describes). Density-sampled the same way (density.sample_category,
    # weight 100) -- no zone-tag filter needed here, unlike Key Hunt's
    # key_hunt_zone_pools, since every one of this family's 20 rows is
    # already Barrens-only by curation (golden_boar_statues.yaml has no
    # `tags:` block at all).
    #
    # The sampled COUNT (not the specific rows) is stashed on `world` so
    # items.py's create_golden_boar_statues_item_pool, which runs later
    # during create_items, pools EXACTLY this many "Golden Boar Statue"
    # copies -- same world.<family>_sampled_count convention
    # world.key_hunt_sampled_rare_count established above.
    world.golden_boar_statues_sampled_count = 0
    if world.options.game_mode != "zone_leveler":
        return []
    if "golden_boar_statues" not in world.options.zone_leveler_goals.value:
        return []

    all_rows = list(golden_boar_statues_content_data.LOCATIONS.items())
    sampled = density.sample_category(
        game_mode_profile.effective_check_density(world), category_weight=100, all_rows=all_rows, rng=world.random,
    )
    world.golden_boar_statues_sampled_count = len(sampled)
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


def create_achievement_locations(world, region) -> list:
    # Achievement Hunt (M4.9 Sec4): every achievement in the compiled
    # 1,162-row pool always exists as a location whenever game_mode is
    # achievement_hunt, regardless of achievement_hunt_tier/subset -- NOT
    # filtered at generation time. Only the completion RULE (goals.py's
    # _achievement_hunt_target_item_names) differs by chosen tier/subset,
    # mirroring Collector's own "every location exists, only the threshold
    # differs" shape. Not density-sampled either, same "gated on game_mode
    # itself" family as professions/collections/fish.
    if world.options.game_mode != "achievement_hunt":
        return []
    return [
        WoWLocation(world.player, name, location_id, region)
        for name, location_id in achievements_content_data.LOCATIONS.items()
    ]


def create_explorer_locations(world, region) -> list:
    # Explorer (M4.9 Sec4): a single location, the real World Explorer
    # achievement (id 46) -- reuses the SAME compiled achievements.yaml
    # table Achievement Hunt draws from (both key off the shared
    # OnPlayerAchievementComplete hook per the spec), gated to just this
    # one row rather than the full pool.
    if world.options.game_mode != "explorer":
        return []
    name = achievements_content_data.WORLD_EXPLORER_LOCATION_NAME
    location_id = achievements_content_data.LOCATIONS[name]
    return [WoWLocation(world.player, name, location_id, region)]
