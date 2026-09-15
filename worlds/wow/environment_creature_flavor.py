"""M5.6.3: bundles four independently-toggleable Cosmetic creature traits
into one MutationCategory. See design spec Sec5 and this plan's Global
Constraints for: why equipment targets creature.equipment_id (never
creature_equip_template's composite-keyed rows); why posture/sheath touch
only byte 0 of bytes1/bytes2; why aura draws from a curated whitelist,
never an unfiltered spell range; and why posture/mount/aura merge into one
combined payload per creature_template_addon row when more than one is
enabled together."""
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
