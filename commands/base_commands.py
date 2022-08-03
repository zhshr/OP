from game.game_manager import GameManager
from game.global_state import GlobalState
from khl import Bot


class BaseCommands:
    def __init__(self, bot: Bot, game_manager: GameManager, state:GlobalState):
        self.bot = bot
        self.game_manager = game_manager
        self.state = state
