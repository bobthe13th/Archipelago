# Archipelago/worlds/wow/options.py
from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, Toggle


class GameMode(Choice):
    """Which game mode to generate for (spec Sec5.4). Sprint (reach level 60)
    is the only mode with real completion logic as of Task 22 -- every other
    value here is reserved for a specific M4 task (see docs/m4-plan.md
    Group 6) and currently fails generation immediately with an OptionError
    naming which task builds it, rather than silently falling back to
    Sprint's behavior. Selecting one of these before its task lands is a
    configuration mistake the world should catch loudly, not paper over."""
    display_name = "Game Mode"
    option_sprint = 0
    option_key_hunt = 1
    option_classic = 2
    option_burning_crusade = 3
    option_wrath = 4
    option_completionist = 5
    option_artisan = 6
    option_collector = 7
    option_achievement_hunt = 8
    option_gladiator = 9
    option_explorer = 10
    option_fishing_quest = 11
    default = 0


class InstanceClearMode(Choice):
    """How much of a boss-roster-tracked raid (Task 23: Molten Core, Sunwell
    Plateau, Icecrown Citadel) must die before its instance-clear check
    fires. "all_bosses" (default, the fuller experience) requires every
    boss configured for that raid to die at least once, in any order, across
    however many attempts it takes. "final_boss_only" fires the instant the
    raid's own final boss dies, matching how the two M2 dungeons (Ragefire
    Chasm, Deadmines) already behave -- those two dungeons are unaffected by
    this option either way, since they carry no boss roster to track. The
    connected worldserver must have Archipelago.InstanceClearMode set to
    match -- this module has no way to read this option from the AP server
    itself, same manual-sync requirement as delivery_policy/
    combo_unlocks_scope above."""
    display_name = "Instance Clear Mode"
    option_all_bosses = 0
    option_final_boss_only = 1
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


class AuctionHouseCostTier(Choice):
    """Only used when delivery_policy is auction_house: the buyout price
    band for listed items (spec §7.1). "varied" mirrors the module's
    "Random" conf value -- picks uniformly among the other four tiers per
    listing; named differently here because AP's Choice options reserve
    the literal name "random" for its own random-value-selection feature.
    Never read by any rule. The connected worldserver must also have
    Archipelago.AuctionHouseCostTier set to match -- same manual-sync
    requirement as delivery_policy."""
    display_name = "Auction House Cost Tier"
    option_free = 0
    option_cheap = 1
    option_market = 2
    option_expensive = 3
    option_varied = 4
    default = 2


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


class CatchUpPolicy(Choice):
    """How a brand-new character catches up on WoW items the realm has
    already received (spec §7.2). Every delivered item is logged once
    regardless of delivery_policy, but historically only reached one
    designated character (everyone_receives' delivery character); every
    other character starts with none of it. Never read by any rule. The
    connected worldserver must also have Archipelago.CatchUpPolicy set to
    match -- same manual-sync requirement as delivery_policy and the gate
    toggles above. "Nothing" is the safe default (no behavior change from
    before this option existed)."""
    display_name = "New Character Catch-Up Policy"
    option_all_mailed_on_login = 0
    option_nothing = 1
    option_percent_per_level = 2
    option_level_scaled_bundle = 3
    default = 1


class CatchUpPercentPerLevel(Range):
    """Only used when catch_up_policy is percent_per_level: what percentage
    of the realm's total delivery history is granted to a character on each
    level-up, until they're fully caught up. Mirrored to
    Archipelago.CatchUpPercentPerLevel in the worldserver's .conf -- same
    manual-sync requirement as catch_up_policy."""
    display_name = "Catch-Up Percent Per Level"
    range_start = 1
    range_end = 100
    default = 10


class TrapsEnabled(Toggle):
    """When on, a percentage of the item pool becomes traps instead of
    progression/filler items -- fun and/or lethal effects that fire on
    receipt (spec §8's trap menu). Off by default per spec §18#5. Only 8 of
    the design's 17 trap effects have a real implementation as of Task 17
    -- see the module's content/traps.yaml for exactly which (the rest log
    and safely no-op instead of crashing or silently pretending to have
    applied something)."""
    display_name = "Traps"
    default = False


class TrapPercentageOfFiller(Range):
    """Only used when traps_enabled is on: what percentage of this seed's
    baseline quest+core-loop location count (a fixed 33, independent of how
    many traps/gates are actually enabled) becomes trap item copies.
    Distinct from check_density (spec §8 specifies this as its own knob,
    not the general density model)."""
    display_name = "Trap Percentage of Filler"
    range_start = 0
    range_end = 100
    default = 10


class TrapDistributionMode(Choice):
    """Only used when traps_enabled is on: how the total trap count (from
    trap_percentage_of_filler) is split across the eligible trap effect
    types. "uniform" spreads them as evenly as possible; "weighted" uses
    each trap's own relative weight (its content-table ceiling count) so
    some effects are proportionally more common than others; "chaos" picks
    each individual copy's type independently at random, varying the split
    generation to generation even for identical options. weighted is the
    spec §18#5 default."""
    display_name = "Trap Distribution Mode"
    option_uniform = 0
    option_weighted = 1
    option_chaos = 2
    default = 1


class LethalTrapsEnabled(Toggle):
    """Only used when traps_enabled is on: whether the lethal-tagged trap
    subset (spawn-a-rare-on-you, floor-is-lava) is eligible to be sampled
    at all. Off by default per spec §18#5 -- funny and lethal traps are not
    mutually exclusive in the design, but lethal ones need an explicit
    opt-in."""
    display_name = "Lethal Traps"
    default = False


class DeathLinkSend(Toggle):
    """When on, a player-caused death on your WoW realm broadcasts a
    DeathLink Bounce to the rest of the multiworld (spec §11). Independent
    of death_link_receive -- you can send without receiving, or vice versa.
    Never read by any rule. The connected worldserver must also have
    Archipelago.DeathLinkSendEnabled set to match -- this module has no way
    to read this option from the AP server itself, same manual-sync
    requirement as delivery_policy/catch_up_policy/the gate toggles above."""
    display_name = "DeathLink: Send"
    default = False


class DeathLinkReceive(Toggle):
    """When on, an incoming DeathLink Bounce from the multiworld kills every
    online player on your WoW realm (spec §11). Never read by any rule. The
    connected worldserver must also have Archipelago.DeathLinkReceiveEnabled
    set to match -- same manual-sync requirement as death_link_send."""
    display_name = "DeathLink: Receive"
    default = False


class DeathLinkSendCooldown(Range):
    """Only used when death_link_send is on: minimum seconds between two
    outgoing DeathLink sends -- prevents a raid wipe (many players dying
    within the same few seconds) from spamming the multiworld with one
    Bounce per player (spec §11). Mirrored to
    Archipelago.DeathLinkSendCooldownSeconds in the worldserver's .conf --
    same manual-sync requirement as death_link_send."""
    display_name = "DeathLink Send Cooldown (seconds)"
    range_start = 1
    range_end = 60
    default = 15


class DeathLinkReceiveCooldown(Range):
    """Only used when death_link_receive is on: minimum seconds between two
    incoming DeathLink kills being applied -- prevents a cascade where
    several other slots' deaths arrive in a burst and repeatedly re-kill
    your realm's players (spec §11). Mirrored to
    Archipelago.DeathLinkReceiveCooldownSeconds in the worldserver's .conf --
    same manual-sync requirement as death_link_receive."""
    display_name = "DeathLink Receive Cooldown (seconds)"
    range_start = 1
    range_end = 60
    default = 15


class SpiritHealerVariant(Choice):
    """Which of resurrection sickness and spirit-healer durability loss are
    suppressed when resurrecting (spec §11's spirit-healer options).
    "vanilla" applies both penalties normally; "no_res_sickness" and
    "no_durability_loss" each suppress exactly one; "neither" suppresses
    both (read as "neither penalty applies", not "neither is suppressed" --
    the spec names this option "neither" without pinning the reading, so
    this is a resolved interpretation, not a literal spec quote). Applies
    realm-wide to every resurrection, not narrowly to the spirit-healer NPC
    only -- this AzerothCore checkout's veto hook for resurrection sickness
    (OnPlayerResurrect) has no way to distinguish which resurrection source
    triggered it, and the durability-loss suppression is a worldserver-wide
    rate override (RATE_DURABILITY_LOSS_ON_SPIRIT_RESURRECT), not a per-call
    choice -- both are correct scope for this architecture anyway, since one
    WoW realm is one AP slot (spec's core commitment), not a per-character
    choice. Never read by any rule. The connected worldserver must also have
    Archipelago.SpiritHealerVariant set to match -- this module has no way to
    read this option from the AP server itself, same manual-sync requirement
    as delivery_policy/catch_up_policy above."""
    display_name = "Spirit Healer Variant"
    option_vanilla = 0
    option_no_res_sickness = 1
    option_no_durability_loss = 2
    option_neither = 3
    default = 0


class ComboUnlocksScope(Choice):
    """Which race/class combos requiring an expansion (spec §5.5) start
    locked behind an Archipelago item instead of being freely creatable.
    "tbc" gates Blood Elf and Draenei (both races, not narrowed to their
    class-restricted combos -- see the module's content/gates.yaml for why
    per-combo granularity isn't attempted); "wotlk" gates Death Knight
    (any race); "both" gates all three. Off by default (§18#5). Only the
    expansion-tier gate is implemented, not every individual race/class
    pairing -- unlocking every combo (e.g. Dwarf Paladin specifically)
    would need the out-of-scope MPQ client patch per §5.5/§20.1. The
    connected worldserver must also have Archipelago.ComboUnlocksScope set
    to match -- this module has no way to read this option from the AP
    server itself, same manual-sync requirement as delivery_policy/
    catch_up_policy above."""
    display_name = "Combo Unlocks Scope"
    option_off = 0
    option_tbc = 1
    option_wotlk = 2
    option_both = 3
    default = 0


class StartingChoice(Choice):
    """How many race/class combos a new character can freely choose from
    before any combo-unlock item is earned (spec §5.5's exact menu):
    "one_choice_only" locks the account to whichever single combo is
    chosen at generation; "one_horde_one_alliance" allows one pre-chosen
    combo per faction; "one_class_one_horde_one_alliance" additionally
    allows a second, different class as long as it's also one-per-faction.
    This is pure itemization/config resolved once at generation -- the
    module does not enforce it at runtime (there is no per-account
    "which combo did you pick" state anywhere in this checkout to check
    against), so it only affects `Fill`/spoiler-log bookkeeping in this
    milestone, not an in-game restriction beyond what ComboUnlocksScope
    itself already locks. Deliberately NOT mirrored to a worldserver.conf
    key for that reason -- there is nothing on the module side that reads
    it."""
    display_name = "Starting Choice"
    option_one_choice_only = 0
    option_one_horde_one_alliance = 1
    option_one_class_one_horde_one_alliance = 2
    default = 0


@dataclass
class WoWOptions(PerGameCommonOptions):
    game_mode: GameMode
    check_density: CheckDensity
    max_optional_locations: MaxOptionalLocations
    delivery_policy: DeliveryPolicy
    auction_house_cost_tier: AuctionHouseCostTier
    proficiency_gating: ProficiencyGating
    access_gating: AccessGating
    character_unlock_gating: CharacterUnlockGating
    catch_up_policy: CatchUpPolicy
    catch_up_percent_per_level: CatchUpPercentPerLevel
    traps_enabled: TrapsEnabled
    trap_percentage_of_filler: TrapPercentageOfFiller
    trap_distribution_mode: TrapDistributionMode
    lethal_traps_enabled: LethalTrapsEnabled
    death_link_send: DeathLinkSend
    death_link_receive: DeathLinkReceive
    death_link_send_cooldown: DeathLinkSendCooldown
    death_link_receive_cooldown: DeathLinkReceiveCooldown
    spirit_healer_variant: SpiritHealerVariant
    combo_unlocks_scope: ComboUnlocksScope
    starting_choice: StartingChoice
    instance_clear_mode: InstanceClearMode

