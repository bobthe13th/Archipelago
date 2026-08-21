# Archipelago/worlds/wow/items.py
from BaseClasses import Item, ItemClassification
from . import content_data
from .content_data import ITEMS
from . import core_loop_content_data
from . import fish_content_data
from . import gates_content_data
from . import rares_content_data
from . import traps_content_data


class WoWItem(Item):
    game = "World of Warcraft WotLK"


def create_item_pool(world) -> list:
    return [
        WoWItem(name, ItemClassification.progression, item_id, world.player)
        for name, item_id in ITEMS.items()
    ]


def create_core_loop_item_pool(world) -> list:
    pool = []
    for name, (item_id, count) in core_loop_content_data.ITEMS.items():
        for _ in range(count):
            pool.append(WoWItem(name, ItemClassification.progression, item_id, world.player))
    return pool


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
    ("Progressive Bank Bag Slot:", "character_unlock_gating"),
    ("Talent Point Access", "character_unlock_gating"),
    ("Dual Spec Unlock", "character_unlock_gating"),
]


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


def _trap_baseline_location_count() -> int:
    # The stable "real content" location count traps are sized as a
    # percentage of -- quest + core-loop locations, which don't themselves
    # grow when traps are enabled (unlike the gates family's own filler
    # locations, which would make the baseline circular).
    return (
        len(content_data.LOCATIONS)
        + len(core_loop_content_data.LEVEL_LOCATIONS)
        + len(core_loop_content_data.INSTANCE_CLEAR_LOCATIONS)
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
    return max(0, round(_trap_baseline_location_count() * world.options.trap_percentage_of_filler / 100))


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

