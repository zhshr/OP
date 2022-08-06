import logging
from enum import IntEnum

from base.config_class import ConfigClass
from khl import Role


class RoleTypes(IntEnum):
    OTHER = 0,
    KP = 1,
    PLAYER = 2,
    DEV = 3,
    ADMIN = 4,


class RoleManager(ConfigClass):

    def default_config(self):
        return {
            'role_ids': {
                'KP': [],
                'Player': []
            }
        }

    def config_loaded(self):
        pass

    def save_config(self):
        pass

    def __init__(self):
        super().__init__()
        self.roles: dict[int, Role] = {}

    def set_roles(self, roles: list[Role], ):
        self.roles.update({role.id: role for role in roles})
        logging.info([role.name for role in roles])
        logging.info(self.roles)

    def get_kp_role(self):
        for role in self.roles.values():
            if 'kp' in role.name.lower():
                return role

    def get_everyone_role(self):
        for role in self.roles.values():
            if '@全体用户' == role.name.lower():
                return role

    def get_player_role(self, name: str):
        for role in self.roles.values():
            if name == role.name:
                return role

    def get_role(self, role_id: int):
        if role_id not in self.roles:
            return None
        return self.roles[role_id]

    def get_role_type(self, role_id: int) -> RoleTypes:
        role = self.roles.get(role_id)
        if role_id in self.config['role_ids']['KP']:
            return RoleTypes.KP
        elif role_id in self.config['role_ids']['Player']:
            return RoleTypes.PLAYER
        elif role_id in self.config['role_ids']['Dev']:
            return RoleTypes.DEV
        elif role_id in self.config['role_ids']['Admin']:
            return RoleTypes.ADMIN
        else:
            return RoleTypes.OTHER

    def get_player_index(self, role_id: int) -> int:
        pl_list: list[int] = self.config['role_ids']['Player']
        try:
            return pl_list.index(role_id)
        except ValueError:
            return -1

