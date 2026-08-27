# GENERATED FILE - do not edit by hand.
# Regenerate with: python modules/archipelago_wow/tools/generate_content.py content/filler_reward_effects.yaml


ITEMS: dict[str, tuple[int, int]] = {
    "Filler: Random Buff": (8500000, 30),
    "Filler: Gold Reward": (8500001, 30),
    "Filler: XP Reward": (8500002, 30),
    "Filler: Character Title": (8500003, 30),
    "Filler: Portable Service": (8500004, 30),
}

EFFECT_BY_ITEM_NAME: dict[str, str] = {
    "Filler: Random Buff": "cast_spell",
    "Filler: Gold Reward": "grant_money",
    "Filler: XP Reward": "grant_xp_percent",
    "Filler: Character Title": "grant_title",
    "Filler: Portable Service": "portable_service",
}
