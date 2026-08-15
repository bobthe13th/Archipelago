# Archipelago/worlds/wow/__init__.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from BaseClasses import Item, ItemClassification, Location, Region
from Options import PerGameCommonOptions
from worlds.AutoWorld import WebWorld, World

ITEM_NAME_TO_ID: Dict[str, int] = {
    "Progressive Level Cap": 0xAC0000,
}

LOCATION_NAME_TO_ID: Dict[str, int] = {
    "Azeroth: Reach Level 2": 0xAC0000,
}


@dataclass
class WoWOptions(PerGameCommonOptions):
    pass


class WoWItem(Item):
    game = "World of Warcraft WotLK"


class WoWLocation(Location):
    game = "World of Warcraft WotLK"


class WoWWebWorld(WebWorld):
    theme = "grass"


class WoWWorld(World):
    """A multiworld integration for World of Warcraft: Wrath of the Lich King (3.3.5a) on AzerothCore."""

    game = "World of Warcraft WotLK"
    web = WoWWebWorld()
    options_dataclass = WoWOptions
    options: WoWOptions

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        azeroth = Region("Azeroth", self.player, self.multiworld)
        self.multiworld.regions += [menu, azeroth]

        menu.connect(azeroth, "Menu to Azeroth")
        azeroth.add_locations(
            {"Azeroth: Reach Level 2": LOCATION_NAME_TO_ID["Azeroth: Reach Level 2"]}, WoWLocation
        )

    def create_items(self) -> None:
        self.multiworld.itempool.append(self.create_item("Progressive Level Cap"))

    def create_item(self, name: str) -> WoWItem:
        return WoWItem(name, ItemClassification.progression, ITEM_NAME_TO_ID[name], self.player)

    def set_rules(self) -> None:
        self.set_completion_rule(lambda state: state.has("Progressive Level Cap", self.player))
