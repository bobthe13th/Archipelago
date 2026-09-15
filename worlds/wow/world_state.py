# Archipelago/worlds/wow/world_state.py
"""The single point of contact between Pipeline A's logic generation and
Pipeline B's world mutation (M5, not yet built). Pipeline A's rule-generation
code (rules.py, goals.py) reads species_expansion_tags() and NEVER branches
on whether Pipeline B ran -- it always gets a valid mapping, vanilla by
default.

Ships as part of M4.12 (design spec
docs/superpowers/specs/2026-08-24-archipelago-wow-m4.12-pipeline-interface-design.md),
whose own §3 sketches this as a raw creature_entry->zone_id map. This
implementation deviates deliberately: the only data this project's real
extraction actually produces is an expansion-tag set per species
(enemysanity_content_data.TAGS, M4.10.3), which is also the exact
granularity the project's one real, shipped precedent for this kind of gate
already uses (Fishing Quest's Northrend-catch rule, rules.py's
NORTHREND_LOCATION_NAMES loop). See M4.12's plan doc, "Real corrections",
for the full reasoning -- in short, a raw zone_id map would either invent
data no extraction script produces, or hand-duplicate enemysanity_content_data's
own real, compiler-generated facts into a second, drift-prone copy.
"""
from __future__ import annotations

from . import enemysanity_content_data

# Real data, sourced from enemysanity_content_data.TAGS/.TRIGGERS
# (compiler-generated from content/enemysanity.yaml's live DB extraction,
# M4.10.3) -- re-keyed here from location name to the real creature_entry
# integer, since that's the natural key for anything gating on a specific
# species (Pipeline A's rules.py, and Pipeline B's eventual mutation
# output). NOT a second hand-curated dataset -- see this module's own
# docstring above and M4.12's plan doc for why that would be wrong here,
# unlike APTraps.cpp's SPHERE_ZERO_ZONE_ID (one well-known, unchanging
# constant, an appropriate case for hardcoding).
_VANILLA_SPECIES_EXPANSION_TAGS: dict[int, frozenset[str]] = {
    trigger["creature_entry"]: enemysanity_content_data.TAGS[name]["expansion"]
    for name, trigger in enemysanity_content_data.TRIGGERS.items()
}


def species_expansion_tags(world) -> dict[int, frozenset[str]]:
    """Returns creature_entry -> frozenset of real expansion tags
    ({"vanilla"}, {"wotlk"}, {"vanilla", "wotlk"}, etc.) for this seed.

    If Pipeline B (M5) has written a mutated mapping onto `world`
    (world.pipeline_b_species_expansion_tags, set during Pipeline B's own
    generate_early step -- BEFORE Pipeline A's set_rules runs, per the
    AP-standard generate_early -> create_regions -> create_items ->
    set_rules -> generate_basic ordering this apworld's __init__.py already
    follows), that mapping is returned instead of the vanilla default.
    Pipeline A's callers (rules.py) never check which case applies -- they
    just call this function.

    Contract for Pipeline B (M5, not built here): if you move a creature
    entry to spawn in a different expansion's zones, write the corrected
    entry -> frozenset(expansion tags) into
    world.pipeline_b_species_expansion_tags for every entry you touch
    before set_rules runs, and -- per the base design spec's own §4
    reachability obligation -- re-verify at generation time that every
    location gated on the OLD tags (rules.py's Enemysanity zone-access
    rule, and any future consumer of this function) is still reachable
    under the NEW assignment for this seed, failing generation with a
    clear OptionError if not (the same discipline _validate_key_hunt
    already established for an unsatisfiable option combination -- see
    rules.py/goals.py). This module does not implement that
    re-verification pass itself; it is Pipeline B's own obligation to
    satisfy when M5 builds it (design spec §4, explicitly out of scope for
    M4.12).
    """
    return getattr(world, "pipeline_b_species_expansion_tags", _VANILLA_SPECIES_EXPANSION_TAGS)
