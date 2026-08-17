# Archipelago/worlds/wow/options.py
from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions


class GameMode(Choice):
    """Which game mode to generate for. Sprint (reach level 60) is the only
    mode implemented so far -- the spec's other modes (Key Hunt, Classic,
    Burning Crusade, Wrath, Completionist, Artisan, Collector, Achievement
    Hunt) are explicitly Milestone 4 scope."""
    display_name = "Game Mode"
    option_sprint = 0
    default = 0


@dataclass
class WoWOptions(PerGameCommonOptions):
    game_mode: GameMode
