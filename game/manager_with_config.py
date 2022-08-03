from game.base_manager import BaseManager
from game.global_state import GlobalState


class ManagerWithState(BaseManager):

    def __init__(self, global_state: GlobalState):
        super().__init__()
        self.state = global_state
