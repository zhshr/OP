from pprint import pprint

import ipdb

from commands.game_commands import GameCommands
from commands.player_commands import PlayerCommands
from commands.room_commands import RoomCommands
from database import Database
from game.game_manager import GameManager
from game.global_state import GlobalState
from khl import Bot, Message, ChannelTypes, PublicMessage, Guild, Event, EventTypes
from khl.card import CardMessage, Card, Types, Module, Element
from khl.command import Command
#
# 8636039613288526: 文字频道
# 4409068061183200: 语音频道
# 7251287929680713: 机器人指令区
# 9657331640632914: KP组交流区
# 4020361214656874: A
# 7573827474720009: B
# 5536361253300239: A和B
# 8102462154823487: B和C
# 5841193295094693: 聊天区
# 6174240507904923: 休闲区
#
#
# 2688957342566548: 文字分组
# 2810036372749165: 语音分组
# 3707234716365969: KP组
# 4765489161378098: 玩家单人组
# 4561803135920062: 玩家对话组
# 1240807523669127: 历史对话组
# 3872743605733543: 观众讨论组

class Commands:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.state = GlobalState()
        self.game_manager = GameManager(bot, Database(), self.state)

    async def startup(self):
        await self.game_manager.fetch_roles()

    def register(self):
        GameCommands.init_and_register(self.bot, self.game_manager, self.state)
        RoomCommands.init_and_register(self.bot, self.game_manager, self.state)
        PlayerCommands.init_and_register(self.bot, self.game_manager, self.state)
        self.bot.command.add(Command.command(name='cc', )(self.create_channel))
        self.bot.command.add(Command.command(name='debug', )(self.debug))
        self.bot.command.add(Command.command(name='initialize', )(self.initialize))
        self.bot.command.add(Command.command(name='getroles')(self.get_role))
        self.bot.command.add(Command.command(name='getchannels')(self.get_channels))
        self.bot.command.add(Command.command(name='getcategories')(self.get_categories))
        self.bot.command.add(Command.command(name='deletechannel')(self.do_delete_channels))
        self.bot.add_event_handler(EventTypes.MESSAGE_BTN_CLICK, self.button_click)

    async def create_channel(self, msg: Message, name: str):
        await msg.reply(name)
        await msg.ctx.guild.create_channel(
            name=name,
            type=ChannelTypes.TEXT,
        )

    async def debug(self, msg: Message):
        # ipdb.set_trace()
        if isinstance(msg, PublicMessage):
            reply = str.format("author: {authorid} {authorname}, channel: {channelid} {channelname}",
                               authorid=msg.author.id,
                               authorname=msg.author.nickname,
                               channelid=msg.channel.id,
                               channelname=msg.channel.name)
            guild: Guild = await self.bot.fetch_guild(msg.ctx.guild.id)
            pprint(guild.channels)
            pprint(await guild.fetch_channel_category_list())
            ipdb.set_trace()
            await msg.reply(reply)

    async def get_role(self, msg: Message):
        roles = await msg.ctx.guild.fetch_roles()
        await msg.reply("\n".join(
            ["{0}: {1}".format(role.id, role.name) for role in roles]
        ))
        # ipdb.set_trace()

    async def get_channels(self, msg: Message):
        channels = await msg.ctx.guild.fetch_channel_list()
        await msg.reply("\n".join(
            ["{0}: {1}".format(channel.id, channel.name) for channel in channels]
        ))
        # ipdb.set_trace()

    async def get_categories(self, msg: Message):
        channels = await msg.ctx.guild.fetch_channel_category_list()
        await msg.reply("\n".join(
            ["{0}: {1}".format(channel.id, channel.name) for channel in channels]
        ))
        # ipdb.set_trace()

    async def initialize(self, msg: Message):
        if not isinstance(msg, PublicMessage):
            return

        cm = CardMessage(
            Card(
                Module.Header('游戏初始化'),
                Module.ActionGroup(
                    Element.Button('Yes', 'initialize_y', theme=Types.Theme.PRIMARY),
                    Element.Button('No', 'initialize_n', theme=Types.Theme.SECONDARY),
                ),
                theme=Types.Theme.INFO, )
        )
        await self.bot.send(msg.channel, cm)

    async def do_initialize(self, guild_id: str):
        await self.game_manager.initialize(guild_id)

    async def do_delete_channels(self, *args):
        await self.game_manager.delete_channels(*args)

    async def button_click(self, bot: Bot, e: Event):
        # pprint(e.body)
        if e.body['value'] == 'initialize_y':
            await self.do_initialize(e.body['guild_id'])
        elif e.body['value'] == 'initialize_n':
            await self.do_delete_channels()
