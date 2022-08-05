import random

from commands import CardMessageHelper
from commands.authenticator import Authenticated, AllowedUsers
from commands.base_commands import BaseCommands
from game import channel_manager
from game.game_manager import GameManager
from game.global_state import GlobalState
from game.utils import ChannelUtils
from khl import Message, Bot, ChannelTypes, MessageTypes
from khl.command import Command


class RoomCommands(BaseCommands):
    def __init__(self, bot: Bot, game_manager: GameManager, state: GlobalState, card_message_helper: CardMessageHelper):
        super().__init__(bot, game_manager, state, card_message_helper)

    def _register(self):
        self.bot.command.add(Command.command(name='setchat', )(self.create_private_room))
        self.bot.command.add(Command.command(name='endchat')(self.close_private_room))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[channel_manager.ChannelTypes.BOT_CONTROL])
    async def create_private_room(self, msg: Message, *params: str):
        channel_name = '玩家对话区#{0}'.format(random.randint(10000, 99999))
        player_indice = [self.state.players.get_index(name) for name in params]
        channel = await self.game_manager.create_channel(
            channel_name, ChannelTypes.TEXT, self.state.channels.get_private_room_category())
        self.state.channels.add(channel, {'start': self.game_manager.turn, 'players': params,
                                          'type': channel_manager.ChannelTypes.PLAYER_SHARED})
        await ChannelUtils.set_to_players_only(channel, self.state.roles, [param for param in params])
        channels = await self.state.channels.fetch_channel_map(self.state.guild)
        for param in params:
            for player in self.state.players.player_state:
                if player.name == param:
                    player_channel_id = self.state.channels.get_player_private_channel_id(player.player_index)
                    await self.bot.send(channels[player_channel_id], "new channel: (chn){0}(chn)".format(channel.id),
                                        type=MessageTypes.KMD)

    @Authenticated(allowed_user=[AllowedUsers.KP])
    async def close_private_room(self, msg: Message):
        channel = msg.ctx.channel
        metadata = self.state.channels.metadata.get(channel.id)
        new_name = "{0}T - {1}T: {2}".format(metadata['start'], self.game_manager.turn,
                                             ' '.join(metadata['players']))
        await self.bot.update_channel(channel.id, new_name)
        metadata['name'] = new_name
        metadata['type'] = channel_manager.ChannelTypes.ARCHIVED
        self.state.channels.save_config()
