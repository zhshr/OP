from base.config_class import ConfigClass
from game.global_state import GlobalState


class ManagerWithState(ConfigClass):

    def __init__(self, global_state: GlobalState):
        super().__init__()
        self.state = global_state
