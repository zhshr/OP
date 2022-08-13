import asyncio
import logging

from database import Database
from game import channel_manager
from game.global_state import GlobalState
from game.manager_with_config import ManagerWithState
from game.utils import ChannelUtils
from khl import Bot, Message, ChannelTypes
from khl.card import CardMessage, Card, Module, Element, Types
from khl.command import Command


class Config:
    def __init__(self):
        pass


class GameManager(ManagerWithState):

    def default_config(self):
        return {
            'guild_id': 0,
            'turn': 1
        }

    def config_loaded(self):
        self.guild_id = self.config['guild_id']
        self.turn = self.config['turn']

    def save_config(self):
        self.config['guild_id'] = self.guild_id
        self.config['turn'] = self.turn
        super().write_config()

    def __init__(self, bot: Bot, database: Database, global_state: GlobalState):
        self.bot = bot
        self.database = database
        self.guild_id = ''
        self.turn = 0
        super().__init__(global_state)

    def resume(self):
        pass

    @staticmethod
    async def initialize_game(msg: Message):
        await msg.reply('initializing')

    async def initialize(self, guild_id: str):
        await self.fetch_roles(guild_id)
        await self.create_channels()

    async def fetch_roles(self, guild_id=None):
        self.state.guild = await self.bot.fetch_guild(guild_id if guild_id else self.config['guild_id'])
        self.state.roles.set_roles(await self.state.guild.fetch_roles())

    async def create_channel(self, name: str, type: ChannelTypes, category_id: str | None):
        return await self.state.guild.create_channel(name, type, category_id)

    async def create_channels(self):
        # kp_category = await self.create_channel('KP组', ChannelTypes.CATEGORY, None)
        # robot_channel = await self.create_channel('机器人指令区', ChannelTypes.TEXT, kp_category.id)
        # kp_comms = await self.create_channel('KP组交流区', ChannelTypes.TEXT, kp_category.id)
        # self.state.channels.add_all([kp_category, robot_channel, kp_comms])
        # await ChannelUtils.set_to_kp_only(kp_category, self.state.roles)
        #
        player_single_category = self.state.channels.get_all_channels(
            [channel_manager.ChannelTypes.PLAYER_SINGLE_CATEGORY])
        if len(player_single_category) < 1:
            ch = await self.create_channel('玩家单人组', ChannelTypes.CATEGORY, None)
            player_single_category_id = ch.id
            self.state.channels.add(player_single_category,
                                    {'type': channel_manager.ChannelTypes.PLAYER_SINGLE_CATEGORY})
        else:
            player_single_category_id = player_single_category[0]

        for player_state in self.state.players.player_state:
            channel = await self.create_channel(player_state.name, ChannelTypes.TEXT, player_single_category_id)
            player_state.channel = channel
            self.state.channels.add(channel, {'player_private_channel': player_state.player_index,
                                              'type': channel_manager.ChannelTypes.PLAYER_SINGLE}, )
            await ChannelUtils.set_to_player_only(channel, self.state.roles, player_state.name)

        # player_shared_category = self.state.channels.get_all_channels(
        #     [channel_manager.ChannelTypes.PLAYER_SHARED_CATEGORY])
        # if len(player_single_category) < 1:
        #     ch = await self.create_channel('玩家对话组', ChannelTypes.CATEGORY, None)
        #     player_single_category_id = ch.id
        #     self.state.channels.add(player_single_category,
        #                             {'type': channel_manager.ChannelTypes.PLAYER_SINGLE_CATEGORY})
        # else:
        #     player_single_category_id = player_single_category[0]
        #
        # private_room_category = await self.create_channel('玩家对话组', ChannelTypes.CATEGORY, None)
        # self.state.channels.add(private_room_category)
        # await ChannelUtils.set_to_kp_only(private_room_category, self.state.roles)

    async def delete_channels(self, *args):
        types = [channel_manager.ChannelTypes[arg].value for arg in args]
        metadata = self.state.channels.metadata.copy()
        for metadata in metadata.values():
            if 'type' in metadata and metadata['type'] in types:
                await self.bot.delete_channel(metadata['id'])
                self.state.channels.metadata.pop(metadata['id'])
        self.state.channels.save_config()

    def get_channels_config(self):
        return \
            [
                {'name': 'KP组',
                 'type': ChannelTypes.CATEGORY,
                 'children': [
                     {'name': '机器人指令区', 'type': ChannelTypes.TEXT},
                     {'name': 'KP组交流区', 'type': ChannelTypes.TEXT},
                 ]},
                {'name': '玩家单人组',
                 'type': ChannelTypes.CATEGORY,
                 },
            ]

    def init(self):
        self.bot.command.add(Command.command(name='initialize', )(self.initialize_game))

    async def time_lapse(self, turns: int):
        prev = self.turn
        after = self.turn + turns
        auto_recover_times = (after-1) // 12 - (prev-1) // 12
        logging.info('time lapse {0} -> {1}, triggered {2} AP recovery'.format(prev, after, auto_recover_times))
        if auto_recover_times > 0:
            channels = await self.state.channels.fetch_channel_map(self.state.guild)
            futures = []
            for player_state in self.state.players.player_state:
                result = self.state.players.add_state(player_state.player_index, 'ap', 40 * auto_recover_times)
                cm = CardMessage(
                    Card(
                        Module.Header("自动回复"),
                        Module.Divider(),
                        Module.Section(
                            text=Element.Text(content=result)
                        ),
                        theme=Types.Theme.INFO,
                    )
                )
                futures.append(
                    channels[self.state.channels.get_player_private_channel_id(player_state.player_index)].send(cm))
            await asyncio.gather(*futures)
        self.turn = after
        self.state.players.save_config()
        self.save_config()
        return self.turn
