# Archipelago/worlds/wow/options.py
from dataclasses import dataclass

from Options import Choice, OptionSet, PerGameCommonOptions, Range, Toggle


class GameMode(Choice):
    """Which game mode to generate for (spec Sec5.4). Sprint (reach level 60)
    is the only mode with real completion logic as of Task 22 -- every other
    value here is reserved for a specific M4 task (see docs/m4-plan.md
    Group 6) and currently fails generation immediately with an OptionError
    naming which task builds it, rather than silently falling back to
    Sprint's behavior. Selecting one of these before its task lands is a
    configuration mistake the world should catch loudly, not paper over.
    hundred_percent: one-click theoretical maximum -- forces every optional
    category on at effective check_density 100, ignoring check_density and
    every include_* toggle. A true one-click maximum, not a
    default-but-overridable convenience."""
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
    option_hundred_percent = 12
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


class CompletionistExpansion(Choice):
    """Only relevant when game_mode is completionist (Task 24). Which
    expansion's instance-clear locations Completionist requires -- vanilla
    (Ragefire Chasm, Deadmines, Molten Core), tbc (Sunwell Plateau), or
    wotlk (Icecrown Citadel), per core_loop.yaml's own `expansion:` tag on
    each row. Completionist's completion rule is unaffected by
    InstanceClearMode -- it checks the same "Instance Unlock" items every
    other raid completion rule checks, regardless of which granularity
    produced the underlying location check."""
    display_name = "Completionist Expansion"
    option_vanilla = 0
    option_tbc = 1
    option_wotlk = 2
    default = 0


class KeyHuntKeysRequired(Range):
    """Only relevant when game_mode is key_hunt (Task 25). How many "Key
    Hunt: Key" items must be received to complete the goal, alongside
    key_hunt_instances_required raids/dungeons also being cleared. Capped at
    40 -- content/rares.yaml's curated roster and its matching item ceiling
    (a future task widening that roster must widen this range_end to match,
    the same coupling filler.yaml's own header comment documents for its
    ceiling). The actual number of keys pooled in a given generation is
    density-sampled (check_density), and can be LOWER than this value if
    check_density constrains the sampled rare count below 40 -- a
    key_hunt seed with a keys_required higher than what density sampling
    actually pools would be uncompletable, which is exactly what this
    task's goals.py validator exists to catch at generation time."""
    display_name = "Key Hunt: Keys Required"
    range_start = 1
    range_end = 40
    # 10, not some rounder-looking number: at the global CheckDensity default
    # of 25, density.predict_sample_size(40 rows, weight 100) predicts
    # exactly ceil(40 * 0.25) = 10 -- so key_hunt is satisfiable out of the
    # box with every other option left at its own default, not an
    # immediate OptionError. A higher default here would make "just pick
    # key_hunt" alone fail generation, which is correct behavior for the
    # validator to catch but a bad first-touch default.
    default = 10


class KeyHuntInstancesRequired(Range):
    """Only relevant when game_mode is key_hunt (Task 25). How many of the 5
    existing instance-clear raids/dungeons (Ragefire Chasm, Deadmines,
    Molten Core, Sunwell Plateau, Icecrown Citadel) must also be cleared to
    complete the goal, alongside key_hunt_keys_required keys. 0 makes Key
    Hunt a pure key-collection goal with no instance requirement at all."""
    display_name = "Key Hunt: Instances Required"
    range_start = 0
    range_end = 5
    default = 1


class ArtisanPrimaryProfessionsRequired(Range):
    """Only relevant when game_mode is artisan (Task 27). How many of the 11
    primary professions must reach skill 450 to complete the goal, alongside
    all 3 secondary professions (First Aid, Cooking, Fishing) also reaching
    450. Default 2 matches the realistic limit of primary professions a
    single WotLK character can actively know at once -- see
    professions.yaml's own KNOWN ACCEPTED LIMITATION comment for why a
    higher value, while selectable, may require profession-swapping or
    multiple characters to actually complete."""
    display_name = "Artisan: Primary Professions Required"
    range_start = 0
    range_end = 11
    default = 2


class CollectorItemsRequired(Range):
    """Only relevant when game_mode is collector (Task 27). How many of the
    264 curated mounts/pets (collections.yaml) must have been received at
    least once to complete the goal. Default 264 (the full roster) matches
    the design spec's "every collectible mount AND every collectible pet"
    scope exactly -- item delivery here is not gated by in-game drop rarity
    (a received AP item is mailed directly, it does not need to actually
    drop from its original source), so unlike Artisan's profession-slot
    constraint there is no hard game-mechanic reason to require fewer than
    all of them. Lower this only if a shorter Collector run is wanted for a
    given seed."""
    display_name = "Collector: Items Required"
    range_start = 1
    range_end = 264
    default = 264


class CheckDensity(Range):
    """Global check density (0-100). Controls how many rows are sampled from
    each enabled optional location category. 0 disables every optional
    category; 100 samples the maximum this seed's per-category weights
    allow. Level-ups and instance clears (the core loop) are
    never subject to this -- only optional categories route through it."""
    display_name = "Check Density"
    range_start = 0
    range_end = 100
    default = 25


class DeliveryPolicy(Choice):
    """How Archipelago-granted items reach you. This never affects what
    items exist or what's required to win -- see design spec §7; never read
    by any rule. The connected worldserver must also have
    Archipelago.DeliveryPolicy set to match -- this module has no way to
    read this option from the AP server itself, same manual-sync
    requirement as proficiency_gating/access_gating/character_unlock_gating
    (see the module's conf.dist for the matching warning, including the
    auction_house + access_gating softlock it refuses to combine).
    all_accounts_delivery mails every delivered item to every account with
    at least one real (non-deleted) character -- deduped to one character
    per account (whichever logged out most recently), not literally every
    character. No cap on volume: a long campaign can mail thousands of
    items to every account with no filtering by classification. Orthogonal
    to catch_up_policy: this only ever reaches accounts/characters that
    exist AT THE MOMENT each item is delivered -- an account created
    afterward relies entirely on catch_up_policy to backfill what it
    missed, exactly like every other delivery policy."""
    display_name = "Item Delivery Policy"
    option_single_delivery_character = 0
    option_shared_cache_npc = 1
    option_auction_house = 2
    option_first_to_claim = 3
    option_all_accounts_delivery = 4
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
    designated character (single_delivery_character's delivery character); every
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


class QuestRewardTypePools(OptionSet):
    """Which Quest Rewards quest-type pools to include (M4.8 tag-based
    sub-filtering). A location is a candidate iff its own type tag(s)
    intersect this selection -- dungeon_quest (real QuestInfo.dbc "Dungeon"
    category), elite_quest (group-recommended quests), repeatable (daily/
    weekly quests), standard (every quest that's none of the other three --
    every quest carries at least one type tag, never zero). Default selects
    every value (full vocabulary) -- narrow this to shrink the candidate
    pool before check_density/quest_reward_weight sample from it. The 19
    locations migrated from the retired standalone `quests` family (the
    M1/M2 Northshire/Goldshire starting quests) are exempt from this filter
    entirely (always_present) -- see quest_reward_weight's own docstring."""
    display_name = "Quest Reward Type Pools"
    valid_keys = ["dungeon_quest", "elite_quest", "repeatable", "standard"]
    default = valid_keys


class QuestRewardExpansionPools(OptionSet):
    """Which Quest Rewards expansion pools to include (M4.8), ANDed against
    quest_reward_type_pools -- a location must match BOTH dimensions'
    selections to become a candidate. Expansion is resolved at
    content-extraction time from the quest's own quest-giver's real spawn
    map. Default selects every value."""
    display_name = "Quest Reward Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class VendorStockExpansionPools(OptionSet):
    """Which Vendor Inventories expansion pools to include (M4.8).
    Expansion is resolved from the selling vendor's own real spawn map.
    Default selects every value."""
    display_name = "Vendor Stock Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class QuestRewardWeight(Range):
    """Category weight for Quest Rewards (M4.8, replaces the removed
    include_quest_rewards boolean toggle and locations.py's former
    hardcoded weight=100 literal) -- multiplied against global
    check_density to decide how many of the tag-matched candidate
    locations actually enter the pool (density.sample_category, unchanged).
    Default 100 (this project's own explicit, deliberate choice): at the
    global check_density default (25), this makes Quest Rewards
    on-by-default at roughly a 25% sample of the tag-matched candidate set,
    a real behavior change from the predecessor include_quest_rewards
    toggle's own default of False (fully off). Set to 0 to fully exclude
    this family, matching the old toggle's off state. The 19 locations
    migrated from the retired `quests` family are exempt from this
    weight/density sampling entirely (always_present) -- they are always
    included, at any weight, including 0."""
    display_name = "Quest Reward Weight"
    range_start = 0
    range_end = 100
    default = 100


class VendorStockWeight(Range):
    """Category weight for Vendor Inventories (M4.8, replaces the removed
    include_vendor_stock boolean toggle and locations.py's former hardcoded
    weight=10 literal). Default 100 (this project's own explicit,
    deliberate choice) -- NOT zero-regression relative to the old hardcoded
    10: an unmodified seed now samples roughly 10x more Vendor Inventories
    locations by default than before this milestone, and is on by default
    at all (the predecessor include_vendor_stock toggle defaulted to
    False, fully off). Set to 0 to fully exclude this family."""
    display_name = "Vendor Stock Weight"
    range_start = 0
    range_end = 100
    default = 100


class RecipeProfessionPools(OptionSet):
    """Which Learned Recipes profession pools to include (M4.9, adopting
    M4.8's tag-based sub-filtering from day one). A location is a
    candidate iff its own profession tag intersects this selection --
    resolved at extraction time from the recipe's own taught spell's real
    skill-line (SkillLineAbility.dbc, since this DB's own skill_line_ability
    SQL tables are unpopulated stubs). "other" catches the small remainder
    (61 of 1,912 real rows) whose skill-line doesn't resolve to one of the
    14 known primary/secondary professions -- every recipe carries exactly
    one profession tag, never zero. Default selects every value (full
    vocabulary, zero-regression). Unlike quest_reward_type_pools/
    vendor_stock_expansion_pools, there is no matching *_weight Range
    option for this family -- per spec, EVERY tag-matching row is
    included, with no check_density/weight sampling stage at all."""
    display_name = "Recipe Profession Pools"
    valid_keys = [
        "alchemy", "blacksmithing", "cooking", "enchanting", "engineering",
        "first_aid", "fishing", "herbalism", "inscription", "jewelcrafting",
        "leatherworking", "mining", "skinning", "tailoring", "other",
    ]
    default = valid_keys


class RecipeExpansionPools(OptionSet):
    """Which Learned Recipes expansion pools to include (M4.9), ANDed
    against recipe_profession_pools. Expansion is resolved from the
    recipe's own required-skill-rank bracket (<=300 vanilla, <=375 tbc,
    else wotlk -- the same bracket convention content/professions.yaml's
    own skill_milestone rows already use), not the teaching trainer/
    vendor's zone -- chosen because a meaningful fraction of real recipe
    items in this DB have no vendor/trainer source at all (loot/quest-only
    recipes), while RequiredSkillRank is always present on every recipe
    item. Default selects every value."""
    display_name = "Recipe Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class TrainerSpellClassPools(OptionSet):
    """Which Trainer Spells & Abilities class pools to include (M4.9). A
    location is a candidate iff its own class tag(s) intersect this
    selection -- resolved from the real class-trainer's own
    trainer.Requirement field, confirmed real via
    Trainer::IsTrainerValidForPlayer (Trainer.cpp): for Type::Class
    trainers, Requirement IS the player's class id directly. A small
    number of real spell_ids (4 of 1,966) are taught by more than one
    class's trainer and carry every matching class tag, not just one.
    Mount/Tradeskill/Pet trainers are out of scope for this family
    entirely (Tradeskill rank-up spells are already covered by the
    existing professions family's skill_milestone triggers; Mount
    trainers gate by race, not class). Default selects every value."""
    display_name = "Trainer Spell Class Pools"
    valid_keys = [
        "warrior", "paladin", "hunter", "rogue", "priest",
        "death_knight", "shaman", "mage", "warlock", "druid",
    ]
    default = valid_keys


class TrainerSpellExpansionPools(OptionSet):
    """Which Trainer Spells & Abilities expansion pools to include (M4.9).
    Expansion is resolved from the teaching trainer's own real spawn map
    (creature_default_trainer -> creature.map -> Map.dbc's expansionID),
    the same pattern extract_vendor_stock.py's _load_vendor_expansions and
    extract_quest_rewards.py's _load_quest_expansions already established.
    Default selects every value."""
    display_name = "Trainer Spell Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class VendorCheckRepeatBehavior(Choice):
    """What happens when a player interacts again with a Vendor Inventories
    slot they've already checked (M4.7). The synthesized AP item only ever
    represents the FIRST interaction -- suppress_entirely (default) cancels
    the purchase/refunds gold with a system message, matching "kept out of
    the way as much as possible". vanilla_item swaps back to the real WoW
    item, as if the slot had never been AP-tagged. gold_conversion grants
    the real item's vendor SellPrice in copper instead of either item.
    filler_consumable grants a fixed generic filler item instead. Read
    directly from slot_data at connect (Finding #10's first real consumer) --
    unlike most of this module's options, this one does NOT need a manual
    Archipelago.conf mirror.
    Two caveats not obvious from the names above (M4.7 final review, Finding
    I7): gold_conversion is NOT a fair trade -- the player is still charged
    the real item's full BuyPrice (times any reputation discount) to make
    the repeat purchase, and only refunded the item's (typically much lower)
    SellPrice, a guaranteed net loss of roughly 75-80% of the price paid.
    vanilla_item and filler_consumable each grant exactly 1 unit of the item
    regardless of the quantity actually purchased, and neither of those two
    (nor gold_conversion beyond its partial SellPrice refund) refunds the
    gold charged for the purchase.
    KNOWN LIMITATION (as of the vendor maxcount=1 stock-limit change): vanilla_item,
    gold_conversion, and filler_consumable currently have NO EFFECT for Vendor
    Inventories locations -- the vendor's own native stock limit (maxcount=1) now
    refuses a second purchase attempt before this module's interception hook can
    ever run, so only suppress_entirely's behavior (a no-op) is actually reachable
    in practice. This is an unintended interaction between two separately-built
    features, not a deliberate design choice, and is tracked for a real fix
    (conditionally applying the stock limit only when this option is
    suppress_entirely) in a future pass."""
    display_name = "Vendor Check Repeat Behavior"
    option_suppress_entirely = 0
    option_vanilla_item = 1
    option_gold_conversion = 2
    option_filler_consumable = 3
    default = 0


class DeathKnightSlot(Toggle):
    """M4.9: whether this slot's realm is intended to be played on a Death
    Knight character. Purely a generation-time signal, exactly like
    starting_choice above -- there is no per-account "which class did you
    actually create" state in this checkout for the module to check
    against, so this option is NOT read at runtime by the C++ module at
    all (unlike most of this module's options, it is deliberately NOT
    mirrored to slot_data or a worldserver.conf key -- see slot_data.py's
    own "_add_x_to_slot_data" pattern, which this option does not
    participate in). Instead, the C++ level-up hook
    (ArchipelagoLevelScript.cpp) reads the connecting player's OWN real
    class directly via player->getClass() at the moment they level up, and
    picks whichever of the two content tracks (LEVEL_LOCATIONS_STANDARD /
    LEVEL_LOCATIONS_DEATH_KNIGHT) matches -- this option's ONLY job is to
    decide, at generation time, which of those two tracks' "Reach Level N"
    locations even exist in this slot's world
    (locations.py's create_core_loop_locations). If you turn this on but
    then actually play a non-Death-Knight character (or vice versa), the
    world you generated and the character you played no longer agree, and
    the mismatched track's locations will never be reachable in practice
    -- the same "you must honor your own declared option" trust model this
    module already uses for starting_choice/combo_unlocks_scope, not a new
    kind of gap. Off by default: most seeds are not Death Knight runs, and
    every existing seed's YAML (with this key absent) resolves to the
    pre-M4.9 standard 1-80 track, matching pre-M4.9 behavior as closely as
    the granularity change allows."""
    display_name = "Death Knight Slot"
    default = False


class DeathKnightLevel1Start(Toggle):
    """M4.9: only meaningful when death_knight_slot is also True. Documents
    and enables an opt-in for a level-1 (rather than the class's native
    level-55) Death Knight start, by flipping the REALM-WIDE
    StartHeroicPlayerLevel setting in worldserver.conf (real AzerothCore
    config, confirmed default 55, range 1-MaxPlayerLevel) from 55 down to
    1. This is a one-line config flip, not something this option enforces
    or reads at runtime -- it is realm-wide, not per-slot (the WoW server
    has exactly one StartHeroicPlayerLevel value for every character on
    the realm), so it falls into this project's existing "manual
    server-config sync" category (see docs/guides/server-setup-guide.md),
    the same as delivery_policy/catch_up_policy/the gate toggles, NOT a
    new kind of limitation.
    IMPORTANT, real rough edges if enabled (verified during M4.9 planning
    against this checkout's own live database, not guessed -- see Task 6's
    reproducible queries): a level-1 Death Knight still spawns in Ebon
    Hold and is still handed the Death's Door questline -- both are built
    around a level-55 character's stat/gear/ability budget, not a level-1
    one. This checkout's live `trainer_spell` table (the normalized
    trainer/trainer_spell schema this checkout's worldserver actually
    reads -- `npc_trainer` does not exist in the live DB) shows the Death
    Knight class trainer's taught-spell ReqLevel values start at exactly
    55 (55, 56, 57, ... 80, zero rows below 55), and
    playercreateinfo_spell_custom (the other table a dormant sub-55 grant
    could theoretically live in) is entirely empty in this checkout's base
    data -- confirming there is no dormant/latent sub-55 Death Knight
    ability-acquisition curve anywhere in this checkout's data to fall
    back on. A level-1 Death Knight who turns this on is playable (can
    immediately leave Ebon Hold and level normally, like any other class,
    picking up the class's real level-up ability grants starting at level
    55 same as everyone else), but faces level-58-appropriate starting-zone
    content at level 1 if they choose to engage with Ebon Hold/Death's
    Door instead of leaving immediately. Off by default."""
    display_name = "Death Knight Level 1 Start (Opt-In, Rough Edges)"
    default = False


@dataclass
class WoWOptions(PerGameCommonOptions):
    game_mode: GameMode
    check_density: CheckDensity
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
    completionist_expansion: CompletionistExpansion
    key_hunt_keys_required: KeyHuntKeysRequired
    key_hunt_instances_required: KeyHuntInstancesRequired
    artisan_primary_professions_required: ArtisanPrimaryProfessionsRequired
    collector_items_required: CollectorItemsRequired
    quest_reward_type_pools: QuestRewardTypePools
    quest_reward_expansion_pools: QuestRewardExpansionPools
    vendor_stock_expansion_pools: VendorStockExpansionPools
    quest_reward_weight: QuestRewardWeight
    vendor_stock_weight: VendorStockWeight
    recipe_profession_pools: RecipeProfessionPools
    recipe_expansion_pools: RecipeExpansionPools
    trainer_spell_class_pools: TrainerSpellClassPools
    trainer_spell_expansion_pools: TrainerSpellExpansionPools
    vendor_check_repeat_behavior: VendorCheckRepeatBehavior
    death_knight_slot: DeathKnightSlot
    death_knight_level1_start: DeathKnightLevel1Start

