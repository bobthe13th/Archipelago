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


# M4.11.1 Task 12: possession-triggered categories -- these fire on
# pickup/craft/learn (item_first_held, recipe_craft, reputation_rank,
# learn_spell trigger kinds) regardless of the player's physical zone.
# Quest Rewards/instance clears are, unlike these 4, real physically
# zone-bound families (a real quest-giver NPC/instance entrance somewhere
# specific), so their own restriction is unconditional whenever game_mode
# is zone_leveler rather than gated by zone_leveler_content_scope the way
# these 4 are -- see _zone_leveler_quest_reward_zone_matches and
# _zone_leveler_scope_matches below for the actual filtering behavior.
# Only relevant when game_mode is zone_leveler.
# M4.11.2: Repsanity was originally in this set but is now handled by its
# own dedicated _zone_leveler_repsanity_matches function with expansion-tag
# filtering, so it's been removed from here -- the early-return branch in
# _zone_leveler_scope_matches intercepts it before this set is consulted.
_POSSESSION_TRIGGERED_CATEGORY_KEYS = frozenset({
    "itemsanity", "craftsanity", "recipes", "trainer_spells",
})


def _zone_leveler_possession_family_min_level(name: str, category: OptionalCategory) -> int | None:
    """The real, DB-sourced level requirement for one possession-triggered
    row, if this family tracks one at all (M4.11.1 Task 12). Read from
    TRIGGERS[name]["min_level"], NOT TAGS -- TAGS is exported as
    dict[str, frozenset[str]] (generate_content.py's export_tags emission,
    string-only, meant for OR-within-dimension pool selection), which can't
    hold a numeric value; TRIGGERS keeps the raw `trigger` sub-dict verbatim
    (repr()'d as-is), the same real placement extract_quest_rewards.py's own
    min_level/zone_id keys already established and locations.py has read
    from since M4.7.1.3/M4.11.1 Task 2.

    Real per-family sourcing (only 3 of the 4 possession-triggered families
    actually carry this key):
      - itemsanity: item_template.RequiredLevel (extract_itemsanity.py).
      - trainer_spells: MIN(trainer_spell.ReqLevel) across every class
        trainer that teaches the spell (extract_trainer_spells.py).
      - recipes: item_template.RequiredLevel of the recipe ITEM that teaches
        the spell (extract_recipes.py) -- distinct from RequiredSkillRank,
        which drives this family's own expansion tag instead.
      - craftsanity: NOT tractable with real data -- crafting requirements
        are skill-tier-gated (skill_line_ability-style), and no official,
        real 1:1 skill-tier-to-player-level mapping exists in this game's
        actual data. Fabricating an approximate mapping would violate this
        project's "real DB column, cited, not guessed" discipline.
      - repsanity: NOT tractable -- reputation ranks are not level-gated by
        design; there is no real per-row level-requirement concept for this
        family at all.
    Craftsanity/repsanity's own TRIGGERS dicts simply never gain a
    "min_level" key, so this returns None for them like any other row
    missing the key -- see _zone_leveler_scope_matches for how that
    naturally excludes both families under whole_game_scaled."""
    return category.locations_module.TRIGGERS[name].get("min_level")


def _zone_leveler_quest_reward_zone_matches(world, name: str) -> bool:
    """M4.11.1 Task 12 fix (post-hoc defect found after the task was
    originally closed): Quest Rewards is a REAL, physically zone-bound
    family -- each row is tied to a real quest-giver NPC standing
    somewhere specific in the world -- but nothing about the zone_leveler
    lock mechanism (a C++ PlayerScript hook that stops the PLAYER from
    walking outside the selected zone) actually restricts which Quest
    Rewards LOCATIONS get sampled into the check pool at generation time.
    Without this filter, a Barrens slot could sample a quest whose
    real-world quest-giver stands in, say, Redridge Mountains: AP's own
    logic considers that location reachable once its min_level is
    satisfied (there's no equivalent of Dark Portal Access/Northrend
    Passage gating same-continent vanilla travel), but the player is
    physically locked to Barrens and can never actually walk there to
    trigger it -- a real unreachable-location bug, not a cosmetic
    "too many items" one.

    Unlike the 5 possession-triggered families in
    _POSSESSION_TRIGGERED_CATEGORY_KEYS (which fire on pickup/craft/learn
    regardless of physical zone, and whose inclusion is governed by
    zone_leveler_content_scope), Quest Rewards' restriction here is
    UNCONDITIONAL whenever game_mode is zone_leveler -- it applies the
    same way under both zone_only and whole_game_scaled, since the toggle
    only ever widens/narrows the possession-triggered families, and Quest
    Rewards was never one of them.

    M4.11.2: extended to also accept the selected zone's own curated
    allowed_hub_zone_ids, but ONLY when zone_leveler_allow_hub_zone is on
    -- if the toggle is off, the in-bounds set stays zone-only, matching
    the physical zone-lock's own real enforcement (a player can't walk to
    Orgrimmar if the toggle hasn't opened that path). Per the design spec's
    own §1: this same "selected zone OR allowed hub zones (when the toggle
    is on)" rule applies uniformly to every zone-bound family as its own
    real data lands, not just Quest Rewards.

    A row only matches if its own real TRIGGERS[name]["zone_id"] equals
    the selected zone's own real zone_id (quest_rewards_content_data.py,
    DB-extracted by extract_quest_rewards.py). zone_id == 0 is this data's
    own "unresolvable, real zone unknown" sentinel (~2,210 of ~9,208 rows
    game-wide) -- since no real zone has zone_id 0, such a row can never
    equal a real zone's zone_id and is naturally excluded here, matching
    this project's "unknown zone means excluded, not included" default
    for a physically zone-locked game mode."""
    zone_key = world.options.zone_leveler_starting_zone.current_key
    zone_data = zone_leveler_content_data.ZONES[zone_key]
    row_zone_id = quest_rewards_content_data.TRIGGERS[name].get("zone_id")
    in_bounds_zone_ids = {zone_data.zone_id}
    if getattr(world.options, "zone_leveler_allow_hub_zone", False):
        in_bounds_zone_ids |= zone_data.allowed_hub_zone_ids
    return row_zone_id in in_bounds_zone_ids


def _zone_leveler_repsanity_matches(world, name: str) -> bool:
    """M4.11.2: Repsanity has no real per-row player-level requirement
    (M4.11.1 Task 12's own confirmed finding -- reputation ranks aren't
    level-gated by design) and no physical location either (reputation
    gain isn't tied to a place, unlike a quest-giver/trainer/chest) -- so
    it's exempt from the ZONE axis entirely (same as core_loop's level
    milestones), but it DOES get a LEVEL-axis proxy: Barrens' whole 10-30
    band is squarely vanilla-era content, so a tbc/wotlk reputation
    faction (Argent Crusade, Netherwing, ...) isn't realistically
    farmable by a Barrens-locked, Azeroth-only character regardless of any
    literal rank-based gate. Reuses Repsanity's own real, already-shipped
    `expansion` tag (M4.10.4) as this proxy -- no new DB extraction
    needed. Applies unconditionally under zone_leveler (both
    zone_only/whole_game_scaled) -- this is NOT the possession-triggered
    min_level mechanism (Repsanity was never in
    _POSSESSION_TRIGGERED_CATEGORY_KEYS and doesn't join it here either),
    it's a separate, always-on restriction specific to this one family."""
    expansion_tags = repsanity_content_data.TAGS[name].get("expansion", frozenset())
    return "vanilla" in expansion_tags


def _zone_leveler_trainer_spell_zone_matches(world, name: str) -> bool:
    """M4.11.2: Trainer Spells are learned from a real, physical trainer
    NPC -- unlike Recipes (a mailable item), there's no way to learn a
    trainer-taught spell without physically visiting a trainer. Confirmed
    this session (re-running extract_trainer_spells.py's own real position-
    resolution query against the live DB): 417 of 427 real level-10-30
    Trainer Spells have at least one teaching trainer in Orgrimmar or
    Durotar (this project's own WorldMapArea.dbc position-resolution
    mechanism, extract_trainer_spells.py's trainer_zone_ids). A row is
    in-bounds if trainer_zone_ids intersects the selected zone's own
    {zone_id} | allowed_hub_zone_ids (only including the hub zones when
    zone_leveler_allow_hub_zone is on, same rule as
    _zone_leveler_quest_reward_zone_matches). This is ADDITIVE to the
    family's own existing min_level check
    (_zone_leveler_scope_matches's possession-triggered path) -- a row
    must satisfy BOTH axes."""
    zone_key = world.options.zone_leveler_starting_zone.current_key
    zone_data = zone_leveler_content_data.ZONES[zone_key]
    trainer_zone_ids = set(trainer_spells_content_data.TRIGGERS[name].get("trainer_zone_ids", []))
    in_bounds_zone_ids = {zone_data.zone_id}
    if getattr(world.options, "zone_leveler_allow_hub_zone", False):
        in_bounds_zone_ids |= zone_data.allowed_hub_zone_ids
    return bool(trainer_zone_ids & in_bounds_zone_ids)


def _zone_leveler_scope_matches(world, category: OptionalCategory, name: str) -> bool:
    """Only called when game_mode is zone_leveler (M4.11.1 Task 12; Quest
    Rewards restriction added by Task 12's own post-hoc fix round).

    Quest Rewards (category.key == "quest_rewards") is handled first and
    separately, via _zone_leveler_quest_reward_zone_matches above -- it's a
    real, physically zone-bound family (a real quest-giver NPC), unlike the
    5 possession-triggered families below, so it is restricted to the
    selected zone's own real zone_id UNCONDITIONALLY (both zone_only and
    whole_game_scaled), not gated by zone_leveler_content_scope at all.

    Every other category outside _POSSESSION_TRIGGERED_CATEGORY_KEYS always
    matches here (True unconditionally) -- instance clears are inherently
    zone-bound already via a different mechanism (rules.py/
    zone_leveler_content_data's own instance_keys), so this generic path
    doesn't touch them; other optional categories not curated with zone
    data at all (containersanity, gathersanity, enemysanity, vendor_stock,
    ...) are simply not scoped by content_scope -- that's M4.11.2's
    full-breadth follow-up, not this task.

    zone_only (default): every possession-triggered row is excluded
    entirely, since these families fire on pickup/craft/learn regardless of
    physical zone and their own real zone-of-origin isn't tagged yet
    (M4.11.2).

    whole_game_scaled: a possession-triggered row is included if its own
    real level requirement falls inside the selected zone's level band.
    Craftsanity and Repsanity have NO real min_level data at all (by design,
    not an oversight -- see _zone_leveler_possession_family_min_level's own
    docstring), so _zone_leveler_possession_family_min_level always returns
    None for their rows and they fall through the `min_level is None` branch
    below -- identical, excluded, behavior to zone_only for those two
    families specifically, same as it is for every other family's rows that
    happen to carry no real min_level (there are none among the 3 tractable
    families, since every DB row has a real, if sometimes 0, RequiredLevel/
    ReqLevel)."""
    if category.key == "quest_rewards":
        return _zone_leveler_quest_reward_zone_matches(world, name)
    if category.key == "repsanity":
        return _zone_leveler_repsanity_matches(world, name)
    if category.key not in _POSSESSION_TRIGGERED_CATEGORY_KEYS:
        return True
    if world.options.zone_leveler_content_scope == "zone_only":
        return False
    # M4.11.2: Trainer Spells additionally needs its own real zone check --
    # a spell taught only by a trainer outside Barrens/allowed hub zones is
    # never physically learnable, regardless of whole_game_scaled's own
    # level-band widening (which only ever governs ITEM/recipe VARIETY for
    # the other 4 possession-triggered families, not physical reachability
    # for this one -- Trainer Spells is the one possession-triggered family
    # that IS also physically zone-bound, per the design spec's own §4).
    if category.key == "trainer_spells" and not _zone_leveler_trainer_spell_zone_matches(world, name):
        return False
    zone_key = world.options.zone_leveler_starting_zone.current_key
    zone_data = zone_leveler_content_data.ZONES[zone_key]
    min_level = _zone_leveler_possession_family_min_level(name, category)
    if min_level is None:
        return False
    return zone_data.min_level <= min_level <= zone_data.max_level


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
            if name not in always_present_names:
                continue
            # M4.11.2: Quest Rewards' 19 ALWAYS_PRESENT starting-quest rows
            # (Northshire/Goldshire, M4.8.0) previously bypassed EVERY filter this
            # category has (tag pools, content_scope) -- confirmed and explicitly
            # flagged as a known gap by M4.11.1 Task 12's own hotfix report. For
            # zone_leveler specifically, apply the same zone-or-hub-zone
            # restriction every other quest_rewards row already gets; every other
            # mode's ALWAYS_PRESENT semantics are completely unaffected (the
            # `category.key == "quest_rewards"` check below only ever fires when
            # game_mode is zone_leveler in the first place, via
            # _zone_leveler_quest_reward_zone_matches's own real logic).
            if (
                world.options.game_mode == "zone_leveler"
                and category.key == "quest_rewards"
                and not _zone_leveler_quest_reward_zone_matches(world, name)
            ):
                continue
            created.append(WoWLocation(world.player, name, location_id, region))
            _stash(name)

        if not game_mode_profile.is_category_eligible(world, category):
            continue

        candidates = [
            (name, location_id) for name, location_id in all_rows
            if name not in always_present_names
            and (force_all or _location_matches_pools(world, category, name))
            # M4.11.1 Task 12: zone_leveler's own zone_only/whole_game_scaled
            # content-scope filter, ANDed in alongside tag-pool matching
            # (not bypassed by force_all -- zone_leveler's own
            # GameModeProfile never sets force_all_categories, see
            # game_mode_profile.py, so this never actually interacts with a
            # force_all slot in practice).
            and (world.options.game_mode != "zone_leveler" or _zone_leveler_scope_matches(world, category, name))
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
    # Finding 10 (final whole-branch review, 2026-09-01): track/zone_key
    # resolution used to be duplicated independently here, items.py, and
    # rules.py -- now shared via resolve_core_loop_track
    # (zone_leveler_content_data.py).
    track, zone_key = zone_leveler_content_data.resolve_core_loop_track(world)
    if zone_key is not None:
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
