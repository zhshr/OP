import functools
import inspect
import logging
from enum import IntEnum

from commands.base_commands import BaseCommands
from game import channel_manager
from game.channel_manager import ChannelTypes
from game.role_manager import RoleTypes
from khl import Message, PublicMessage, GuildUser


class AllowedUsers(IntEnum):
    EVERYONE = 1,
    KP = 2,
    PLAYER = 3,
    PLAYER_IN_SINGLE_CHANNEL = 4,
    PLAYER_IN_SHARED_CHANNEL = 5,
    # Administrators are ALWAYS allowed EVERYWHERE
    # ADMINISTRATOR = 999,
    DEV = 1000


class Auth:
    def __init__(self, role_type: RoleTypes, role_index: int):
        self.role_type = role_type
        self.role_index = role_index


class AuthUser:
    def __init__(self, auth: list[Auth]):
        self.auth = auth

    def player_index(self):
        player_auth = list(filter(lambda a: a.role_type == RoleTypes.PLAYER, self.auth))
        if len(player_auth) != 1:
            return -1
        return player_auth[0].role_index


class Authenticated:
    def __init__(self, allowed_user=None, allowed_channel=None):
        if allowed_user is None:
            allowed_user = [AllowedUsers.EVERYONE]
        if allowed_channel is None:
            allowed_channel = [ChannelTypes.EVERY_CHANNEL]
        self.allowed_user = allowed_user
        self.allowed_channel = allowed_channel

    def __call__(self, func):
        # ipdb.set_trace()

        # @functools.wraps(func)
        async def wrapper(base: BaseCommands, msg: Message, *args, **kwargs):
            # ipdb.set_trace()
            if not isinstance(msg, PublicMessage):
                return
            user = await msg.ctx.guild.fetch_user(msg.author.id)
            auth_user = await self.get_auth(user, base)
            logging.info(auth_user)
            if not await self.is_user_allowed(auth_user, msg, base):
                await msg.reply("调用失败，用户组权限不足")
                return
            if not await self.is_channel_allowed(auth_user, msg, base):
                await msg.reply("调用失败，频道b")
                return
            argspec = inspect.getfullargspec(func)
            for name, arg in argspec.annotations.items():
                if arg == AuthUser:
                    kwargs.update({name: auth_user})
            await func(base, msg, *args, **kwargs)

        return wrapper

    async def get_auth(self, user: GuildUser, base: BaseCommands):
        logging.info(user)
        result = AuthUser([])
        for role_id in user.roles:
            role_type = base.state.roles.get_role_type(role_id)
            role_index = base.state.roles.get_player_index(role_id)
            result.auth.append(Auth(role_type, role_index))
        return result

    async def is_user_allowed(self, auth_user: AuthUser, msg: PublicMessage, base: BaseCommands):
        temp = []
        result = False
        for auth in auth_user.auth:
            temp.append(
                "Type={0}, Index={1} ".format(auth.role_type.name, auth.role_index))
            matched = False
            matched |= auth.role_type == RoleTypes.KP and AllowedUsers.KP in self.allowed_user
            matched |= auth.role_type == RoleTypes.DEV and AllowedUsers.DEV in self.allowed_user
            if AllowedUsers.EVERYONE in self.allowed_user:
                matched = True
            elif auth.role_type == RoleTypes.PLAYER:
                if AllowedUsers.PLAYER in self.allowed_user:
                    matched = True
                elif AllowedUsers.PLAYER_IN_SINGLE_CHANNEL in self.allowed_user:
                    try:
                        player_index = auth.role_index
                        if base.state.channels.is_player_private_channel(player_index, msg.channel.id):
                            matched = True
                    except ValueError:
                        pass

            if matched:
                result = True
                temp[-1] += "✓"

        reply = "Allowed roles: {1}\n\nUser roles:\n{0}".format(
            '\n'.join(temp),
            ', '.join(au.name for au in self.allowed_user)
        )
        await msg.reply(reply)
        return result

    async def is_channel_allowed(self, user: AuthUser, msg: PublicMessage, base: BaseCommands):
        temp = []
        result = False
        for ac in self.allowed_channel:
            temp.append(ac.name)
            if ChannelTypes.EVERY_CHANNEL == ac:
                pass
            elif base.state.channels.get_channel_type(msg.channel.id) == ac:
                pass
            else:
                continue
            temp[-1] += " ✓"
            result = True
        await msg.reply("Allowed channels:\n{0}".format('\n'.join(temp)))
        return result
