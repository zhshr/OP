import asyncio
import logging
import math
import random

from commands.authenticator import AllowedUsers, Authenticated
from commands.base_commands import BaseCommands
from game.channel_manager import ChannelTypes
from khl import Message, Channel, MessageTypes
from khl.card import Card, Module, Types, Element, CardMessage
from khl.command import Command


class GameCommands(BaseCommands):
    def __init__(self, bot, game_manager, state):
        super().__init__(bot, game_manager, state)

    @classmethod
    def init_and_register(cls, bot, game_manager, state):
        inst = cls(bot, game_manager, state)
        inst._register()
        return inst

    def _register(self):
        random.seed()
        self.bot.command.add(Command.command(name='r', )(self.roll))
        self.bot.command.add(Command.command(name='t')(self.show_turn))
        self.bot.command.add(Command.command(name='shout')(self.shout))
        self.bot.command.add(Command.command(name='setT')(self.set_turn))
        self.bot.command.add(Command.command(name='passT')(self.pass_turn))

    def do_roll(self, exp: str) -> list[int]:
        comp = exp.split('d')
        if len(comp) == 1:
            result = [random.randint(1, int(comp[0]))]
        elif comp[0] == '':
            result = [random.randint(1, int(comp[1]))]
        else:
            result = [random.randint(1, int(comp[1])) for i in range(int(comp[0]))]
        return result

    @Authenticated(allowed_user=[AllowedUsers.KP, AllowedUsers.PLAYER])
    async def roll(self, msg: Message, *params: str):
        segments = []
        total = 0
        for param in params:
            result = self.do_roll(param)
            segments.append("({0})".format('+'.join(map(str, result))))
            total += sum(result)
        reply = "{0} = {1}".format(" + ".join(segments), total)
        await msg.reply(reply)

    @Authenticated(allowed_user=[AllowedUsers.PLAYER, AllowedUsers.KP])
    async def show_turn(self, msg: Message):
        time = ['早上', '中午', '下午', '晚上']
        turn = self.game_manager.turn
        await msg.reply('目前为第{0}回合，第{1}天{2}'
                        .format(turn, math.ceil(turn / 4), time[(turn-1) % 4]))

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
