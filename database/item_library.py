from dataclasses import dataclass
from enum import IntEnum
from typing import Union

from dataclasses_json import dataclass_json

from base.config_class import ConfigClass


class ItemType(IntEnum):
    ITEM = 1,
    EQUIPMENT3 = 2,
    EQUIPMENT4 = 3
    ARTIFACT = 4,
    MAT_GATHER = 5,
    MAT_DROP = 6,
    MAT_BOSS_DROP = 7,
    OTHER = 999

    @property
    def display_name(self):
        match self:
            case ItemType.ITEM:
                return "道具"
            case ItemType.EQUIPMENT3:
                return "三星装备"
            case ItemType.EQUIPMENT4:
                return "四星装备"
            case ItemType.ARTIFACT:
                return "圣遗物"
            case ItemType.MAT_GATHER:
                return "采集素材"
            case ItemType.MAT_DROP:
                return "怪物素材"
            case ItemType.MAT_BOSS_DROP:
                return "首领素材"


@dataclass_json
@dataclass
class Item:
    name: str
    desc: str
    type: ItemType


class ItemLibrary(ConfigClass):
    def save_config(self):
        self.config['metadata'] = self.item_map
        super().write_config()

    def config_loaded(self):
        for item_id, item in self.config['metadata'].items():
            self.item_map.update({item_id: Item.from_dict(item)})

    def default_config(self):
        return {
        }

    def __init__(self):
        self.item_map: dict[int, Item] = {}
        super().__init__(config_name="items")

    def add_item(self, item: Item) -> int:
        new_id = int(max([int(k) for k in self.item_map.keys()], default=-1)) + 1
        self.item_map.update({str(new_id): item})
        self.save_config()
        return new_id

    def get_item(self, item_name_or_id: Union[str, int]) -> [int, Item]:
        if isinstance(item_name_or_id, str) and not item_name_or_id.isdigit():
            return self.get_item_by_name(item_name_or_id)
        else:
            return self.get_item_by_id(item_name_or_id)

    def get_item_by_name(self, name: str) -> [int, Item]:
        for item_id, item in self.item_map.items():
            if item.name == name:
                return item_id, item

        return -1, None

    def get_item_by_id(self, item_id: int) -> [int, Item]:
        if item_id in self.item_map:
            return item_id, self.item_map.get(item_id)
        else:
            return -1, None

    def get_all_by_type(self, item_type: ItemType) -> dict[int, Item]:
        return {k: v for k, v in self.item_map.items() if v.type == item_type}


_item_library = None


def instance() -> ItemLibrary:
    global _item_library
    if _item_library is None:
        _item_library = ItemLibrary()
    return _item_library
