# Archipelago/worlds/wow/options.py
from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, Toggle


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
    items exist or what's required to win -- see design spec §7; never read
    by any rule. The connected worldserver must also have
    Archipelago.DeliveryPolicy set to match -- this module has no way to
    read this option from the AP server itself, same manual-sync
    requirement as proficiency_gating/access_gating/character_unlock_gating
    (see the module's conf.dist for the matching warning, including the
    auction_house + access_gating softlock it refuses to combine)."""
    display_name = "Item Delivery Policy"
    option_everyone_receives = 0
    option_shared_cache_npc = 1
    option_auction_house = 2
    option_first_to_claim = 3
    default = 0


class ProficiencyGating(Toggle):
    """When on, armor and weapon proficiencies (Plate/Mail/Leather armor;
    Two-Handed Swords/Axes/Maces/Staves/Wands) are locked behind Archipelago
    items instead of being free at character creation (spec §5.1 -- large
    class-feel impact, optional, off by default). The connected worldserver
    must also have Archipelago.ProficiencyGating enabled in its .conf to
    match -- this module has no way to read this option from the AP server
    itself, so operator and seed must be kept in sync by hand (see the
    module's conf.dist for the matching warning)."""
    display_name = "Armor/Weapon Proficiency Gating"
    default = False


class AccessGating(Toggle):
    """When on, Auction House access, Hearthstone use, and sending mail are
    locked behind Archipelago items instead of being free from the start
    (spec §5.1 -- optional, off by default). Only 3 of the design's 5 access
    types are implemented: this AzerothCore checkout has no suppression
    hook for bank access or gathering (mining/herbalism/skinning), so those
    two are not gated (see the module's content/gates.yaml for why). The
    connected worldserver must also have Archipelago.AccessGating enabled
    in its .conf to match -- same manual-sync requirement as
    proficiency_gating above."""
    display_name = "Access Gating"
    default = False


class CharacterUnlockGating(Toggle):
    """When on, bank bag slots, spending talent points, and dual spec are
    locked behind Archipelago items instead of being free/purchasable from
    the start (spec §5.1 -- optional, off by default). Glyph Slot gating
    (also named in the design) is not implemented by this module -- see
    the module's content/gates.yaml for why. The connected worldserver must
    also have Archipelago.CharacterUnlockGating enabled in its .conf to
    match -- same manual-sync requirement as the other gate toggles."""
    display_name = "Character Unlock Gating"
    default = False


@dataclass
class WoWOptions(PerGameCommonOptions):
    game_mode: GameMode
    check_density: CheckDensity
    max_optional_locations: MaxOptionalLocations
    delivery_policy: DeliveryPolicy
    proficiency_gating: ProficiencyGating
    access_gating: AccessGating
    character_unlock_gating: CharacterUnlockGating

