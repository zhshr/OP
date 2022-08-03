import random

from commands.authenticator import Authenticated, AllowedUsers, AuthUser
from commands.base_commands import BaseCommands
from game.role_manager import RoleTypes
from khl import Message
from khl.command import Command


class PlayerCommands(BaseCommands):
    def __init__(self, bot, game_manager, state):
        super().__init__(bot, game_manager, state)

    @classmethod
    def init_and_register(cls, bot, game_manager, state):
        inst = cls(bot, game_manager, state)
        inst._register()
        return inst

    def _register(self):
        random.seed()
        self.bot.command.add(Command.command(name='state', )(self.get_player_state))
        self.bot.command.add(Command.command(name='add')(self.add_attr))

    @Authenticated(allowed_user=[AllowedUsers.PLAYER_IN_SINGLE_CHANNEL])
    async def get_player_state(self, msg: Message, *, auth: AuthUser):
        await msg.reply(
            "\n".join(["{0}: {1}".format(k, v) for (k, v) in
                       self.state.players.player_state[auth.player_index()].attr.items()]))

    @Authenticated(allowed_user=[AllowedUsers.PLAYER_IN_SINGLE_CHANNEL])
    async def add_attr(self, msg: Message, attr: str, value: int, *, auth: AuthUser):
        value = int(value)
        if value <= 0:
            await msg.reply("加点须大于0")
            return
        attr = attr.lower()
        if attr in ['hp', 'ap', 'sp']:
            await msg.reply("此属性只能由KP操作")
            return
        await msg.reply(self.state.players.change_attr(auth.player_index(), attr, value))
