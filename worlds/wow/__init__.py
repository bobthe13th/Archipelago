from worlds.AutoWorld import World
from .items import WoWItem, create_item_pool, create_core_loop_item_pool, create_gates_item_pool, create_trap_item_pool
from .regions import create_regions
from .rules import set_rules
from . import goals
from .content_data import LOCATIONS, ITEMS
from . import core_loop_content_data
from . import gates_content_data
from . import filler_content_data
from . import traps_content_data
from .options import WoWOptions


class WoWWorld(World):
    """
    World of Warcraft: Wrath of the Lich King (3.3.5a) Archipelago
    integration. M2.1: core loop -- level-up and instance-clear locations,
    Progressive Level Cap / Instance Unlocks / Dark Portal / Northrend
    Passage items, Sprint mode (reach level 60) playable end to end.

    Known accepted limitation: Death Knight characters start at level 55
    via a server-side path that bypasses the level-up hook driving the
    "Reach Level N" checks for N in 5..55, so those 11 locations are
    unreachable in actual play for that class (see the extended comment in
    locations.py's create_core_loop_locations). Sprint's completion rule
    only requires collecting all 10 Progressive Level Cap copies, not
    checking any specific location, so the goal remains logically
    reachable for every class; this is tracked as a residual experiential
    risk, not a generation-time error, and is deferred pending a
    class-aware state model (out of scope for M2.1).
    """
    game = "World of Warcraft WotLK"
    options_dataclass = WoWOptions
    options: WoWOptions

    item_name_to_id = {
        **{name: item_id for name, item_id in ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in core_loop_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in gates_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in traps_content_data.ITEMS.items()},
    }
    location_name_to_id = {
        **{name: loc_id for name, loc_id in LOCATIONS.items()},
        **{f"Reach Level {level}": loc_id for level, loc_id in core_loop_content_data.LEVEL_LOCATIONS.items()},
        "Clear Ragefire Chasm": core_loop_content_data.INSTANCE_CLEAR_LOCATIONS["ragefire_chasm"],
        "Clear Deadmines": core_loop_content_data.INSTANCE_CLEAR_LOCATIONS["deadmines"],
        **{name: loc_id for name, loc_id in filler_content_data.LOCATIONS.items()},
    }

    def generate_early(self) -> None:
        # Task 22: a bad game_mode/option combination must fail generation
        # loudly here, before create_regions/create_items/set_rules ever run
        # (spec Sec5.3's "fail generation with a clear message" requirement) --
        # every GameMode value beyond Sprint currently raises OptionError
        # naming which M4 task builds it, until that task lands.
        goals.validate(self)

    def create_regions(self) -> None:
        create_regions(self)

    def create_items(self) -> None:
        self.multiworld.itempool += create_item_pool(self)
        self.multiworld.itempool += create_core_loop_item_pool(self)
        self.multiworld.itempool += create_gates_item_pool(self)
        self.multiworld.itempool += create_trap_item_pool(self)

    def set_rules(self) -> None:
        set_rules(self)
        goals.set_completion_rule_for_mode(self)

