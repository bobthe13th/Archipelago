# Archipelago/worlds/wow/items.py
from BaseClasses import Item, ItemClassification
from . import achievements_content_data
from . import collections_content_data
from . import core_loop_content_data
from . import filler_reward_items_content_data
from . import filler_reward_effects_content_data
from . import fish_content_data
from . import gates_content_data
from . import golden_boar_statues_content_data
from . import holidaysanity_content_data
from . import professions_content_data
from . import rares_content_data
from . import traps_content_data
from . import zone_leveler_content_data


class WoWItem(Item):
    game = "World of Warcraft WotLK"


# M4.9.3.1: maps each real filler_reward_effects `effect` string to its
# player-facing FillerCategoryPools key -- the two vocabularies differ
# slightly (effect="cast_spell" is category="random_buff", etc.) since
# `effect` names the underlying C++ dispatch case (APFillerRewardEffects.cpp)
# while `category` names the player-facing concept (options.py).
_EFFECT_TO_CATEGORY = {
    "cast_spell": "random_buff",
    "grant_money": "gold_reward",
    "grant_xp_percent": "xp_reward",
    "grant_title": "title",
    "portable_service": "portable_service",
}

# Shared per-category cap ("as even as possible" -- design spec's own
# phrasing): every category is sampled down to this count if it has more
# real/curated rows than this; a category with FEWER rows than this
# contributes everything it has (badge_currency: 5, toy: 6) rather than
# being padded or excluded.
FILLER_PER_CATEGORY_CAP = 30


def _core_loop_natural_item_count(track: str) -> int:
    """Total real, unconditional core_loop item copies pooled for `track` --
    Progressive Level Cap's own per-track total
    (core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK, since Finding 10's
    fix below) plus every other core_loop item's flat count (the 10
    Instance Unlock/Dark Portal Access/Northrend Passage items, currently
    identical across every track). Single source of truth for BOTH
    create_core_loop_item_pool's own pool size and core_loop_item_surplus's
    deficit/surplus computation (final whole-branch review Finding 10,
    2026-09-01) -- these two must never be able to drift apart on what
    "how many Progressive Level Cap copies does this track pool" means."""
    level_cap_copies = core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK[track]
    other_items_count = sum(
        count for name, (_item_id, count) in core_loop_content_data.ITEMS.items()
        if name != "Progressive Level Cap"
    )
    return level_cap_copies + other_items_count


def create_core_loop_item_pool(world) -> list:
    # Finding 10 (final whole-branch review, 2026-09-01): Progressive Level
    # Cap used to pool core_loop.yaml's flat, standard/death_knight-sized
    # count (70) for EVERY track, including zone_leveler_barrens -- which
    # only ever needs to walk its level cap from 10 to 30 (20 copies,
    # LEVEL_CAP_TOTAL_BY_TRACK["zone_leveler_barrens"]), not all the way to
    # 80. Pooling 70 let a BarrensBeater realm's level cap walk past its own
    # intended level-30 ceiling, directly undermining the mode's vertical-
    # slice premise. Now resolved per-track via the same
    # resolve_core_loop_track helper items.py/locations.py/rules.py all
    # share (Finding 10 also factored this out -- see
    # zone_leveler_content_data.py).
    track, _zone_key = zone_leveler_content_data.resolve_core_loop_track(world)
    pool = []
    for name, (item_id, count) in core_loop_content_data.ITEMS.items():
        if name == "Progressive Level Cap":
            count = core_loop_content_data.LEVEL_CAP_TOTAL_BY_TRACK[track]
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    # M4.9.3.1: core_loop's every-level granularity (M4.9.3) grew its own
    # location count (88 standard-track / 34 death_knight-track as of
    # M4.11.1 Task 4's 3 new instance clears -- was 85/31) well past
    # its own fixed item count (21) -- pad the pool to close the deficit
    # exactly, the same track-aware sizing _trap_baseline_location_count
    # already established for the trap family's own baseline. (M4.11.1
    # Task 9: now calls that same function directly instead of
    # re-deriving the count inline, so zone_leveler's own much smaller
    # 23-location floor -- and any future track -- only needs to be taught
    # to _trap_baseline_location_count once.)
    location_count = _trap_baseline_location_count(world)
    deficit = location_count - len(pool)
    if deficit > 0:
        pool.extend(create_filler_item_pool(world, deficit))
    return pool


def core_loop_item_surplus(world) -> int:
    """M4.11.1 (Task 3): the mirror image of create_core_loop_item_pool's
    own deficit-padding above. LEVEL_CAP_STEP dropped from 5 to 1, growing
    Progressive Level Cap's pooled copy count from 14 to 70 for the
    standard/death_knight tracks (core_loop.yaml) -- combined with the
    unconditional unlock items (7 at the time, 10 as of M4.11.1 Task 4's 3
    new instance unlocks), core_loop's own natural item count is 80 for the
    standard/death_knight tracks (was 77). The standard track's own 88
    locations (was 85) still exceed that (a deficit, already padded with
    filler above), but the death_knight track's own 34 locations (was 31;
    26 level milestones (55-80) + 8 instance clears, grown from 5 by Task 4)
    do not -- a real 46-item surplus with nowhere of its own family to
    live (unchanged numerically from before Task 4, since both the item
    count and the death_knight floor grew by exactly 3). Used by
    locations.py's create_filler_locations to size its own sink-location
    count, same role
    count_enabled_gates_items/count_enabled_trap_items/
    count_enabled_holidaysanity_items already play for their own families'
    "no AP location of its own" items -- 0 for the standard track (whose
    own deficit already covers it), nonzero only for death_knight.

    Finding 10 correction (final whole-branch review, 2026-09-01): this
    function's natural_item_count is no longer a flat, track-independent
    80 -- it is resolved per-track via _core_loop_natural_item_count (the
    SAME per-track total create_core_loop_item_pool above now pools), so
    zone_leveler_barrens (natural count 30: 20 level-cap copies + 10 flat
    unlock items) can never drift out of sync with what was actually
    pooled for it."""
    track, _zone_key = zone_leveler_content_data.resolve_core_loop_track(world)
    natural_item_count = _core_loop_natural_item_count(track)
    return max(0, natural_item_count - _trap_baseline_location_count(world))


# (name prefix, WoWOptions field name) pairs identifying gates.yaml items
# that belong to an optional gate family -- only pooled when the matching
# toggle is on. Riding and Flight Unlock items match no prefix here, so they
# fall through to the "always pooled" branch below (§5.1 treats them as
# mandatory Pipeline A content, not an optional family).
_OPTIONAL_ITEM_PREFIXES = [
    ("Armor Proficiency:", "proficiency_gating"),
    ("Weapon Proficiency:", "proficiency_gating"),
    ("Auction House Access", "access_gating"),
    ("Hearthstone Access", "access_gating"),
    ("Mailbox Access", "access_gating"),
    ("Bank Access", "access_gating"),
    ("Gathering Access", "access_gating"),
    ("Progressive Bank Bag Slot:", "character_unlock_gating"),
    ("Talent Point Access", "character_unlock_gating"),
    ("Dual Spec Unlock", "character_unlock_gating"),
    ("Progressive Glyph Slot:", "character_unlock_gating"),
]


# M4.10.7 (Holidaysanity): the five holidays whose quest-chain components
# require visiting BOTH a TBC capital (Shattrath) and a Northrend capital
# (Dalaran) -- or, for Lunar Festival specifically, stepping inside
# TBC/Northrend dungeons/raids (design spec §8a's combo_unlocks_scope
# interaction section). Each of the five spec entries names BOTH expansion
# tiers, not just one, so "both" is the correct scope requirement for every
# one of them, not a per-holiday split.
_COMBO_SCOPE_GATED_HOLIDAYS = {
    "Holiday Unlock: Hallow's End",
    "Holiday Unlock: Lunar Festival",
    "Holiday Unlock: Children's Week",
    "Holiday Unlock: Pilgrim's Bounty",
    "Holiday Unlock: Winter Veil",
}


def _is_gate_item_enabled(world, name: str) -> bool:
    # Task 21 (design spec Sec5.5): combo_unlocks_scope is a 4-way Choice
    # (off/tbc/wotlk/both), not a plain Toggle, so it can't go through
    # _OPTIONAL_ITEM_PREFIXES's simple getattr-truthiness check -- that would
    # incorrectly treat BOTH combo items as enabled the moment the option is
    # anything other than "off", even for a seed that only scoped in one of
    # the two. Each combo item checks its own matching scope value(s)
    # directly instead.
    if name == "TBC Combo Unlock":
        return world.options.combo_unlocks_scope in ("tbc", "both")
    if name == "WotLK Combo Unlock":
        return world.options.combo_unlocks_scope in ("wotlk", "both")
    # M4.10.7: five Holidaysanity holiday-unlock items share combo_unlocks_scope's
    # gating too, but only at its "both" value -- each of these five holidays'
    # own quest chain needs BOTH expansion tiers reachable (see
    # _COMBO_SCOPE_GATED_HOLIDAYS's own docstring above), not "tbc" or
    # "wotlk" alone.
    if name in _COMBO_SCOPE_GATED_HOLIDAYS:
        return world.options.combo_unlocks_scope == "both"

    option_name = next((opt for prefix, opt in _OPTIONAL_ITEM_PREFIXES if name.startswith(prefix)), None)
    return option_name is None or bool(getattr(world.options, option_name))


def count_enabled_gates_items(world) -> int:
    """Total gates_content_data item copies that create_gates_item_pool will
    actually pool for this generation's options -- i.e. how many locations
    with no matching AP location of their own (every gates-family item)
    need a filler sink location instead. Used by locations.py to size
    create_filler_locations so item/location parity holds exactly, not just
    in the worst case -- AP's generation pipeline has no generic step that
    tops up a short itempool to match location count (that only happens for
    start_inventory_from_pool item replacement, a fixed-size swap, not
    padding), so every option combination needs len(itempool) ==
    len(locations) to hold by construction, not just <=."""
    return sum(
        count
        for name, (_item_id, count) in gates_content_data.ITEMS.items()
        if _is_gate_item_enabled(world, name)
    )


def create_gates_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in gates_content_data.ITEMS.items():
        if not _is_gate_item_enabled(world, name):
            continue
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool


# M4.10.7 (Holidaysanity): architecturally identical to gates_content_data's
# own items -- no AP location of their own, gated by the same
# _is_gate_item_enabled function (now extended with _COMBO_SCOPE_GATED_HOLIDAYS
# above). Needs the same count_enabled_* counterpart gates/traps already have
# so locations.py's create_filler_locations can size its sink locations to
# exact 1:1 item/location parity (see count_enabled_gates_items's own
# docstring for why this is required, not optional, for every option
# combination).
def count_enabled_holidaysanity_items(world) -> int:
    """Total holidaysanity_content_data item copies that
    create_holidaysanity_item_pool will actually pool for this generation's
    options -- same role as count_enabled_gates_items, for the Holidaysanity
    family."""
    return sum(
        count
        for name, (_item_id, count) in holidaysanity_content_data.ITEMS.items()
        if _is_gate_item_enabled(world, name)
    )


def create_holidaysanity_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in holidaysanity_content_data.ITEMS.items():
        if not _is_gate_item_enabled(world, name):
            continue
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool


# Task 17 (design spec §8): traps are pure filler-classification items with no
# location of their own, exactly like gates-family items -- they need the
# same item=location parity treatment Task 11 established
# (count_enabled_gates_items above), just for a second, independently-sized
# optional family. Kept as its own function rather than folded into
# count_enabled_gates_items because traps have a genuinely different sizing
# model (a percentage-of-baseline-content total, split across eligible trap
# types by trap_distribution_mode) instead of "every enabled item's own
# fixed count".
def _eligible_trap_names(world) -> list[str]:
    lethal_enabled = bool(world.options.lethal_traps_enabled)
    return [
        name
        for name in traps_content_data.ITEMS
        if lethal_enabled or not traps_content_data.LETHAL_BY_ITEM_NAME[name]
    ]


def _trap_baseline_location_count(world) -> int:
    # M4.9: track-aware -- a slot's real core-loop location count now
    # depends on death_knight_slot (locations.py's two-track split), not a
    # single fixed number. Standard track: 80 level milestones + 8 instance
    # clears = 88. Death Knight track: 26 level milestones (55-80) + 8
    # instance clears = 34. (M4.11.1 Task 4, BarrensBeater, grew the
    # instance-clear count from 5 to 8 -- was 85/31.) (M4.8.0's own
    # docstring note about the standalone `quests` family's 19 locations no
    # longer being part of this baseline still applies -- unaffected by
    # this task.)
    #
    # M4.11.1 (Task 9): a zone_leveler slot is a third, much smaller floor
    # -- only its own zone's level-cap track PLUS that zone's own curated
    # instance-clear subset (Barrens: 20 + 3 = 23), not all 8 of
    # core_loop's real instances (locations.py's create_core_loop_locations
    # zone_leveler branch never creates the other 5). getattr (not direct
    # attribute access) since this function is also called directly by
    # test_basic.py's TestFillerPoolCoversWorstCaseGatesTrapsAndHolidaysanity
    # with a bare `types.SimpleNamespace(options=...)` fake world that has
    # no game_mode attribute at all -- that fake world must keep resolving
    # to the standard/death_knight branch exactly as before.
    #
    # Finding 10 (final whole-branch review, 2026-09-01): this branch used
    # to be duplicated independently in locations.py/rules.py too -- now
    # shared via resolve_core_loop_track (zone_leveler_content_data.py),
    # which preserves this exact same getattr safety for the fake-world
    # test case above.
    track, zone_key = zone_leveler_content_data.resolve_core_loop_track(world)
    if zone_key is not None:
        instance_count = len(zone_leveler_content_data.ZONES[zone_key].instance_keys)
    else:
        instance_count = len(core_loop_content_data.INSTANCE_CLEAR_LOCATIONS)
    return (
        len(core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK[track])
        + instance_count
    )


def count_enabled_trap_items(world) -> int:
    """Total trap item copies create_trap_item_pool will actually pool for
    this generation's options -- same role as count_enabled_gates_items
    (Task 11) but for the traps family, sized independently. 0 when
    traps_enabled is off or every eligible trap type has weight 0."""
    if not world.options.traps_enabled:
        return 0
    if not _eligible_trap_names(world):
        return 0
    return max(0, round(_trap_baseline_location_count(world) * world.options.trap_percentage_of_filler / 100))


def _distribute_trap_counts_uniform(eligible: list[str], total: int) -> dict[str, int]:
    counts = {name: 0 for name in eligible}
    for i in range(total):
        counts[eligible[i % len(eligible)]] += 1
    return counts


def _distribute_trap_counts_weighted(eligible: list[str], total: int) -> dict[str, int]:
    # Each trap's own traps.yaml `count` (its content-table ceiling) doubles
    # as its relative weight here -- a trap declared with a higher ceiling is
    # proportionally more likely to be the one sampled. Largest-remainder
    # apportionment so the counts sum to EXACTLY total, not just
    # approximately -- count_enabled_trap_items must be able to predict that
    # exact total from options alone, without re-running this distribution,
    # for locations.py's parity sizing to hold.
    weights = [traps_content_data.ITEMS[name][1] for name in eligible]
    total_weight = sum(weights)
    if total_weight == 0:
        return _distribute_trap_counts_uniform(eligible, total)
    raw = [total * w / total_weight for w in weights]
    counts_list = [int(r) for r in raw]
    remainder = total - sum(counts_list)
    order = sorted(range(len(eligible)), key=lambda i: raw[i] - counts_list[i], reverse=True)
    for i in order[:remainder]:
        counts_list[i] += 1
    return {eligible[i]: counts_list[i] for i in range(len(eligible))}


def _distribute_trap_counts_chaos(world, eligible: list[str], total: int) -> dict[str, int]:
    # "Chaos": each of the total copies independently picks a uniformly
    # random eligible trap type, so the split (unlike uniform/weighted)
    # varies generation to generation even for the same options -- still
    # sums to exactly total by construction, one pick at a time.
    counts = {name: 0 for name in eligible}
    for _ in range(total):
        counts[world.random.choice(eligible)] += 1
    return counts


def _distribute_filler_effect_counts_uniform(eligible: list[str], total: int) -> dict[str, int]:
    counts = {name: 0 for name in eligible}
    for i in range(total):
        counts[eligible[i % len(eligible)]] += 1
    return counts


def _distribute_filler_effect_counts_weighted(eligible: list[str], total: int) -> dict[str, int]:
    # Same largest-remainder apportionment as _distribute_trap_counts_weighted
    # -- every M4.9.6 row currently carries a flat weight of 1 (see this
    # plan's Global Constraints), so weighted and uniform currently agree
    # for real data; this function stays independently correct for a future
    # milestone that assigns differentiated weights (see
    # test_weighted_apportions_proportionally_to_each_rows_own_weight).
    weights = [filler_reward_effects_content_data.ITEMS[name][1] for name in eligible]
    total_weight = sum(weights)
    if total_weight == 0:
        return _distribute_filler_effect_counts_uniform(eligible, total)
    raw = [total * w / total_weight for w in weights]
    counts_list = [int(r) for r in raw]
    remainder = total - sum(counts_list)
    order = sorted(range(len(eligible)), key=lambda i: raw[i] - counts_list[i], reverse=True)
    for i in order[:remainder]:
        counts_list[i] += 1
    return {eligible[i]: counts_list[i] for i in range(len(eligible))}


def _distribute_filler_effect_counts_chaos(world, eligible: list[str], total: int) -> dict[str, int]:
    counts = {name: 0 for name in eligible}
    for _ in range(total):
        counts[world.random.choice(eligible)] += 1
    return counts


def _distribute_filler_effect_counts(world, eligible: list[str], total: int) -> dict[str, int]:
    if world.options.filler_effect_distribution_mode == "weighted":
        return _distribute_filler_effect_counts_weighted(eligible, total)
    elif world.options.filler_effect_distribution_mode == "chaos":
        return _distribute_filler_effect_counts_chaos(world, eligible, total)
    return _distribute_filler_effect_counts_uniform(eligible, total)


def create_trap_item_pool(world) -> list:
    if not world.options.traps_enabled:
        return []
    eligible = _eligible_trap_names(world)
    total = count_enabled_trap_items(world)
    if total == 0 or not eligible:
        return []

    if world.options.trap_distribution_mode == "weighted":
        counts = _distribute_trap_counts_weighted(eligible, total)
    elif world.options.trap_distribution_mode == "chaos":
        counts = _distribute_trap_counts_chaos(world, eligible, total)
    else:
        counts = _distribute_trap_counts_uniform(eligible, total)

    pool = []
    for name, count in counts.items():
        item_id, _ceiling = traps_content_data.ITEMS[name]
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.trap, item_id, world.player))
    return pool


# Task 25 (Key Hunt, Tier 2): "Key Hunt: Key" is only pooled when game_mode
# is key_hunt, and only as many copies as create_rares_locations (locations.py)
# actually sampled -- rares_content_data.ITEMS["Key Hunt: Key"][1] (40) is a
# ceiling/ceiling-only count, like traps_content_data's per-item ceilings, not
# a literal always-pooled count like core_loop's Progressive Level Cap.
def count_enabled_rares_items(world) -> int:
    """Total "Key Hunt: Key" copies create_key_hunt_item_pool will pool for
    this generation -- 0 unless game_mode is key_hunt, in which case it's
    whatever create_rares_locations (locations.py, which runs first during
    create_regions) sampled and stashed on `world`. Named to match
    count_enabled_gates_items/count_enabled_trap_items's shape, but unlike
    those two, this is NOT a pure function of options alone -- it depends on
    create_regions having already run (always true by the time create_items
    runs, in both real generation and the test harness's gen_steps order)."""
    return getattr(world, "key_hunt_sampled_rare_count", 0)


def create_key_hunt_item_pool(world) -> list:
    count = count_enabled_rares_items(world)
    if count == 0:
        return []
    item_id, _ceiling = rares_content_data.ITEMS["Key Hunt: Key"]
    return [WoWItem("Key Hunt: Key", ItemClassification.progression, item_id, world.player) for _ in range(count)]


# M4.11.1 Task 10: "Golden Boar Statue" is only pooled when game_mode is
# zone_leveler AND golden_boar_statues is one of the selected
# zone_leveler_goals, and only as many copies as create_golden_boar_statues_locations
# (locations.py, which runs first during create_regions) actually sampled --
# same shape as count_enabled_rares_items/create_key_hunt_item_pool above.
def count_enabled_golden_boar_statues_items(world) -> int:
    """Total "Golden Boar Statue" copies create_golden_boar_statues_item_pool
    will pool for this generation -- 0 unless game_mode is zone_leveler and
    golden_boar_statues is selected, in which case it's whatever
    create_golden_boar_statues_locations (locations.py) sampled and stashed
    on `world`. Not a pure function of options alone (like
    count_enabled_rares_items above, this depends on create_regions having
    already run -- always true by the time create_items runs)."""
    return getattr(world, "golden_boar_statues_sampled_count", 0)


def create_golden_boar_statues_item_pool(world) -> list:
    count = count_enabled_golden_boar_statues_items(world)
    if count == 0:
        return []
    item_id, _ceiling = golden_boar_statues_content_data.ITEMS["Golden Boar Statue"]
    return [WoWItem("Golden Boar Statue", ItemClassification.progression, item_id, world.player) for _ in range(count)]


# Task 26 (Fishing Quest): all 46 "Fish: <name>" items are pooled
# unconditionally whenever game_mode is fishing_quest, one copy each,
# mirroring create_fish_locations' identical game_mode check and count
# (fish.yaml's locations/items are NOT density-sampled, unlike rares.yaml).
def create_fish_item_pool(world) -> list:
    if world.options.game_mode != "fishing_quest":
        return []
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, (item_id, _count) in fish_content_data.ITEMS.items()
    ]


# Task 27 (Artisan): all 84 "Skill Milestone: <name> <threshold>" items are
# pooled unconditionally whenever game_mode is artisan, one copy each,
# mirroring create_professions_locations' identical game_mode check and
# count (not density-sampled when this mode is itself active).
def create_professions_item_pool(world) -> list:
    if world.options.game_mode != "artisan":
        return []
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, (item_id, _count) in professions_content_data.ITEMS.items()
    ]


# Task 27 (Collector): all 264 "Mount: <name>" / "Pet: <name>" items are
# pooled unconditionally whenever game_mode is collector, one copy each,
# mirroring create_professions_item_pool's identical game_mode check and
# count (not density-sampled). Progression classification for the full
# roster (not just collector_items_required's worth) matches Artisan's own
# precedent -- which specific subset satisfies the threshold isn't fixed
# ahead of time, so every item can potentially be needed for completion.
def create_collections_item_pool(world) -> list:
    if world.options.game_mode != "collector":
        return []
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, (item_id, _count) in collections_content_data.ITEMS.items()
    ]


# M4.9 Sec4 (Achievement Hunt): all 1,162 "Achievement Complete: <name>"
# items are pooled unconditionally whenever game_mode is achievement_hunt,
# one copy each, mirroring create_achievement_locations' identical
# game_mode check and count.
def create_achievements_item_pool(world) -> list:
    if world.options.game_mode != "achievement_hunt":
        return []
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, (item_id, _count) in achievements_content_data.ITEMS.items()
    ]


# M4.9 Sec4 (Explorer): the single "Achievement Complete: World Explorer
# (#46)" item, mirroring create_explorer_locations' identical single-row
# game_mode check.
def create_explorer_item_pool(world) -> list:
    if world.options.game_mode != "explorer":
        return []
    name = achievements_content_data.WORLD_EXPLORER_ITEM_NAME
    item_id, count = achievements_content_data.ITEMS[name]
    return [WoWItem(name, ItemClassification.progression, item_id, world.player) for _ in range(count)]


def create_optional_category_item_pool(world) -> list:
    # Mirrors create_optional_category_locations exactly: for each enabled
    # category, pool one item per location ACTUALLY sampled (not the
    # category's full candidate set) -- reads world's own sampled locations
    # back from world.multiworld.get_locations rather than re-sampling
    # (re-sampling here would consume world.random a second time and could
    # pick a DIFFERENT subset than what create_regions already placed,
    # exactly the bug count_enabled_rares_items' own docstring warns about
    # for Key Hunt).
    #
    # Pairing sampled locations to their reward item by ROW INDEX, not by
    # string-matching the location name against the item name: every
    # existing content family (Task 5's quest_rewards, plus the hand-rolled
    # fish/professions/collections families already in this file) names its
    # LOCATIONS and ITEMS entries with DIFFERENT prefixes for the same
    # underlying row (e.g. quest_rewards_content_data: location
    # "Quest: X Reward (#N)" vs item "Quest Reward: X (#N)" -- confirmed
    # against the real generated file, not assumed). An earlier version of
    # this function matched on `item_name in sampled_location_names`, which
    # is vacuously false for every real family and would silently pool ZERO
    # items for any enabled optional category, corrupting the 1:1 item/
    # location parity test_item_pool_matches_location_count_exactly enforces
    # for every option combination. LOCATIONS and ITEMS dicts are emitted by
    # generate_content.py from the same ordered `locations:`/`items:` YAML
    # lists, row-for-row, so index alignment is a real invariant of the
    # compiler's output, not a name-based assumption -- guarded below so a
    # future Group 2-4 family that breaks this alignment fails generation
    # loudly instead of silently under-pooling.
    #
    # Imported here rather than at module level: locations.py already
    # imports count_enabled_gates_items/count_enabled_trap_items from this
    # module at import time, so a module-level `from .locations import
    # _OPTIONAL_CATEGORIES` here would create a circular import (confirmed:
    # `python -c "import worlds.wow"` fails with "cannot import name
    # 'count_enabled_gates_items' from partially initialized module" when
    # this import is hoisted to the top of the file). Deferring it to call
    # time avoids the cycle since both modules are fully loaded by then.
    from .locations import _OPTIONAL_CATEGORIES

    pool = []
    for category in _OPTIONAL_CATEGORIES:
        # M4.8.0 fix: do NOT gate this loop on is_category_eligible -- unlike
        # the old include_*=False toggle it replaced, an ineligible category
        # can still have real, unconditionally-created locations in the
        # multiworld (always_present rows bypass is_category_eligible
        # entirely in locations.py's create_optional_category_locations).
        # Skipping the category here would silently leave those locations
        # paired with no item at all, breaking the 1:1 item/location parity
        # this function exists to protect. This is safe for the ordinary
        # ineligible case too: sampled_indices below is derived from
        # world.multiworld.get_locations(), so a category with genuinely
        # zero locations present (ineligible AND no always_present rows)
        # naturally yields an empty sampled_indices and pools nothing --
        # the eligibility check was redundant optimization, not a
        # correctness requirement.
        if category.items_module is None:
            # First real consumer: Enemysanity (M4.10.3) has no synthesized/
            # mailed item at all, so there is nothing to pool 1:1 the way
            # every other category's ITEMS dict provides. Left as a bare
            # `continue` (M4.8-era code), this silently contributes ZERO
            # items for this category's sampled locations, corrupting the
            # item/location parity every other family maintains --
            # create_filler_item_pool (M4.9.3.1) is the existing, generic
            # mechanism for exactly this shape of deficit (core_loop's own
            # every-level granularity change already uses it the same way).
            category_location_names = set(category.locations_module.LOCATIONS.keys())
            sampled_count = sum(
                1 for loc in world.multiworld.get_locations(world.player)
                if loc.name in category_location_names
            )
            if sampled_count > 0:
                pool.extend(create_filler_item_pool(world, sampled_count))
            continue
        location_names = list(category.locations_module.LOCATIONS.keys())
        item_rows = list(category.items_module.ITEMS.items())
        if len(location_names) != len(item_rows):
            raise ValueError(
                f"optional category {category.key!r}: LOCATIONS ({len(location_names)} rows) and "
                f"ITEMS ({len(item_rows)} rows) must be the same length and row-index-aligned -- "
                f"see create_optional_category_item_pool's docstring for why this is required."
            )
        index_by_location_name = {name: i for i, name in enumerate(location_names)}
        sampled_indices = {
            index_by_location_name[loc.name]
            for loc in world.multiworld.get_locations(world.player)
            if loc.name in index_by_location_name
        }
        for i in sampled_indices:
            item_name, (item_id, count) = item_rows[i]
            for _ in range(count):
                pool.append(WoWItem(item_name, ItemClassification.progression, item_id, world.player))
    return pool


def create_filler_item_pool(world, count: int) -> list[WoWItem]:
    """Generic, reusable "N random filler reward items" pool -- any content
    family with more locations than pooled items calls this to close its
    own deficit exactly (M4.9.3.1's own origin: core_loop's every-level
    granularity change left the standard/death_knight tracks short 64/10
    items respectively, with no existing mechanism in this direction --
    every other family is either self-balancing 1:1 or, for gates/traps,
    backfills the OPPOSITE direction via locations.py's own
    create_filler_locations/content/filler.yaml, a different, pre-existing
    mechanism this function does not touch or duplicate).

    Draws from BOTH filler_reward_items (12 real DB-extracted item
    categories, tag-filtered) and filler_reward_effects (5 curated reward
    effects, effect-filtered) together, respecting FillerCategoryPools,
    sampling each eligible category down to FILLER_PER_CATEGORY_CAP ("as
    even as possible" -- a category with fewer real rows than the cap
    contributes everything it has instead of being padded/excluded).
    Returns exactly `count` items whenever at least one category is
    selected: at real production scale (~11,284+5 rows across 17
    categories) the unique eligible supply comfortably exceeds `count`
    and every item is sampled without repetition ("as even as possible"
    category variety, unchanged). If a player narrows FillerCategoryPools
    to a combination whose real eligible supply is smaller than `count`
    (e.g. only "badge_currency" selected, 5 real items, against a
    64-item deficit), the shortfall is padded via repeated random draws
    from that same eligible set -- filler reward items are explicitly
    non-unique/replaceable by design, so a repeated item is a normal,
    valid outcome here, not a correctness problem. Only degrades to
    fewer than `count` items in the genuinely degenerate case where zero
    categories/names are eligible at all."""
    selected = set(world.options.filler_category_pools.value)

    by_category: dict[str, list[str]] = {}
    for name, tags in filler_reward_items_content_data.TAGS.items():
        category = next(iter(tags["category"]))
        if category in selected:
            by_category.setdefault(category, []).append(name)

    # M4.9.6: filler_reward_effects categories use the new distribution-
    # mode-aware weighted selection (mirroring traps' own mechanism)
    # instead of the plain "one entry per distinct name" the
    # filler_reward_items categories above still use -- a higher-weighted
    # effect row is proportionally more likely to survive the existing
    # shuffle+FILLER_PER_CATEGORY_CAP slice below, since it contributes
    # that many duplicate name-entries here.
    effect_names_by_category: dict[str, list[str]] = {}
    for name, effect in filler_reward_effects_content_data.EFFECT_BY_ITEM_NAME.items():
        category = _EFFECT_TO_CATEGORY[effect]
        if category in selected:
            effect_names_by_category.setdefault(category, []).append(name)
    for category, names in effect_names_by_category.items():
        # C1 (final whole-branch review): names is built from
        # EFFECT_BY_ITEM_NAME.items(), which iterates in item_id insertion
        # order (ascending spell_id). Feeding that order directly into
        # _distribute_filler_effect_counts, whose uniform/weighted modes
        # both cycle `i % len(eligible)`, is fine when total >> len(eligible)
        # (the trap trio this was copied from) but degenerates the OTHER
        # way when len(eligible) >> total (random_buff: 568 real names vs.
        # the 30-slot FILLER_PER_CATEGORY_CAP) -- it deterministically
        # selects only the first `total` names by item_id, on every seed,
        # regardless of distribution mode. Shuffling per-category with
        # world.random here (still seed-derived, so still deterministic
        # per-seed) restores real seed-to-seed variety across all 568
        # candidates without touching the distribution math itself.
        world.random.shuffle(names)
        weighted_counts = _distribute_filler_effect_counts(world, names, FILLER_PER_CATEGORY_CAP)
        weighted_names = []
        for name, n in weighted_counts.items():
            weighted_names.extend([name] * n)
        by_category.setdefault(category, []).extend(weighted_names)

    eligible_names: list[str] = []
    for category, names in by_category.items():
        world.random.shuffle(names)
        capped = names[:FILLER_PER_CATEGORY_CAP]
        eligible_names.extend(capped)

    world.random.shuffle(eligible_names)
    if len(eligible_names) >= count:
        chosen_names = eligible_names[:count]
    elif eligible_names:
        # M4.9.3.1: a player can legitimately narrow FillerCategoryPools
        # to a combination whose real eligible supply is smaller than
        # what a deficit-closing caller needs (e.g. only "badge_currency"
        # selected, 5 real items, against core_loop's up-to-64-item
        # standard-track deficit) -- filler reward items are explicitly
        # non-unique/replaceable by design (unlike progression items),
        # so padding with repeats here is correct behavior, not a
        # workaround: every chosen name still resolves to one real,
        # valid WoW item/effect either way. Only degrades gracefully to
        # fewer-than-count if NO category is selected at all (the
        # eligible_names-empty branch below), a distinct, much rarer
        # misconfiguration.
        chosen_names = list(eligible_names)
        chosen_names.extend(world.random.choice(eligible_names) for _ in range(count - len(eligible_names)))
        world.random.shuffle(chosen_names)
    else:
        chosen_names = []

    pool = []
    for name in chosen_names:
        if name in filler_reward_items_content_data.ITEMS:
            item_id, _item_count = filler_reward_items_content_data.ITEMS[name]
        else:
            item_id, _item_count = filler_reward_effects_content_data.ITEMS[name]
        pool.append(WoWItem(name, ItemClassification.filler, item_id, world.player))
    return pool

