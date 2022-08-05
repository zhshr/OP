from abc import ABC, abstractmethod

from commands.card_message_helper import CardMessageHelper
from game.game_manager import GameManager
from game.global_state import GlobalState
from khl import Bot


class BaseCommands(ABC):
    def __init__(self, bot: Bot, game_manager: GameManager, state: GlobalState, card_message_helper: CardMessageHelper):
        self.bot = bot
        self.game_manager = game_manager
        self.state = state
        self.card_message_helper = card_message_helper

    @classmethod
    def init_and_register(cls, bot, game_manager, state, card_message_helper: CardMessageHelper):
        inst = cls(bot, game_manager, state, card_message_helper)
        inst._register()
        return inst

    @abstractmethod
    def _register(self):
        pass
