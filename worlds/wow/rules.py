# Archipelago/worlds/wow/rules.py
import math

from . import core_loop_content_data
from . import enemysanity_content_data
from . import fish_content_data
from . import quest_rewards_content_data
from . import world_state
from . import zone_leveler_content_data


def _set_rules_gathersanity_progression(world) -> None:
    """M4.11.4.2 Task 4: gate every Gathersanity "zone_pool_credit"-kind
    location (Task 2's real "<zone>|<profession>|<tier>" composite zone_key)
    on enough copies of the matching Progressive Mining/Herbalism item for
    its own tier -- exactly the same state.has(name, world.player, count)
    shape core_loop's own Progressive Level Cap rule above already
    establishes. No-ops cleanly (zero iterations do anything) against
    gathersanity_content_data.TRIGGERS before Task 5 regenerates it with
    real zone_pool_credit rows, since `if trigger.get("kind") !=
    "zone_pool_credit"` skips every real entry that exists today.

    M4.11.4.2 fix round 1 (real generation-time crash found by review):
    iterates the real locations THIS generation actually created
    (world.multiworld.get_locations), matching each one into TRIGGERS by
    name -- the same safe idiom the Enemysanity and Quest Rewards blocks
    above already use -- rather than iterating TRIGGERS' own full,
    unfiltered dict and assuming every zone_pool_credit row has a matching
    location. Once Task 5 populates real zone_pool_credit rows, tag/pool
    filtering, zone_leveler zone matching, etc. can and will exclude some
    rows from any given generation; world.get_location(name) would
    KeyError for those if TRIGGERS were iterated directly instead,
    crashing generation."""
    from . import gathersanity_content_data
    from .items import GATHERING_SKILL_TIERS
    for loc in world.multiworld.get_locations(world.player):
        trigger = gathersanity_content_data.TRIGGERS.get(loc.name)
        if trigger is None or trigger.get("kind") != "zone_pool_credit":
            continue
        parts = trigger.get("zone_key", "").split("|")
        if len(parts) != 3:
            continue  # a Containersanity-shaped bare zone_key never reaches this family's own TRIGGERS
        _zone, profession, tier = parts
        if tier not in GATHERING_SKILL_TIERS:
            continue
        tier_index = GATHERING_SKILL_TIERS.index(tier) + 1
        item_name = "Progressive Mining" if profession == "mining" else "Progressive Herbalism"
        world.set_rule(
            loc,
            lambda state, item_name=item_name, count=tier_index: state.has(item_name, world.player, count),
        )


# M2: all 19 Northshire/Goldshire locations are always accessible (no
# prerequisite logic yet -- matches the real quest line's actual structure,
# where these are early low-level quests with no hard level/item gates).
# Real access-rule logic (level gates, prerequisite quests, region gating
# for later zones) is deferred to M3 when the content pool grows beyond a
# single starting zone.
#
# M2.1 (final-review fix): the 12 level-milestone and 2 instance-clear
# locations must NOT be left unconditionally accessible -- the real C++
# server enforces genuine prerequisites (you can't gain XP past your
# current level cap without already holding enough Progressive Level Cap
# items; you can't enter Ragefire Chasm/Deadmines without already holding
# the matching Instance Unlock item). Leaving these locations rule-free let
# the fill algorithm place a required Progressive Level Cap copy on a
# milestone location that itself required already having that copy,
# producing permanently unwinnable seeds. M4.9: the separate Death Knight
# reachability gap this comment used to describe as "still accepted" is
# now resolved via a two-track split -- see locations.py's
# create_core_loop_locations for the real mechanism and its own trust-model
# caveat.
def set_rules(world):
    step = core_loop_content_data.LEVEL_CAP_STEP
    # M4.9: the M2.1-era Death Knight "safety collapse" (every level < 55
    # location required the SAME copy count as level 55, so a required
    # Progressive Level Cap copy could never land somewhere DK-unreachable)
    # is retired, superseded by locations.py's own two-track split
    # (core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK["standard"] vs
    # ["death_knight"]). A death_knight_slot=True slot now only ever
    # creates the death_knight track's 55-80 locations to begin with, so
    # there is no longer any DK-unreachable "Reach Level N" location in the
    # pool for that slot to collapse away -- every location (on whichever
    # track this slot actually created) can use its own natural per-level
    # threshold.
    # M4.11.1 (Task 9): zone_leveler resolves to its own
    # f"zone_leveler_{zone_key}" track instead of the shared
    # standard/death_knight pair -- extends the same track-resolution shape
    # Task 3 set up, gated on game_mode instead of death_knight_slot,
    # matching locations.py's create_core_loop_locations split exactly.
    # Finding 10 (final whole-branch review, 2026-09-01): this resolution
    # used to be duplicated independently here, items.py, and locations.py
    # -- now shared via resolve_core_loop_track
    # (zone_leveler_content_data.py).
    track, _zone_key = zone_leveler_content_data.resolve_core_loop_track(world)
    # M4.11.1 (Task 3): starting_cap is now per-track (STARTING_LEVEL_CAP_BY_TRACK)
    # instead of a single flat STARTING_LEVEL_CAP -- both current tracks share
    # the same value (10) today, but Zone Leveler's own track (Task 9) tops
    # out at 30 with a different starting cap, so this can no longer be a
    # bare module-level constant.
    starting_cap = core_loop_content_data.STARTING_LEVEL_CAP_BY_TRACK[track]
    for level, _location_id in core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK[track].items():
        copies_needed = max(0, math.ceil((level - starting_cap) / step))
        name = core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK[track][level]
        location = world.get_location(name)
        if copies_needed > 0:
            world.set_rule(
                location,
                lambda state, count=copies_needed: state.has(
                    "Progressive Level Cap", world.player, count
                ),
            )

    # M4.11.1 (Task 9): Ragefire Chasm/Deadmines are NOT among Zone
    # Leveler's own curated instance-clear locations (only Wailing
    # Caverns/Razorfen Kraul/Razorfen Downs are, for the Barrens zone --
    # see locations.py's create_core_loop_locations zone_leveler branch), so
    # a zone_leveler slot never has these two locations in its pool at all;
    # world.get_location would KeyError for that slot, same idiom as the
    # fishing_quest gate below.
    if world.options.game_mode != "zone_leveler":
        world.set_rule(
            world.get_location("Clear Ragefire Chasm"),
            lambda state: state.has("Instance Unlock: Ragefire Chasm", world.player),
        )
        world.set_rule(
            world.get_location("Clear Deadmines"),
            lambda state: state.has("Instance Unlock: Deadmines", world.player),
        )
    world.set_rule(
        world.get_location("Clear Wailing Caverns"),
        lambda state: state.has("Instance Unlock: Wailing Caverns", world.player),
    )
    world.set_rule(
        world.get_location("Clear Razorfen Kraul"),
        lambda state: state.has("Instance Unlock: Razorfen Kraul", world.player),
    )
    world.set_rule(
        world.get_location("Clear Razorfen Downs"),
        lambda state: state.has("Instance Unlock: Razorfen Downs", world.player),
    )

    # Task 26 (Fishing Quest, spec Sec5.4): "fish-catch locations inherit
    # normal regional access logic -- a Northrend-only fish requires
    # Northrend Passage in logic". Only meaningful when game_mode is
    # fishing_quest, since that's the only time fish.yaml's locations exist
    # in the pool at all (create_fish_locations' own game_mode check) --
    # world.get_location would KeyError for any other mode.
    if world.options.game_mode == "fishing_quest":
        for name in fish_content_data.NORTHREND_LOCATION_NAMES:
            world.set_rule(
                world.get_location(name),
                lambda state: state.has("Northrend Passage", world.player),
            )

    # M4.12: Enemysanity's per-species kill locations must gate reachability
    # on the same real expansion-zone-access items every other
    # expansion-locked piece of content in this project already requires --
    # a species tagged wotlk-only genuinely cannot be killed without first
    # reaching Northrend, the same real constraint Fishing Quest's Northrend
    # catches already enforce two blocks above. No level-based gate is added
    # here (contrast Quest Rewards' min_level clamp just below) -- unlike
    # accepting a quest, killing a creature has no real hard
    # character-level mechanic blocking it, so a level requirement would be
    # an artificial constraint, not a real one. Reads
    # world_state.species_expansion_tags(world), the M4.12 Pipeline A/B
    # interface -- if Pipeline B (M5) ever mutates a species' real zone
    # placement, it writes its own tags there and this loop needs zero
    # changes.
    species_tags = world_state.species_expansion_tags(world)
    for loc in world.multiworld.get_locations(world.player):
        if loc.name not in enemysanity_content_data.LOCATIONS:
            continue
        creature_entry = enemysanity_content_data.TRIGGERS[loc.name]["creature_entry"]
        expansions = species_tags.get(creature_entry, frozenset({"vanilla"}))
        if "vanilla" in expansions:
            continue  # always reachable, no gate needed
        gate_items = tuple(
            item for tag, item in (("tbc", "Dark Portal Access"), ("wotlk", "Northrend Passage"))
            if tag in expansions
        )
        world.set_rule(
            loc,
            lambda state, items=gate_items: any(state.has(item, world.player) for item in items),
        )

    # M4.5 Task 6 (Quest Rewards), M4.8.0: unconditional -- include_quest_rewards
    # was removed in favor of tag/weight filtering (options.py, locations.py),
    # and this loop's own per-location `continue` guards already no-op
    # correctly when zero quest_rewards locations exist in the pool (weight
    # 0, or every tag dimension narrowed to nothing), so there's no longer a
    # single toggle to gate this on. Also now covers the 19 locations
    # migrated from the retired `quests` family (always_present, M4.8.0)
    # with zero extra code -- they're ordinary quest_rewards rows with real
    # DB-derived min_level values, so this exact clamp applies to them the
    # same as every other quest_reward.
    # M4.11.1 (Task 3): total_caps now comes from LEVEL_CAP_TOTAL_BY_TRACK
    # (per-track pooled total) instead of the flat ITEMS["Progressive Level
    # Cap"][1] count -- this clamp stays anchored to whichever track the
    # connected slot uses (including zone_leveler_<zone_key>, resolved above),
    # reusing the same starting_cap/step/track locals already computed above.
    # Comment correction (final whole-branch review M6, 2026-09-01; function
    # name updated by the M4.11.3 milestone final review, Minor #5): a
    # zone_leveler slot DOES create quest_rewards locations -- the ~103 real
    # Barrens-tagged quest_rewards rows for zone_leveler_barrens. M4.11.3.3
    # Task 2's generic _zone_leveler_row_matches (locations.py, which
    # collapsed and replaced the old per-family filter stack including
    # _zone_leveler_quest_reward_zone_matches) zone-filters the 19
    # always-present rows; none match Barrens. This clamp genuinely applies
    # to Zone Leveler's quest rewards too, not only standard/death_knight's.
    total_caps = core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK[track]
    for loc in world.multiworld.get_locations(world.player):
        if not loc.name.startswith("Quest:") or loc.name not in quest_rewards_content_data.LOCATIONS:
            continue
        trigger = quest_rewards_content_data.TRIGGERS[loc.name]
        copies_needed = min(total_caps, max(0, math.ceil((trigger["min_level"] - starting_cap) / step)))
        if copies_needed > 0:
            world.set_rule(
                loc,
                lambda state, count=copies_needed: state.has("Progressive Level Cap", world.player, count),
            )

    # M4.11.4.2 (Task 4): Gathersanity's own zone+tier abstract
    # (zone_pool_credit) locations, gated on Progressive Mining/Herbalism --
    # see the function's own docstring for why this stays a clean no-op
    # until Task 5 regenerates real zone_pool_credit TRIGGERS rows.
    _set_rules_gathersanity_progression(world)
