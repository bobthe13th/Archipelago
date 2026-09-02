# Archipelago/worlds/wow/options.py
from dataclasses import dataclass

from Options import Choice, OptionSet, PerGameCommonOptions, Range, Toggle

from . import rares_content_data


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
    default-but-overridable convenience. zone_leveler (M4.11.1): a short,
    vertical leveling slice inside one locked zone -- BarrensBeater is its one
    curated instance (zone_leveler_starting_zone=barrens)."""
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
    option_explorer = 10
    option_fishing_quest = 11
    option_hundred_percent = 12
    option_zone_leveler = 13
    default = 0


class InstanceClearMode(Choice):
    """How much of a boss-roster-tracked raid (Task 23: Molten Core, Sunwell
    Plateau, Icecrown Citadel) must die before its instance-clear check
    fires. "all_bosses" (default, the fuller experience) requires every
    boss configured for that raid to die at least once, in any order, across
    however many attempts it takes. "final_boss_only" fires the instant the
    raid's own final boss dies, matching how the two M2 dungeons (Ragefire
    Chasm, Deadmines) already behave -- those two dungeons are unaffected by
    this option either way, since they carry no boss roster to track. Read
    directly from slot_data at connect (M4.9) -- unlike most of this
    module's options, this one does NOT need a manual Archipelago.conf
    mirror; the old Archipelago.InstanceClearMode conf key has been removed
    outright."""
    display_name = "Instance Clear Mode"
    option_all_bosses = 0
    option_final_boss_only = 1
    default = 0


class CompletionistExpansion(Choice):
    """Only relevant when game_mode is completionist (Task 24). Which
    expansion's instance-clear locations Completionist requires -- vanilla
    (Ragefire Chasm, Deadmines, Molten Core, Wailing Caverns, Razorfen
    Kraul, Razorfen Downs -- the last 3 added M4.11.1 for BarrensBeater),
    tbc (Sunwell Plateau), or wotlk (Icecrown Citadel), per
    core_loop.yaml's own `expansion:` tag on each row. Completionist's
    completion rule is unaffected by InstanceClearMode -- it checks the
    same "Instance Unlock" items every other raid completion rule checks,
    regardless of which granularity produced the underlying location
    check."""
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
    """Only relevant when game_mode is key_hunt (Task 25). How many of the 8
    existing instance-clear raids/dungeons (Ragefire Chasm, Deadmines, Molten
    Core, Sunwell Plateau, Icecrown Citadel, Wailing Caverns, Razorfen Kraul,
    Razorfen Downs -- the last 3 added M4.11.1 for BarrensBeater) must also be
    cleared to complete the goal, alongside key_hunt_keys_required keys. 0
    makes Key Hunt a pure key-collection goal with no instance requirement at
    all."""
    display_name = "Key Hunt: Instances Required"
    range_start = 0
    range_end = 8
    default = 1


class KeyHuntZonePools(OptionSet):
    """Only relevant when game_mode is key_hunt (M4.11.1). Which real WoW
    areas' rares are eligible to be sampled into the pool -- default is every
    area tag this checkout's 40 curated rares span (zero-regression:
    unrestricted, identical to Key Hunt's pre-M4.11.3.1 behavior). Combined
    with check_density/key_hunt_keys_required exactly like every other tag
    dimension (M4.8 §2): AND'd with density sampling, not a separate ceiling.
    (M4.11.3.1: reads the family's unified `area` tag dimension -- Task 1-3's
    fixed resolve_area_tags_for_positions -- instead of the retired
    single-winner `zone` tag; this option's own player-facing name is
    unchanged.)"""
    display_name = "Key Hunt: Zone Pools"
    valid_keys = frozenset(
        area for tags in rares_content_data.TAGS.values() for area in tags.get("area", frozenset())
    )
    default = valid_keys


class ZoneLevelerStartingZone(Choice):
    """Only relevant when game_mode is zone_leveler (M4.11.1). Which zone's
    curated Zone Leveler entry to play -- only "barrens" (BarrensBeater) is
    curated as of this milestone (docs/superpowers/specs/2026-08-31-archipelago-
    wow-m4.11.1-zone-leveler-barrensbeater-design.md). Adding a zone later is a
    pure zone_leveler_content_data.py curation task, not new engineering."""
    display_name = "Zone Leveler: Starting Zone"
    option_barrens = 0
    default = 0


class ZoneLevelerGoals(OptionSet):
    """Only relevant when game_mode is zone_leveler (M4.11.1). Which win
    conditions must ALL be met to complete the goal -- at least one required
    (validated at generate_early). Rough check-count contribution per goal
    (Barrens' own concrete numbers; other zones will differ once curated):
    reach_zone_level_cap ~= 20 checks (one per level, the zone's own
    max_level - min_level), clear_all_zone_quests ~= the zone's real Barrens-
    tagged Quest Rewards row count (see Task 2's Step 5 verification output),
    golden_boar_statues ~= zone_leveler_statues_required checks (density-
    sampled, Task 10), instance_clears ~= zone_leveler_instances_required
    checks (0-3 for Barrens)."""
    display_name = "Zone Leveler: Goals"
    valid_keys = frozenset({"reach_zone_level_cap", "clear_all_zone_quests", "golden_boar_statues", "instance_clears"})
    default = valid_keys


class ZoneLevelerStatuesRequired(Range):
    """Only relevant when game_mode is zone_leveler and golden_boar_statues is
    selected in zone_leveler_goals (M4.11.1). How many "Golden Boar Statue"
    items must be received to satisfy that goal. Capped at 20 -- Barrens'
    curated golden_boar_statues.yaml roster size (Task 10); a future zone or a
    widened Barrens roster must widen this range_end to match, same coupling
    KeyHuntKeysRequired's own docstring documents for rares.yaml."""
    display_name = "Zone Leveler: Statues Required"
    range_start = 1
    range_end = 20
    # At the global CheckDensity default of 25, density.predict_sample_size(20
    # rows, weight 100) predicts ceil(20 * 0.25) == 5 -- satisfiable out of the
    # box, same reasoning KeyHuntKeysRequired's own default documents.
    default = 5


class ZoneLevelerInstancesRequired(Range):
    """Only relevant when game_mode is zone_leveler and instance_clears is
    selected in zone_leveler_goals (M4.11.1). How many of the selected zone's
    own curated instances must be cleared -- 0-3 for Barrens (Wailing Caverns,
    Razorfen Kraul, Razorfen Downs; Task 4). 0 makes instance_clears a no-op
    even if selected, matching KeyHuntInstancesRequired's own "0 disables the
    requirement" convention."""
    display_name = "Zone Leveler: Instances Required"
    range_start = 0
    range_end = 3
    default = 1


class ZoneLevelerAllowHubZone(Toggle):
    """Only relevant when game_mode is zone_leveler (M4.11.1). Whether the
    selected zone's curated allowed-hub-zone exception (Durotar/Orgrimmar for
    Barrens) is reachable, in addition to the locked zone itself. Off by
    default -- the zone lock (a new C++ PlayerScript, M4.11.1 Task 14) enforces
    whichever this resolves to."""
    display_name = "Zone Leveler: Allow Hub Zone"
    default = False


class ZoneLevelerContentScope(Choice):
    """Only relevant when game_mode is zone_leveler (M4.11.1). Governs 4
    possession-triggered families -- Itemsanity, Craftsanity, Recipes,
    Trainer Spells -- which fire on pickup/craft/learn regardless of
    physical zone (M4.11.2: Repsanity is NOT one of these; see below).
    "zone_only" (default) excludes all 4 of those families' rows entirely.
    "whole_game_scaled" widens 3 of those 4 -- Itemsanity, Recipes, and
    Trainer Spells -- to any item/recipe/spell whose own real level
    requirement (item_template.RequiredLevel / trainer_spell.ReqLevel)
    falls inside the selected zone's level band, project-wide (Task 12).
    Craftsanity has no real level-requirement data to widen by (crafting is
    skill-tier-gated, not player-level-gated) and stays fully excluded
    under whole_game_scaled too, same as zone_only. Trainer Spells is also
    physically zone-bound (a real trainer NPC must be visited to learn it,
    unlike a mailable Recipe item) -- under whole_game_scaled a row must
    ADDITIONALLY pass its own real trainer-position zone check (the
    selected zone or, when zone_leveler_allow_hub_zone is on, its curated
    hub zones) on top of the level-band check; both axes must pass (Task
    4, M4.11.2). Zone-bound families (Quest Rewards, instance clears) are
    unaffected by this option either way, since the player physically
    cannot leave the locked zone (or its allowed hub zones). Repsanity is
    handled entirely separately from this option (M4.11.2) -- it's not a
    possession-triggered family in the sense above, has no zone or level
    data of its own, and is included under BOTH zone_only and
    whole_game_scaled, unconditionally, whenever its own real `expansion`
    tag is vanilla (a level-band proxy: Barrens' 10-30 band is squarely
    vanilla-era, so a tbc/wotlk reputation faction isn't realistically
    farmable there regardless of literal rank gating)."""
    display_name = "Zone Leveler: Content Scope"
    option_zone_only = 0
    option_whole_game_scaled = 1
    default = 0


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


class AchievementHuntTier(Choice):
    """Only relevant when game_mode is achievement_hunt (M4.9 Sec4). Which of
    the three curated tiers the completion rule requires: hundred_percent
    (every real achievement in the compiled pool -- Feats of Strength/meta-
    achievements and achievements that never fire the completion hook at all
    are already excluded at extraction time, not a runtime choice here),
    ninety_nine_percent (the same pool minus a hand-flagged "extremely hard"
    denylist -- realm-first-adjacent PvP-rating grinds, long reputation-
    exalt chains), or named_subset (exactly one of achievement_hunt_subset's
    six thematic groups). Every achievement location/item in the compiled
    table always exists in the pool regardless of this choice -- only the
    completion RULE differs, the same "every location exists, only the
    threshold differs" shape Collector's collector_items_required already
    established. The connected worldserver must also have
    Archipelago.AchievementHuntTier set to match -- this module has no way
    to read this option from the AP server itself, same manual-sync
    requirement as completionist_expansion. Note: some achievements in the
    pool are faction-exclusive (e.g. "For The Alliance!"/"For The Horde!"
    are both in the 100%/99% pools, but no single character can complete
    both) -- since the completion flag is realm-wide, this is completable
    across multiple characters of both factions on the same realm, not a
    single-character requirement."""
    display_name = "Achievement Hunt: Tier"
    option_hundred_percent = 0
    option_ninety_nine_percent = 1
    option_named_subset = 2
    default = 0


class AchievementHuntSubset(Choice):
    """Only relevant when game_mode is achievement_hunt AND
    achievement_hunt_tier is named_subset. Which of the six real,
    Achievement.dbc-category-derived thematic subsets the completion rule
    requires: explorer (Exploration, real category root 97), dungeons/raids
    (both derived from the real "Dungeons & Raids" category root 168, split
    by each achievement's own leaf-category name containing "Raid" or not),
    professions (root 169), reputation (root 201), pvp (Player vs. Player,
    root 95). The connected worldserver must also have
    Archipelago.AchievementHuntSubset set to match -- same manual-sync
    requirement as achievement_hunt_tier above. Note: the ninety_nine_percent
    tier's "extremely hard" exclusion does NOT apply here -- a named subset
    may still require achievements that would have been excluded under the
    99% tier (e.g. the arena rating-gated achievements in the pvp subset)."""
    display_name = "Achievement Hunt: Named Subset"
    option_explorer = 0
    option_dungeons = 1
    option_raids = 2
    option_professions = 3
    option_reputation = 4
    option_pvp = 5
    default = 0


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
    """When on, Auction House access, Hearthstone use, sending mail, Bank
    access, and gathering (mining/herbalism/skinning, gated as one access
    type) are locked behind Archipelago items instead of being free from
    the start (spec §5.1 -- optional, off by default). All 5 of the
    design's access types are implemented as of M4.9. The connected
    worldserver must also have Archipelago.AccessGating enabled in its
    .conf to match -- same manual-sync requirement as proficiency_gating
    above."""
    display_name = "Access Gating"
    default = False


class CharacterUnlockGating(Toggle):
    """When on, bank bag slots, spending talent points, dual spec, and
    Glyph Slots are locked behind Archipelago items instead of being
    free/purchasable from the start (spec §5.1 -- optional, off by
    default). All four character-unlock types named in the design are
    implemented as of M4.9 (Glyph Slot gating closed the last gap). The
    connected worldserver must also have Archipelago.CharacterUnlockGating
    enabled in its .conf to match -- same manual-sync requirement as the
    other gate toggles."""
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


class HolidaysanityStacking(Toggle):
    """When off (default), activating a new holiday via the Archipelago
    Holiday Herald deactivates whichever holiday is currently running --
    only one holiday active at a time. When on, multiple holidays can run
    simultaneously (design spec §8a)."""
    display_name = "Holidaysanity Stacking"


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


class ContainersanityExpansionPools(OptionSet):
    """Which expansion tiers' containers Containersanity draws locations
    from -- a container is tagged by every expansion where a real
    gameobject spawn of its backing chest template exists (M4.10.1)."""
    display_name = "Containersanity Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class GathersanityExpansionPools(OptionSet):
    """Which expansion tiers' gathering/skinning/disenchant slots
    Gathersanity draws locations from -- a slot is tagged by every
    expansion where a real spawn/source exists (gathering nodes: the
    backing gameobject's real spawn map; skinning: the backing
    creature's real spawn map; disenchant: the real character-level
    range of every source item sharing that bracket) (M4.10.2)."""
    display_name = "Gathersanity Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class GathersanitySourcePools(OptionSet):
    """Which of Gathersanity's six real sources to include. gathering_node
    is mining/herbalism world nodes (gameobject_loot_template). skinning/
    mob_herbalism/mob_mining/mob_engineering are all creature corpse
    interactions via skinning_loot_template, split by the real vanilla
    creature_template.type_flags bit that gates which profession can use
    them (CREATURE_TYPE_FLAG_SKIN_WITH_HERBALISM/_MINING/_ENGINEERING,
    src/server/shared/SharedDefines.h:2697-2704) -- plain skinning is the
    default/no-flag case. disenchant is disenchant_loot_template's real
    item-level-bracket loot slots. Default selects every value (full
    vocabulary, zero-regression) (M4.10.2)."""
    display_name = "Gathersanity Source Pools"
    valid_keys = ["gathering_node", "skinning", "mob_herbalism", "mob_mining", "mob_engineering", "disenchant"]
    default = valid_keys


class EnemysanityTypePools(OptionSet):
    """Which of Enemysanity's two type pools to include -- "regular" is
    every creature_template.rank == 0 (CREATURE_ELITE_NORMAL) species with
    a real spawn; "boss" is every nonzero rank (Elite/RareElite/WorldBoss/
    Rare, SharedDefines.h's CreatureEliteType). Selecting both is this
    dimension's "merge" behavior; selecting one is "separate" (M4.10.3).
    Default selects every value (full vocabulary, zero-regression)."""
    display_name = "Enemysanity Type Pools"
    valid_keys = ["boss", "regular"]
    default = valid_keys


class EnemysanityExpansionPools(OptionSet):
    """Which expansion tiers' species Enemysanity draws locations from -- a
    species is tagged by every expansion where a real spawn exists, across
    both its primary creature.id spawns and any alternate-difficulty
    creature_multispawn entries (M4.10.3). Default selects every value."""
    display_name = "Enemysanity Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class RepsanityExpansionPools(OptionSet):
    """Which expansion tiers' factions Repsanity draws locations from -- a
    faction is tagged by the expansion its reputation was introduced in
    (vanilla/tbc/wotlk), hand-curated against real Faction.dbc data since
    this checkout's faction_dbc SQL mirror carries no expansion field at
    all. Default selects every value (full vocabulary, zero-regression)."""
    display_name = "Repsanity Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class RepsanityRankTierPools(OptionSet):
    """Whether Repsanity includes "standard" rank locations (Neutral through
    Exalted, real for every reputation-tracking faction) and/or "negative"
    rank locations (Hated/Hostile/Unfriendly, real only for the curated
    subset of factions that actually start below Neutral -- see this
    family's extraction script for the real, hand-verified roster). Default
    selects both."""
    display_name = "Repsanity Rank Tier Pools"
    valid_keys = ["standard", "negative"]
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


class CraftsanityProfessionPools(OptionSet):
    """Which professions Craftsanity draws "recipe crafted" locations from --
    a location is tagged by the profession(s) of every recipe/trainer spell
    that produces its item (M4.10.5). Same vocabulary as Learned Recipes'
    RecipeProfessionPools, since Craftsanity's produced-item universe is
    derived from that same spell set."""
    display_name = "Craftsanity Profession Pools"
    valid_keys = RecipeProfessionPools.valid_keys
    default = valid_keys


class CraftsanityExpansionPools(OptionSet):
    """Which expansion tiers' crafted items Craftsanity draws locations from."""
    display_name = "Craftsanity Expansion Pools"
    valid_keys = ["vanilla", "tbc", "wotlk"]
    default = valid_keys


class CraftsanityClassPools(OptionSet):
    """Which class-restricted crafted items Craftsanity draws locations
    from -- real class-trainer-taught crafting spells only exist for mage
    (Conjure Food/Water) and warlock (Create Soulstone/Firestone/Spellstone)
    in this checkout's live data (confirmed empirically, M4.10.5 Task 4);
    scoped to exactly those two, not the full 10-class roster, matching
    the project's own "scope valid_keys to real data" convention (e.g.
    RepsanityRankTierPools, EnemysanityTypePools)."""
    display_name = "Craftsanity Class Pools"
    valid_keys = ["mage", "warlock"]
    default = valid_keys


class ItemsanityClassPools(OptionSet):
    """Which real item_template.class categories Itemsanity draws locations
    from (M4.10.6). Real ItemClass enum values, one tag per item -- unlike
    Gathersanity's source tag, an item's class is always exactly one value,
    never a multi-value union."""
    display_name = "Itemsanity Class Pools"
    valid_keys = [
        "consumable", "container", "weapon", "gem", "armor", "reagent",
        "projectile", "trade_goods", "generic", "recipe", "money",
        "quiver", "quest", "key", "permanent", "misc", "glyph",
    ]
    default = valid_keys


class ItemsanityQualityPools(OptionSet):
    """Which real item_template.Quality tiers Itemsanity draws locations
    from (M4.10.6). Real ItemQualities enum values."""
    display_name = "Itemsanity Quality Pools"
    valid_keys = ["poor", "normal", "uncommon", "rare", "epic", "legendary", "artifact", "heirloom"]
    default = valid_keys


class ItemsanityExpansionPools(OptionSet):
    """Which expansion tiers' items Itemsanity draws locations from -- an
    item is tagged by a RequiredLevel bracket (no direct expansion column
    exists on item_template, unlike every prior family's real spawn-map
    join; see extract_itemsanity.py's _expansion_tag docstring) (M4.10.6)."""
    display_name = "Itemsanity Expansion Pools"
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


class FillerCategoryPools(OptionSet):
    """Which Filler reward categories to include (M4.9.3.1, design spec's
    Filler section). Filler is a generic, reusable reward pool any content
    family with more locations than items can draw from to close its own
    deficit -- core_loop's every-level granularity change (M4.9.3) is the
    first real consumer. 17 categories total: 5 curated reward EFFECTS
    (random_buff/gold_reward/xp_reward/title/portable_service -- new
    delivery mechanisms this milestone built) and 12 real, DB-extracted WoW
    ITEM categories (badge_currency/consumable/bag/
    gear_enhancement/equipment/openable/toy/seasonal/mount/pet/tabard/
    reagent). A pooled filler item's category is EITHER its
    filler_reward_items row's own `category` tag OR its
    filler_reward_effects row's own `effect` field, mapped 1:1 to one of
    these 17 keys by items.py's create_filler_item_pool. Default selects
    every value -- Filler is on by default, matching every other pooled
    optional family in this apworld.

    A "recipe" category existed here through M4.9.3.1 but was removed
    after a whole-branch review found a real location-check-collision
    risk: Filler's recipe rows reused the same real recipe items the
    Recipes family's own location-check trigger uses, and the C++ hook
    that fires those checks (a source-agnostic spell-learn hook) cannot
    tell a Filler-delivered "duplicate" recipe apart from a genuine
    Recipes-family reward -- learning one could silently complete that
    Recipes location outside the normal flow. The category was dropped
    entirely rather than reworked, per explicit user direction; see
    content/filler_reward_items.yaml's regeneration history in the
    sibling module repo."""
    display_name = "Filler Category Pools"
    valid_keys = [
        "random_buff", "gold_reward", "xp_reward", "title", "portable_service",
        "badge_currency", "consumable", "bag", "gear_enhancement",
        "equipment", "openable", "toy", "seasonal", "mount", "pet", "tabard", "reagent",
    ]
    default = valid_keys


class FillerEffectDistributionMode(Choice):
    """Only used when filler_category_pools includes at least one of the 5
    curated reward-effect categories (random_buff/gold_reward/xp_reward/
    title/portable_service, M4.9.6): how each category's own discrete
    value rows (e.g. Gold Reward's 21 copper tiers) get sampled when
    create_filler_item_pool draws from them. "uniform" spreads them as
    evenly as possible; "weighted" uses each row's own relative weight
    (its content-table count field); "chaos" picks each individual copy's
    value independently at random, varying the split generation to
    generation even for identical options. Every row in this family
    currently carries an equal weight of 1 (M4.9.6 has no principled
    per-value rarity signal), so weighted and uniform currently produce
    statistically similar results -- the option still functions correctly
    per its documented semantics and is ready for a future milestone to
    assign differentiated weights. weighted is the default, matching
    trap_distribution_mode's own precedent."""
    display_name = "Filler Effect Distribution Mode"
    option_uniform = 0
    option_weighted = 1
    option_chaos = 2
    default = 1


class LootSlotCheckRepeatBehavior(Choice):
    """What happens when a player re-loots an already-checked
    Containersanity/Gathersanity slot -- real and reachable here (unlike
    VendorCheckRepeatBehavior's now-mostly-dead-code modes, which are
    blocked by vendor's native maxcount=1 stock limit): 20.1% of real
    chest-type gameobjects in this checkout have a nonzero restock timer
    (chestRestockTime), so a genuine repeat-loot of the same slot is a
    real, common scenario, not a corner case."""
    display_name = "Loot Slot Check Repeat Behavior"
    option_suppress_entirely = 0
    option_vanilla_item = 1
    option_gold_conversion = 2
    option_filler_consumable = 3
    default = 0


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
    holidaysanity_stacking: HolidaysanityStacking
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
    key_hunt_zone_pools: KeyHuntZonePools
    zone_leveler_starting_zone: ZoneLevelerStartingZone
    zone_leveler_goals: ZoneLevelerGoals
    zone_leveler_statues_required: ZoneLevelerStatuesRequired
    zone_leveler_instances_required: ZoneLevelerInstancesRequired
    zone_leveler_allow_hub_zone: ZoneLevelerAllowHubZone
    zone_leveler_content_scope: ZoneLevelerContentScope
    artisan_primary_professions_required: ArtisanPrimaryProfessionsRequired
    collector_items_required: CollectorItemsRequired
    achievement_hunt_tier: AchievementHuntTier
    achievement_hunt_subset: AchievementHuntSubset
    quest_reward_type_pools: QuestRewardTypePools
    quest_reward_expansion_pools: QuestRewardExpansionPools
    vendor_stock_expansion_pools: VendorStockExpansionPools
    containersanity_expansion_pools: ContainersanityExpansionPools
    gathersanity_expansion_pools: GathersanityExpansionPools
    gathersanity_source_pools: GathersanitySourcePools
    enemysanity_type_pools: EnemysanityTypePools
    enemysanity_expansion_pools: EnemysanityExpansionPools
    repsanity_expansion_pools: RepsanityExpansionPools
    repsanity_rank_tier_pools: RepsanityRankTierPools
    craftsanity_profession_pools: CraftsanityProfessionPools
    craftsanity_expansion_pools: CraftsanityExpansionPools
    craftsanity_class_pools: CraftsanityClassPools
    itemsanity_class_pools: ItemsanityClassPools
    itemsanity_quality_pools: ItemsanityQualityPools
    itemsanity_expansion_pools: ItemsanityExpansionPools
    quest_reward_weight: QuestRewardWeight
    vendor_stock_weight: VendorStockWeight
    recipe_profession_pools: RecipeProfessionPools
    recipe_expansion_pools: RecipeExpansionPools
    trainer_spell_class_pools: TrainerSpellClassPools
    trainer_spell_expansion_pools: TrainerSpellExpansionPools
    vendor_check_repeat_behavior: VendorCheckRepeatBehavior
    death_knight_slot: DeathKnightSlot
    death_knight_level1_start: DeathKnightLevel1Start
    filler_category_pools: FillerCategoryPools
    filler_effect_distribution_mode: FillerEffectDistributionMode
    loot_slot_check_repeat_behavior: LootSlotCheckRepeatBehavior

