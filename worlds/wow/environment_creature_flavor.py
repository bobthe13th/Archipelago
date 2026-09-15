"""M5.6.3: bundles four independently-toggleable Cosmetic creature traits
into one MutationCategory. See design spec Sec5 and this plan's Global
Constraints for: why equipment targets creature.equipment_id (never
creature_equip_template's composite-keyed rows); why posture/sheath touch
only byte 0 of bytes1/bytes2; why aura draws from a curated whitelist,
never an unfiltered spell range; and why posture/mount/aura merge into one
combined payload per creature_template_addon row when more than one is
enabled together.

Note on creature_template_addon.auras' format: the real column is a
SPACE-separated list of spell IDs, not comma-separated -- confirmed against
the real AzerothCore parser (ObjectMgr.cpp's CreatureAddon load, which
tokenizes this field with `Acore::Tokenize(fields[7].Get<std::string_view>(),
' ', false)`). Any code that reads or writes this field's raw string value
(including future whitelist-curation work) must split/join on a single
space, never a comma -- a comma-joined value would fail to parse as
multiple aura IDs at boot and would silently be treated as unparseable by
AzerothCore's tokenizer.

Note on aura shuffle's ADD-only semantics: candidate_rows() only ever
offers the auras/_aura_mode payload keys for a creature_template_addon row
whose EXISTING auras value is already empty ("") -- mutate() therefore only
ever ADDS a cosmetic aura, it never overwrites or removes a real,
possibly-mechanical aura a creature already has (WotLK data uses this
column for things like permanent stealth, invisibility, detection, or
feign-death). The curated whitelist guards against ASSIGNING a mechanical
aura; this constraint guards the symmetric risk of REMOVING one that was
already safely doing its job. A row with a non-empty existing auras value
can still be a candidate for the OTHER three fields (equipment/posture/
mount) -- only the auras field itself is excluded for that row.

Note on interaction with mobs_spawns.py's mob_randomizer_spawn_mode
(M5.1.0, a separate already-shipped milestone): when spawn shuffle is also
enabled, a spawn's underlying creature template can change, which
invalidates the same-id1-grouping safety property this milestone's
equipment shuffle depends on -- equipment_id was grouped and validated
against the spawn's ORIGINAL template, but if spawn shuffle also reassigns
which template occupies that spawn, the equipment_id now resolves against
a different template than the one it was grouped/validated against at
generation time. This is an accepted tradeoff between two Cosmetic-
classified categories interacting, not a bug to fix.
"""
from __future__ import annotations

import random
from typing import Sequence

from . import creature_flavor_content_data
from . import mutation_pipeline

# Empty by design until a human curates real, verified visual-only
# (non-mechanical) spell IDs into this list -- see this plan's Global
# Constraints and docs/testing/m5.6.3-manual-verification-checklist.md's
# curation step. mutate() safely no-ops on aura reassignment whenever this
# is empty, regardless of whether EnvironmentRandomizerAuraEnabled is on.
_COSMETIC_AURA_WHITELIST: tuple[int, ...] = ()


def _extract_byte0(value: int) -> int:
    return value & 0xFF


def _replace_byte0(value: int, new_byte0: int) -> int:
    return (value & 0xFFFFFF00) | (new_byte0 & 0xFF)


def candidate_rows(world) -> list:
    equipment_on = world.options.environment_randomizer_equipment_enabled.value
    posture_on = world.options.environment_randomizer_posture_enabled.value
    mount_on = world.options.environment_randomizer_mount_enabled.value
    aura_on = world.options.environment_randomizer_aura_enabled.value

    rows = []

    if equipment_on:
        for guid, data in creature_flavor_content_data.CREATURE_EQUIPMENT.items():
            rows.append(("creature", guid, {
                "id1": data["id1"], "equipment_id": data["equipment_id"], "_field": "equipment",
            }))

    if posture_on or mount_on or aura_on:
        for entry, data in creature_flavor_content_data.CREATURE_ADDONS.items():
            payload = {}
            if posture_on:
                payload["bytes1"] = data["bytes1"]
                payload["bytes2"] = data["bytes2"]
                payload["emote"] = data["emote"]
                payload["_posture_mode"] = "shuffle"
            if mount_on:
                payload["mount"] = data["mount"]
                payload["_mount_mode"] = "shuffle"
            if aura_on and data["auras"] == "":
                # Only ever ADD a cosmetic aura to a row that has none --
                # never overwrite/remove a real, possibly-mechanical aura
                # a creature already has (see module docstring).
                payload["auras"] = data["auras"]
                payload["_aura_mode"] = "shuffle"
            rows.append(("creature_template_addon", entry, payload))

    return rows


def mutate(rows: Sequence, rng: random.Random) -> list:
    equipment_rows = [(t, k, p) for t, k, p in rows if p.get("_field") == "equipment"]
    addon_rows = [(t, k, p) for t, k, p in rows if t == "creature_template_addon"]

    result = []

    if equipment_rows:
        groups: dict[int, list] = {}
        for table, guid, payload in equipment_rows:
            groups.setdefault(payload["id1"], []).append((table, guid, payload))
        for group_rows in groups.values():
            original_ids = [p["equipment_id"] for _t, _g, p in group_rows]
            shuffled_ids = list(original_ids)
            rng.shuffle(shuffled_ids)
            for (table, guid, payload), new_id in zip(group_rows, shuffled_ids):
                if new_id != payload["equipment_id"]:
                    result.append((table, guid, {"equipment_id": new_id}))

    if addon_rows:
        posture_candidates = [(t, k, p) for t, k, p in addon_rows if "_posture_mode" in p]
        if posture_candidates:
            byte1_pool = [_extract_byte0(p["bytes1"]) for _t, _k, p in posture_candidates]
            byte2_pool = [_extract_byte0(p.get("bytes2", 0)) for _t, _k, p in posture_candidates]
            emote_pool = [p.get("emote", 0) for _t, _k, p in posture_candidates]
            rng.shuffle(byte1_pool)
            rng.shuffle(byte2_pool)
            rng.shuffle(emote_pool)

        mount_candidates = [(t, k, p) for t, k, p in addon_rows if "_mount_mode" in p]
        if mount_candidates:
            mount_pool = [p["mount"] for _t, _k, p in mount_candidates]
            rng.shuffle(mount_pool)

        aura_candidates = [(t, k, p) for t, k, p in addon_rows if "_aura_mode" in p]

        posture_idx = mount_idx = 0
        merged: dict[tuple, dict] = {}
        for table, entry, payload in addon_rows:
            new_payload = merged.setdefault((table, entry), {})
            if "_posture_mode" in payload:
                new_byte1 = _replace_byte0(payload["bytes1"], byte1_pool[posture_idx])
                new_byte2 = _replace_byte0(payload.get("bytes2", 0), byte2_pool[posture_idx])
                new_emote = emote_pool[posture_idx]
                posture_idx += 1
                if new_byte1 != payload["bytes1"]:
                    new_payload["bytes1"] = new_byte1
                if new_byte2 != payload.get("bytes2", 0):
                    new_payload["bytes2"] = new_byte2
                if new_emote != payload.get("emote", 0):
                    new_payload["emote"] = new_emote
            if "_mount_mode" in payload:
                new_mount = mount_pool[mount_idx]
                mount_idx += 1
                if new_mount != payload["mount"]:
                    new_payload["mount"] = new_mount
            if "_aura_mode" in payload and _COSMETIC_AURA_WHITELIST:
                new_aura = str(rng.choice(_COSMETIC_AURA_WHITELIST))
                if new_aura != payload["auras"]:
                    new_payload["auras"] = new_aura

        for (table, entry), new_payload in merged.items():
            if new_payload:
                result.append((table, entry, new_payload))

    return result


mutation_pipeline.register_category(
    mutation_pipeline.MutationCategory(
        key="environment_creature_flavor", candidate_rows=candidate_rows, mutate=mutate, invariant_rules=[],
    )
)
