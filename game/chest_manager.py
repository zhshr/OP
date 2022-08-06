from dataclasses import dataclass

from dataclasses_json import dataclass_json, LetterCase

from base.config_class import ConfigClass
from game.common import ItemEntry


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Chest:
    items: dict[str, ItemEntry]


class ChestManager(ConfigClass):
    def save_config(self):
        self.config = self.chests
        super().write_config()

    def config_loaded(self):
        for chest in self.config:
            self.chests.append(Chest.from_dict(chest))

    def default_config(self):
        return [
            {
                "items": {}
            }, {
                "items": {}
            }, {
                "items": {}
            }, {
                "items": {}
            }
        ]

    def __init__(self):
        self.chests: list[Chest] = []
        super().__init__('treasure_chests')

    def set_item(self, treasure_level: int, item_id: str, value: int):
        if value == -1:
            self.chests[treasure_level].items.pop(item_id, None)
        else:
            self.chests[treasure_level].items.update({item_id: ItemEntry(value)})
        self.save_config()
