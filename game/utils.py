import logging

from game.role_manager import RoleManager
from khl import PublicChannel
from khl.interface import Permissions


class ChannelUtils:
    VISIBLE_EDITABLE = Permissions.VIEW_CHANNEL + Permissions.POST_MESSAGE + Permissions.MANAGE_MESSAGE

    @staticmethod
    async def set_to_kp_only(channel: PublicChannel, roles: RoleManager):
        kp_role = roles.get_kp_role()
        everyone_role = roles.get_everyone_role()
        await channel.update_role_permission(
            everyone_role,
            deny=ChannelUtils.VISIBLE_EDITABLE)

        await channel.create_role_permission(kp_role)
        await channel.update_role_permission(
            kp_role,
            allow=ChannelUtils.VISIBLE_EDITABLE)

    @staticmethod
    async def set_to_player_only(channel: PublicChannel, roles: RoleManager, player_name: str):
        await ChannelUtils.set_to_kp_only(channel, roles)
        player_role = roles.get_player_role(player_name)
        logging.info(player_role.id)
        await channel.create_role_permission(player_role)
        await channel.update_role_permission(
            player_role,
            allow=Permissions.VIEW_CHANNEL + Permissions.POST_MESSAGE)

    @staticmethod
    async def set_to_players_only(channel: PublicChannel, roles: RoleManager, player_names: list[str]):
        await ChannelUtils.set_to_kp_only(channel, roles)
        for name in player_names:
            player_role = roles.get_player_role(name)
            logging.info(player_role.id)
            await channel.create_role_permission(player_role)
            await channel.update_role_permission(
                player_role,
                allow=Permissions.VIEW_CHANNEL + Permissions.POST_MESSAGE)
