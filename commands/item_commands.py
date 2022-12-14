import random

from commands.authenticator import Authenticated, AllowedUsers, AuthUser
from commands.base_commands import BaseCommands
from database import item_library
from game.channel_manager import ChannelTypes
from khl import Message
from khl.command import Command


class ItemCommands(BaseCommands):
    def _register(self):
        self.bot.command.add(Command.command(name='tre')(self.tre))
        self.bot.command.add(Command.command(name='showtre')(self.showtre))
        self.bot.command.add(Command.command(name='gettre')(self.get_tre))
        self.bot.command.add(Command.command(name='listallitems2')(self.list_all_items_new))
        self.bot.command.add(Command.command(name='drop')(self.drop))

        pass

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.BOT_CONTROL])
    async def tre(self, msg: Message, treasure_level: int, item_name_or_id: str, value: int):
        treasure_level = int(treasure_level)
        value = int(value)
        item_id, item = item_library.instance().get_item(item_name_or_id)

        self.state.chests.set_item(treasure_level, item_id, value)
        await msg.reply('操作完成')

    @Authenticated(allowed_user=[AllowedUsers.KP, AllowedUsers.PLAYER_IN_SINGLE_CHANNEL],
                   allowed_channel=[ChannelTypes.PLAYER_SINGLE, ChannelTypes.BOT_CONTROL])
    async def showtre(self, msg: Message, treasure_level: int, *, auth: AuthUser):
        channel_type = self.state.channels.get_channel_type(msg.ctx.channel.id)
        if channel_type == ChannelTypes.BOT_CONTROL:
            await msg.reply(self.showtre_kp(treasure_level))
        else:
            await msg.reply(self.showtre_pl(treasure_level))

    chest_display_name = ['?', '普通', '精致', '华丽']

    def showtre_kp(self, treasure_level: int):
        treasure_level = int(treasure_level)
        items = self.state.chests.chests[treasure_level].items
        lines = ["{0} x {1}".format(item_library.instance().get_item(item_id)[1].name, item_entry.count) for
                 item_id, item_entry in items.items()]
        if len(lines) == 0:
            lines = ['空']
        return "{0}宝箱({1}级)内容\n{2}" \
            .format(self.chest_display_name[treasure_level], treasure_level, '\n'.join(lines))

    def showtre_pl(self, treasure_level: int):
        treasure_level = int(treasure_level)
        items = self.state.chests.chests[treasure_level].items
        lines = ["{0}".format(item_library.instance().get_item(item_id)[1].name, item_entry.count) for
                 item_id, item_entry in items.items()]
        if len(lines) == 0:
            lines = ['空']
        return "{0}宝箱({1}级)内容 (注意物品可能有多件或已被抽取)\n{2}" \
            .format(self.chest_display_name[treasure_level], treasure_level, '\n'.join(lines))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.PLAYER_SINGLE])
    async def get_tre(self, msg: Message, treasure_level: int):
        treasure_level = int(treasure_level)
        chest = self.state.chests.chests[treasure_level]
        content = self.showtre_pl(treasure_level)
        weights = [i.count for i in chest.items.values()]
        if sum(weights) == 0:
            await msg.reply("宝箱池已枯竭")
            return
        item_id = random.choices(list(chest.items.keys()), [i.count for i in chest.items.values()], k=1)[0]
        self.state.chests.set_item(treasure_level, item_id, chest.items[item_id].count - 1)
        self.state.players.add_item_to_player(
            self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id),
            item_id)
        _, item = item_library.instance().get_item(item_id)
        await msg.reply("{0}\n\n获得道具{1}".format(content, item.name))

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.BOT_CONTROL])
    async def list_all_items_new(self, msg: Message):
        # item_map = {}
        # for item_id, item in item_library.instance().item_map.items():
        #     item_map.setdefault(item.type, []).append()
        #     items.append(
        #         'ID={0}: 类别：{2} 名称：{1} 描述：{3}'.format(item_id, item.name, item.type.display_name, item.desc))
        # await msg.reply('\n'.join(items))
        pass

    @Authenticated(allowed_user=[AllowedUsers.KP], allowed_channel=[ChannelTypes.PLAYER_SINGLE])
    async def drop(self, msg: Message, item_type: str = None, count: str = '1'):
        help_message = "说明：随机等概率抽取指定种类物品加入当前玩家背包。可用物品种类：{0}".format(
            ", ".join(["{0}({1})".format(it.name, it.display_name) for it in item_library.ItemType]))
        if item_type is None:
            await msg.reply(help_message)
            return

        all_items = item_library.instance().get_all_by_type(item_library.ItemType(int(item_type)))
        k = random.choice(list(all_items.keys()))

        player_index = self.state.channels.which_player_single_channel_is_this(msg.ctx.channel.id)
        if player_index == -1:
            return
        if int(k) == -1:
            await msg.reply("物品{0}不存在，请先添加".format(k))
            return
        new_count = self.state.players.add_item_to_player(player_index, k, int(count))
        await msg.reply("成功为玩家{0}增加物品{1}*{2},现有{3}个".format(
            self.state.players.player_state[player_index].name,
            all_items[k].name,
            count,
            new_count
        ))
