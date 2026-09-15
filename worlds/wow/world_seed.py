"""M5.0 Sec2/Sec3: world_seed derivation shared by every Pipeline B
mutation category. Pure functions -- no World/multiworld dependency -- so
mutation_pipeline.py's driver, slot_data.py's provenance value, and this
file's own tests all derive the exact same value independently."""
from __future__ import annotations

import hashlib


def derive_world_seed(multiworld_seed: str, slot_name: str) -> str:
    return hashlib.sha256(f"{multiworld_seed}:{slot_name}".encode()).hexdigest()


def derive_sub_seed(world_seed: str, category_key: str, attempt: int) -> str:
    return hashlib.sha256(f"{world_seed}:{category_key}:{attempt}".encode()).hexdigest()
