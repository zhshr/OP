import asyncio
import logging
import math
import random

import utils
from commands.authenticator import AllowedUsers, Authenticated
from commands.base_commands import BaseCommands
from commands.card_message_helper import CardMessageHelper
from database import item_library
from database.item_library import Item
from game.channel_manager import ChannelTypes
from khl import Message, Channel, MessageTypes
from khl.card import Card, Module, Types, Element, CardMessage
from khl.command import Command


class GameCommands(BaseCommands):
    def __init__(self, bot, game_manager, state, card_message_helper: CardMessageHelper):
        super().__init__(bot, game_manager, state, card_message_helper)

    def _register(self):
        random.seed()
        self.bot.command.add(Command.command(name='r', )(self.roll))
        self.bot.command.add(Command.command(name='t')(self.show_turn))
        self.bot.command.add(Command.command(name='shout')(self.shout))
        self.bot.command.add(Command.command(name='setT')(self.set_turn))
        self.bot.command.add(Command.command(name='passT')(self.pass_turn))
        self.bot.command.add(Command.command(name='set')(self.set_attr))
        self.bot.command.add(Command.command(name='additemtoconfig')(self.add_item_to_config))
        self.bot.command.add(Command.command(name='additem')(self.add_item_to_player))
        self.bot.command.add(Command.command(name='listallitems')(self.list_all_items))

    @Authenticated(allowed_user=[AllowedUsers.KP, AllowedUsers.PLAYER])
    async def roll(self, msg: Message, *params: str):
        segments = []
        total = 0
        for param in params:
            result = utils.roll(param)
            segments.append("({0})".format('+'.join(map(str, result))))
            total += sum(result)
        reply = "{0} = {1}".format(" + ".join(segments), total)
        await msg.reply(reply)

    @Authenticated(allowed_user=[AllowedUsers.PLAYER, AllowedUsers.KP])
    async def show_turn(self, msg: Message):
        time = ['早上', '中午', '下午', '晚上']
        turn = self.game_manager.turn
        await msg.reply('目前为第{0}回合，第{1}天{2}'
                        .format(turn, math.ceil(turn / 4), time[(turn - 1) % 4]))

    @Authenticated(allowed_user=[AllowedUsers.KP])
    async def set_turn(self, msg: Message, turn: int):
        new_turn = await self.game_manager.time_lapse(int(turn) - self.game_manager.turn)
        await msg.reply("回合已设为{0}".format(new_turn))

    @Authenticated(allowed_user=[AllowedUsers.KP])
    async def pass_turn(self, msg: Message):
        new_turn = await self.game_manager.time_lapse(1)
        await msg.reply("回合已设为{0}".format(new_turn))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.BOT_CONTROL])
    async def shout(self, msg: Message, content: str):
        channel_ids = self.state.channels.get_all_channels(
            [ChannelTypes.PLAYER_SINGLE, ChannelTypes.PLAYER_SHARED])
        channels = await self.state.guild.fetch_channel_list()
        channels_to_send = [channel for channel in channels if channel.id in channel_ids]
        logging.info('Message to send to {0}'.format(' '.join(
            [channel.name for channel in channels_to_send]
        )))
        card = CardMessage(
            Card(
                Module.Header('全域广播 来自：'),
                Module.Section(text=msg.author.nickname,
                               accessory=Element.Image(src=msg.author.avatar)),
                Module.Divider(),
                Module.Section(text=Element.Text(type=Types.Text.KMD, content=content)),
                theme=Types.Theme.PRIMARY
            ))

        async def send(c: Channel):
            await c.send(card, type=MessageTypes.CARD)

        promises = [send(c) for c in channels_to_send]
        await asyncio.gather(*promises)

    @Authenticated(allowed_user=[AllowedUsers.KP])
    async def set_attr(self, msg: Message, playerid:str,attr: str, value: int):
        value = int(value)


        attr = attr.lower()
        for player in self.state.players.player_state:
            if player.name == playerid:
                
                await msg.reply(self.state.players.change_attr2(player.player_index, attr, value))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.BOT_CONTROL])
    async def add_item_to_config(self, msg: Message, item_name: str, item_desc: str):
        items = item_library.instance()
        new_item = items.add_item(item_library.Item(name=item_name, desc=item_desc, type=item_library.ItemType.ITEM))
        await msg.reply("物品{0}添加完成(ID={1})".format(item_name, new_item))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.PLAYER_SINGLE])
    async def add_item_to_player(self, msg: Message, item: str, count: int):
        player_index = self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
        if player_index == -1:
            return
        item_id, item = item_library.instance().get_item(item)
        new_count = self.state.players.add_item_to_player(player_index, item_id, count)
        await msg.reply("成功为玩家{0}增加物品{1}*{2},现有{3}个".format(
            self.state.players.player_state[player_index].name,
            item.name,
            count,
            new_count
        ))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.BOT_CONTROL])
    async def list_all_items(self, msg: Message):
        items = []
        for item_id, item in item_library.instance().item_map.items():
            items.append('ID={0}: 类别：{2} 名称：{1} 描述：{3}'.format(item_id, item.name, item.type.name, item.desc))
        await msg.reply('\n'.join(items))

