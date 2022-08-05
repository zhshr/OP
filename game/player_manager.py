from dataclasses import dataclass
from typing import Union

from dataclasses_json import dataclass_json
from base.config_class import ConfigClass
from database import item_library


@dataclass_json
@dataclass
class ItemEntry:
    count: int


@dataclass_json
@dataclass
class PlayerState:
    player_index: int
    name: str
    attr: dict
    items: dict[str, ItemEntry]

    # def __init__(self, index: int):
    #     self.player_index = index
    #     self.name = chr(ord('A') + index)
    #     self.attr = {}
    #     self.items: dict[int, ItemEntry] = {}

    def change_attr(self, attr: str, value: int, max: int):
        factor = 1
        attr = attr.lower()
        prev = self.attr[attr]
        if attr in ["atk", "def"]:
            factor = 2
        if value > 0:
            if value * factor > self.attr['sp']:
                return "属性点不足，需要{0} 现有{1}".format(value * factor, self.attr['sp'])
            elif self.attr[attr] + value > max:
                return "将超出属性上限，{0} -> {1} > {2}".format(prev, prev + value, max)
        if value < 0:
            if value + self.attr[attr] < 0:
                return "属性不能为负，现{0}".format(prev)

        self.attr[attr] += value
        prev_sp = self.attr['sp']
        self.attr['sp'] -= value * factor
        return "加点成功，{0} {1} -> {2}，SP {3} -> {4}".format(attr, prev, self.attr[attr], prev_sp, self.attr['sp'])


    def change_attr2(self, attr: str, value: int,max:int):
        
        prev = self.attr[attr]
        
        self.attr[attr] = value

        return "更改成功，{0}{1} ->{2} ".format(attr,prev,self.attr[attr])

    def change_state(self, state: str, value: int):
        if state.lower() == 'hp':
            prev = self.attr['hp']
            new = prev + value
            if new < 0:
                return "操作失败"
            if new > self.attr['maxhp']:
                new = self.attr['maxhp']
            self.attr['hp'] = new
            return "SP: {0} -> {1}".format(prev, new)
        elif state.lower() == 'ap':
            prev = self.attr['ap']
            new = prev + value
            if new < 0:
                return "操作失败"
            if new > self.attr['maxap']:
                new = self.attr['maxap']
            self.attr['ap'] = new
            return "AP: {0} -> {1}".format(prev, new)
        elif state.lower() == 'sp':
            prev = self.attr['sp']
            new = prev + value
            if new < 0:
                return "操作失败"
            self.attr['sp'] = new
            return "SP: {0} -> {1}".format(prev, new)


class PlayerManager(ConfigClass):
    def default_config(self):
        default_values = {
            'maxhp': {'default': 100, 'max': 150},
            'maxap': {'default': 100, 'max': 150},
            'atk': {'default': 50, 'max': 80},
            'def': {'default': 50, 'max': 80},
            'crt': {'default': 0, 'max': 50},
            'erc': {'default': 0, 'max': 50},
            'ele': {'default': 0, 'max': 50},
            'sp': {'default': 50, 'max': 999},
        }

        player_default_attr = {k.lower(): v.get('default') for (k, v) in default_values.items()}
        player_default_attr.update({'hp': default_values["maxhp"]['default'],
                                    'ap': default_values["maxap"]['default']})

        def get_state(i: int):
            player_state = {
                'player_index': i,
                'name': chr(ord('A') + i),
                'attr': player_default_attr.copy(),
                'items': {}
            }
            return player_state

        player_count = 7
        players = [get_state(i) for i in range(player_count)]
        return {
            'attributes': default_values,
            'players': players
        }

    def config_loaded(self):
        # for player in self.config['players']:
        #     state = PlayerState(player['player_index'])
        #     state.attr = player['attr']
        #     state.name = player['name']
        #     self.player_state.append(state)
        for v in self.config['players']:
            self.player_state.append(PlayerState.from_dict(v))

    def save_config(self):
        self.config['players'] = self.player_state
        super().write_config()

    def __init__(self):
        self.player_state: list[PlayerState] = []
        super().__init__()

    def change_attr(self, player_index: int, attr: str, value: int):
        if attr.lower() not in self.config['attributes']:
            return "属性不存在"
        result = self.player_state[player_index].change_attr(attr, value,
                                                             self.config['attributes'][attr.lower()]['max'])
        self.save_config()
        return result

    def change_attr2(self, player_index: int, attr: str, value: int):
        if attr.lower() not in self.config['attributes']:
            return "属性不存在"
        result = self.player_state[player_index].change_attr2(attr, value,
                                                             self.config['attributes'][attr.lower()]['max'])
        self.save_config()
        return result

 
    def get_index(self, name: str):
        for state in self.player_state:
            if state.name == name:
                return state.player_index
        return -1

    def add_item_to_player(self, player_index: int, item_id: int, count: int = 1):
        try:
            state = self.player_state[player_index]
            count = int(count)
            item_id = str(item_id)
            if item_id in state.items:
                state.items.get(item_id).count += count
                return state.items.get(item_id).count
            else:
                state.items.update({item_id: ItemEntry(count)})
                return count
        finally:
            self.save_config()
