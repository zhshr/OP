import logging
import random
from pprint import pprint

import ipdb

import utils
from commands import CardMessageHelper
from commands.authenticator import Authenticated, AllowedUsers, AuthUser
from commands.base_commands import BaseCommands
from commands.card_message_helper import CardMessageButtonData, CardMessageHelperCallbacks
from database import item_library
from game import channel_manager
from khl import Message, Bot, Event
from khl.card import CardMessage, Card, Types, Module, Element
from khl.command import Command


def insufficient_primogem_cm(primogem_count: int):
    return CardMessage(
        Card(
            Module.Header("抽卡失败"),
            Module.Divider(),
            Module.Section(
                text=Element.Text(content="原石不足，现有{0}，需要160".format(primogem_count))
            ),
            theme=Types.Theme.DANGER
        ))


class PlayerCommands(BaseCommands):
    def __init__(self, bot, game_manager, state, card_message_helper: CardMessageHelper):
        super().__init__(bot, game_manager, state, card_message_helper)

    def _register(self):
        random.seed()
        self.bot.command.add(Command.command(name='state', )(self.get_player_state))
        self.bot.command.add(Command.command(name='grow')(self.grow_attr))
        self.bot.command.add(Command.command(name='advgrow')(self.adv_grow))
        self.card_message_helper.register_action('advgrow', self.do_advgrow)
        self.bot.command.add(Command.command(name='add')(self.add))
        self.bot.command.add(Command.command(name='addx')(self.addx))
        self.bot.command.add(Command.command(name='set')(self.set))
        self.bot.command.add(Command.command(name='setx')(self.setx))
        self.bot.command.add(Command.command(name='wish')(self.wish))
        self.card_message_helper.register_action('wish_confirm', self.do_wish)
        self.bot.command.add(Command.command(name='items')(self.get_items))
        self.bot.command.add(Command.command(name='move')(self.move))

    @Authenticated(allowed_user=[AllowedUsers.PLAYER_IN_SINGLE_CHANNEL])
    async def get_player_state(self, msg: Message, *, auth: AuthUser):
        await msg.reply(
            "\n".join(["{0}: {1}".format(k, v) for (k, v) in
                       self.state.players.player_state[auth.player_index()].attr.items()]))

    @Authenticated(allowed_user=[AllowedUsers.PLAYER_IN_SINGLE_CHANNEL])
    async def grow_attr(self, msg: Message, attr: str, value: int, *, auth: AuthUser):
        value = int(value)
        if value <= 0:
            await msg.reply("加点须大于0")
            return
        attr = attr.lower()
        if attr in ['hp', 'ap', 'sp']:
            await msg.reply("此属性只能由KP操作")
            return
        await msg.reply(self.state.players.add_attr(auth.player_index(), attr, value))

    @Authenticated(allowed_user=[AllowedUsers.PLAYER_IN_SINGLE_CHANNEL, AllowedUsers.KP])
    async def wish(self, msg: Message, *, auth: AuthUser):
        player_index = self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
        primo_count = self.state.players.player_state[player_index].get_item_count('0')
        if primo_count < 160:
            internal_id = None
            cm = insufficient_primogem_cm(primo_count)
        else:
            internal_id = self.card_message_helper.get_new_internal_id()
            additional_data = {
                "player_index": self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
            }
            confirm_data: CardMessageButtonData = CardMessageButtonData(
                action="wish_confirm",
                allowed_user_ids=[msg.author_id],
                card_message_internal_id=internal_id,
                additional_data=additional_data)
            cancel_data: CardMessageButtonData = CardMessageButtonData(
                action="wish_cancel",
                allowed_user_ids=[msg.author_id],
                card_message_internal_id=internal_id,
                additional_data=additional_data)
            cm = CardMessage(
                Card(
                    Module.Header("抽卡确认"),
                    Module.Divider(),
                    Module.Section(
                        text=Element.Text(content="现有{0}原石，抽取一次需160原石，是否继续?".format(primo_count))
                    ),
                    Module.Section(text=Element.Text(content="警告：不要多次点击，以防脚本出错！")),
                    Module.Divider(),
                    Module.ActionGroup(
                        Element.Button(
                            text=Element.Text(content="是"),
                            theme=Types.Theme.PRIMARY,
                            value=confirm_data.to_json()),
                        Element.Button(
                            text=Element.Text(content="否"),
                            theme=Types.Theme.SECONDARY,
                            value=cancel_data.to_json()),
                    ),
                    theme=Types.Theme.INFO,
                )
            )
        message = await msg.reply(cm)
        pprint(message)
        # ipdb.set_trace()
        if internal_id:
            self.card_message_helper.add_new_message(internal_id, message['msg_id'])

    async def do_wish(self, data: CardMessageButtonData, bot: Bot, e: Event, callbacks: CardMessageHelperCallbacks):
        logging.info("do_wish")
        player_index = int(data.additional_data['player_index'])
        primo_count = self.state.players.player_state[player_index].get_item_count('0')
        if primo_count < 160:
            cm = insufficient_primogem_cm(primo_count)
            await bot.client.update_message(e.body['msg_id'], cm)
            return
        value = sum(utils.roll('1d100'))
        if value <= 10:
            item_gained = '★ ★ ★ ★ ★'
            pool = {}
        elif value <= 40:
            item_gained = '★ ★ ★ ★'
            pool = item_library.instance().get_all_by_type(item_library.ItemType.EQUIPMENT4)
        else:
            item_gained = '★ ★ ★'
            pool = item_library.instance().get_all_by_type(item_library.ItemType.EQUIPMENT3)

        if len(pool) > 0:
            item_id = random.choice(list(pool.keys()))
            item_gained += ' ' + pool.get(item_id).name
            self.state.players.add_item_to_player(player_index, item_id, 1)
        self.state.players.add_item_to_player(player_index, 0, -160)

        # item_gained +=
        cm = CardMessage(
            Card(
                Module.Header("抽卡完成"),
                Module.Divider(),
                Module.Section(
                    text=Element.Text(content="1d100={0}".format(value))
                ),
                Module.Section(
                    text=Element.Text(content="你获得了{0}".format(item_gained))
                ),
                Module.Section(
                    text=Element.Text(content="剩余{0}原石".format(primo_count-160))
                ),
                theme=Types.Theme.SUCCESS
            ))

        await bot.client.update_message(e.body['msg_id'], cm)

    def _add(self, player_id: int, attr: str, diff: int):
        if attr.lower() in ['hp', 'ap', 'sp']:
            return self.state.players.add_state(player_id, attr.lower(), diff)
        return self.state.players.add_attr(player_id, attr, diff)

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[channel_manager.ChannelTypes.BOT_CONTROL])
    async def addx(self, msg: Message, player_name: str, attr: str, diff: int):
        result = self._add(self.state.players.get_index(player_name), attr, int(diff))
        await msg.reply(result)

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[channel_manager.ChannelTypes.PLAYER_SINGLE])
    async def add(self, msg: Message, attr: str, diff: int):
        result = self._add(
            self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id), attr, int(diff))
        await msg.reply(result)

    def _set(self, player_id: int, attr: str, value: int):
        if attr.lower() in ['hp', 'ap', 'sp']:
            return self.state.players.set_state(player_id, attr.lower(), value)
        return self.state.players.set_attr(player_id, attr, value)

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[channel_manager.ChannelTypes.BOT_CONTROL])
    async def setx(self, msg: Message, player_name: str, attr: str, value: int):
        player_id = self.state.players.get_index(player_name)
        current = self.state.players.get_attr(player_id, attr)
        result = self._set(self.state.players.get_index(player_name), attr, int(value))
        await msg.reply(result)

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[channel_manager.ChannelTypes.PLAYER_SINGLE])
    async def set(self, msg: Message, attr: str, value: int):
        player_id = self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
        current = self.state.players.get_attr(player_id, attr)
        result = self._set(
            self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id), attr, int(value))
        await msg.reply(result)

    @Authenticated(allowed_user=[AllowedUsers.KP, AllowedUsers.PLAYER_IN_SINGLE_CHANNEL],
                   allowed_channel=[channel_manager.ChannelTypes.PLAYER_SINGLE])
    async def get_items(self, msg: Message):
        player_id = self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
        lines = ["{1} \\* {0} [{2}] ".format(
            item_library.instance().get_item(item_id)[1].name,
            item.count,
            item_library.instance().get_item(item_id)[1].desc) for item_id, item in
            self.state.players.player_state[player_id].items.items()]
        await msg.reply('\n'.join(lines))

    @Authenticated(allowed_user=[AllowedUsers.PLAYER_IN_SINGLE_CHANNEL, AllowedUsers.KP])
    async def adv_grow(self, msg: Message):
        # self.state.players.player_state[0].attr
        pass

    def build_adv_grow_cm(self, ):

        cm = CardMessage(
                Card(
                    Module.Header("抽卡确认"),
                    Module.Divider(),
                    Module.Section(
                        text=Element.Text(content="现有{0}原石，抽取一次需160原石，是否继续?".format(0))
                    ),
                    Module.Section(text=Element.Text(content="警告：不要多次点击，以防脚本出错！")),
                    Module.Divider(),
                    Module.ActionGroup(
                        Element.Button(
                            text=Element.Text(content="是"),
                            theme=Types.Theme.PRIMARY,
                            ),
                        Element.Button(
                            text=Element.Text(content="否"),
                            theme=Types.Theme.SECONDARY,
                            ),
                    ),
                    theme=Types.Theme.INFO,
                )
            )

    async def do_advgrow(self, data: CardMessageButtonData, bot: Bot, e: Event, callbacks: CardMessageHelperCallbacks):
        pass

    @Authenticated(allowed_user=[AllowedUsers.KP, AllowedUsers.PLAYER_IN_SINGLE_CHANNEL],
                   allowed_channel=[channel_manager.ChannelTypes.PLAYER_SINGLE])
    async def move(self, msg: Message):
        player_id = self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
        ap = self.state.players.get_attr(player_id, 'ap')
        move_level = 80 if ap > 100 else 65 if ap > 75 else 50 if ap > 40 else 35

        dice = sum(utils.roll('1d100'))
        # dice = 96
        success_level = utils.success_level(dice, move_level)
        if success_level == utils.SuccessLevel.CRITICAL_FAILURE:
            self.state.players.add_state(player_id, 'ap', -5)
            result = '你原地摔了一跤并失去5点体力，剩余{0}点体力'.format(ap-5)
        else:
            avail_dis = \
                30 if success_level == utils.SuccessLevel.FAILURE else \
                60 if success_level == utils.SuccessLevel.REGULAR_SUCCESS else \
                80 if success_level == utils.SuccessLevel.HARD_SUCCESS else \
                120 if success_level == utils.SuccessLevel.EXTREME_SUCCESS else \
                999 if success_level == utils.SuccessLevel.CRITICAL_SUCCESS else \
                0
            result = '可移动{0}距离'.format(avail_dis)

        reply = '初始体力{0} 移动值{1} 掷骰1d100={2}, 成功等级{3}:{4}\n{5}'.format(
            ap, move_level, dice, success_level.value, success_level.display_name(), result)
        await msg.reply(reply)



