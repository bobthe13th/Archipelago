# Archipelago/worlds/wow/options.py
from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range


class GameMode(Choice):
    """Which game mode to generate for. Sprint (reach level 60) is the only
    mode implemented so far -- the spec's other modes (Key Hunt, Classic,
    Burning Crusade, Wrath, Completionist, Artisan, Collector, Achievement
    Hunt) are explicitly Milestone 4 scope."""
    display_name = "Game Mode"
    option_sprint = 0
    default = 0


class CheckDensity(Range):
    """Global check density (0-100). Controls how many rows are sampled from
    each enabled optional location category. 0 disables every optional
    category; 100 samples the maximum this seed's per-category weights and
    hard ceiling allow. Level-ups and instance clears (the core loop) are
    never subject to this -- only optional categories route through it."""
    display_name = "Check Density"
    range_start = 0
    range_end = 100
    default = 25


class MaxOptionalLocations(Range):
    """Hard ceiling on the total number of optional-category locations added
    to the pool in one generation, regardless of check_density or how many
    optional categories are enabled. Exists so a maximalist combination of
    high density + many enabled categories can't bloat the datapackage or
    generation time unboundedly."""
    display_name = "Max Optional Locations"
    range_start = 0
    range_end = 5000
    default = 300


class DeliveryPolicy(Choice):
    """How Archipelago-granted items reach you. This never affects what
    items exist or what's required to win -- see design spec §7. Resolved
    once at generation into slot_data; the module reads it at startup, not
    from any rule."""
    display_name = "Item Delivery Policy"
    option_everyone_receives = 0
    option_shared_cache_npc = 1
    option_auction_house = 2
    option_first_to_claim = 3
    default = 0


@dataclass
class WoWOptions(PerGameCommonOptions):
    game_mode: GameMode
    check_density: CheckDensity
    max_optional_locations: MaxOptionalLocations
    delivery_policy: DeliveryPolicy

