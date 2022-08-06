from game.channel_manager import ChannelManager
from game.chest_manager import ChestManager
from game.player_manager import PlayerState, PlayerManager
from game.role_manager import RoleManager
from khl import Guild


class GlobalState:
    def __init__(self):
        self.guild: Guild | None = None
        self.roles: RoleManager = RoleManager()
        self.channels: ChannelManager = ChannelManager()
        # self.players: list[PlayerState] = [PlayerState(i) for i in range(3)]
        self.players: PlayerManager = PlayerManager()
        self.chests: ChestManager = ChestManager()

