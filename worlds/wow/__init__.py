from worlds.AutoWorld import World
from .items import WoWItem, create_core_loop_item_pool, create_gates_item_pool, create_holidaysanity_item_pool, create_trap_item_pool, create_key_hunt_item_pool, create_golden_boar_statues_item_pool, create_fish_item_pool, create_professions_item_pool, create_collections_item_pool, create_optional_category_item_pool, create_achievements_item_pool, create_explorer_item_pool
from .regions import create_regions
from .rules import set_rules
from . import goals
from . import slot_data
from . import achievements_content_data
from . import collections_content_data
from . import containersanity_content_data
from . import core_loop_content_data
from . import craftsanity_content_data
from . import fish_content_data
from . import filler_reward_effects_content_data
from . import filler_reward_items_content_data
from . import enemysanity_content_data
from . import gates_content_data
from . import gathersanity_content_data
from . import golden_boar_statues_content_data
from . import holidaysanity_content_data
from . import itemsanity_content_data
from . import filler_content_data
from . import professions_content_data
from . import quest_rewards_content_data
from . import rares_content_data
from . import recipes_content_data
from . import repsanity_content_data
from . import traps_content_data
from . import trainer_spells_content_data
from . import vendor_stock_content_data
from .options import WoWOptions


class WoWWorld(World):
    """
    World of Warcraft: Wrath of the Lich King (3.3.5a) Archipelago
    integration. M2.1: core loop -- level-up and instance-clear locations,
    Progressive Level Cap / Instance Unlocks / Dark Portal / Northrend
    Passage items, Sprint mode (reach level 60) playable end to end.

    M4.9 update: the Death Knight reachability gap this docstring used to
    describe here is now resolved via a two-track split (core_loop.yaml's
    "standard"/"death_knight" level-milestone tracks, gated by the
    death_knight_slot option) -- see locations.py's
    create_core_loop_locations for the real mechanism and its own
    trust-model caveat (nothing enforces that a death_knight_slot=True
    player actually plays a Death Knight in-game).
    """
    game = "World of Warcraft WotLK"
    options_dataclass = WoWOptions
    options: WoWOptions

    item_name_to_id = {
        **{name: item_id for name, (item_id, _count) in core_loop_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in gates_content_data.ITEMS.items()},
        # M4.10.7 final review fix (C1): Holidaysanity is architecturally
        # identical to gates (realm-state flag items, no locations of its
        # own -- holidaysanity_content_data exports ITEMS only), so it
        # belongs right here next to gates. create_holidaysanity_item_pool
        # was already wired into create_items below, but without this line
        # the 14 Holiday Unlock items (831000-831013) never entered the
        # datapackage's name->id map, so nothing (server, client, tracker)
        # could resolve them.
        **{name: item_id for name, (item_id, _count) in holidaysanity_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in traps_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in rares_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in golden_boar_statues_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in fish_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in professions_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in collections_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in achievements_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in quest_rewards_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in recipes_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in trainer_spells_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in vendor_stock_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in filler_reward_items_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in filler_reward_effects_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in containersanity_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in craftsanity_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in gathersanity_content_data.ITEMS.items()},
        **{name: item_id for name, (item_id, _count) in itemsanity_content_data.ITEMS.items()},
    }
    location_name_to_id = {
        # M4.9: this class attribute is AP's GLOBAL location namespace for
        # this game (used once per game class to build the datapackage),
        # not a per-slot list -- it must include BOTH tracks' "Reach Level
        # N" locations regardless of any single generation's
        # death_knight_slot value, the same way quest_rewards_content_data's
        # full LOCATIONS dict is included here regardless of per-slot
        # tag/weight sampling.
        **{
            core_loop_content_data.LEVEL_LOCATION_NAMES_BY_TRACK[track][level]: loc_id
            for track, levels in core_loop_content_data.LEVEL_LOCATIONS_BY_TRACK.items()
            for level, loc_id in levels.items()
        },
        **{
            core_loop_content_data.INSTANCE_CLEAR_LOCATION_NAMES[instance_key]: loc_id
            for instance_key, loc_id in core_loop_content_data.INSTANCE_CLEAR_LOCATIONS.items()
        },
        **{name: loc_id for name, loc_id in filler_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in rares_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in golden_boar_statues_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in fish_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in professions_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in collections_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in achievements_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in quest_rewards_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in recipes_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in trainer_spells_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in vendor_stock_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in containersanity_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in craftsanity_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in gathersanity_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in enemysanity_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in repsanity_content_data.LOCATIONS.items()},
        **{name: loc_id for name, loc_id in itemsanity_content_data.LOCATIONS.items()},
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
        self.multiworld.itempool += create_core_loop_item_pool(self)
        self.multiworld.itempool += create_gates_item_pool(self)
        self.multiworld.itempool += create_holidaysanity_item_pool(self)
        self.multiworld.itempool += create_trap_item_pool(self)
        self.multiworld.itempool += create_key_hunt_item_pool(self)
        self.multiworld.itempool += create_golden_boar_statues_item_pool(self)
        self.multiworld.itempool += create_fish_item_pool(self)
        self.multiworld.itempool += create_professions_item_pool(self)
        self.multiworld.itempool += create_collections_item_pool(self)
        self.multiworld.itempool += create_achievements_item_pool(self)
        self.multiworld.itempool += create_explorer_item_pool(self)
        self.multiworld.itempool += create_optional_category_item_pool(self)

    def set_rules(self) -> None:
        set_rules(self)
        goals.set_completion_rule_for_mode(self)

    def fill_slot_data(self):
        return slot_data.build_slot_data(self)

