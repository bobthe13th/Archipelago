# Archipelago/worlds/wow/__init__.py
from worlds.AutoWorld import World
from .items import WoWItem, create_item_pool
from .regions import create_regions
from .rules import set_rules
from .content_data import LOCATIONS, ITEMS


class WoWWorld(World):
    """
    World of Warcraft: Wrath of the Lich King (3.3.5a) Archipelago
    integration. M2: persistent connection, curated Northshire/Goldshire
    quest-line content (19 locations, 19 items), 1:1 fill.
    """
    game = "World of Warcraft WotLK"
    item_name_to_id = {name: item_id for name, item_id in ITEMS.items()}
    location_name_to_id = {name: loc_id for name, loc_id in LOCATIONS.items()}

    def create_regions(self) -> None:
        create_regions(self)

    def create_items(self) -> None:
        self.multiworld.itempool += create_item_pool(self)

    def set_rules(self) -> None:
        set_rules(self)
