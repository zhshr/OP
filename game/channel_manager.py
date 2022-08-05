from enum import IntEnum
from typing import Any

from game.base_manager import BaseManager
from khl import PublicChannel


class ChannelTypes(IntEnum):
    UNKNOWN = -1,
    EVERY_CHANNEL = 0,
    BOT_CONTROL = 1,
    PLAYER_SINGLE = 2,
    PLAYER_SHARED = 3,
    ARCHIVED = 4

    PLAYER_SINGLE_CATEGORY = 100,
    PLAYER_SHARED_CATEGORY = 101,
    ARCHIVED_SHARED_CATEGORY = 102,
    CONTROL_CATEGORY = 103,


class ChannelManager(BaseManager):
    def default_config(self):
        return {
            'metadata': {}
        }

    def config_loaded(self):
        self.metadata: dict[str, dict] = self.config['metadata']

    def save_config(self):
        if self.metadata:
            self.config['metadata'] = self.metadata
        super().write_config()

    def __init__(self):
        self.channels: list[PublicChannel] = []
        self.metadata: dict[str, dict] = {}
        super().__init__()

    def add(self, channel: PublicChannel, metadata: dict[str, Any] = None):
        self.channels.append(channel)
        updated_metadata = {'name': channel.name, 'id': channel.id, 'parent_id': channel.parent_id}
        if metadata:
            updated_metadata.update(metadata)
        self.metadata[channel.id] = updated_metadata
        self.save_config()

    def add_all(self, channels: list[PublicChannel]):
        for channel in channels:
            self.add(channel)

    def get_private_room_category(self):
        for metadata in self.metadata.values():
            if metadata["type"] == ChannelTypes.PLAYER_SHARED_CATEGORY:
                return metadata['id']

    def get_history_private_room_category(self):
        for channel in self.channels:
            if channel.name == '历史对话组':
                return channel

    def is_player_private_channel(self, player_index: int, channel_id: str):
        metadata = self.metadata[channel_id]
        if not metadata:
            return False
        if 'player_private_channel' in metadata and metadata['player_private_channel'] == player_index:
            return True
        return False

    def get_player_private_channel_id(self, player_index: int) -> str:
        for metadata in self.metadata.values():
            if 'player_private_channel' in metadata and metadata['player_private_channel'] == player_index:
                return metadata['id']

    def get_all_channels(self, types: list[ChannelTypes]):
        result: list[str] = []
        for metadata in self.metadata.values():
            if 'type' in metadata and metadata['type'] in types:
                result.append(metadata['id'])
        return result

    def get_channel_type(self, channel_id: str) -> ChannelTypes:
        if channel_id not in self.metadata:
            return ChannelTypes.UNKNOWN
        metadata = self.metadata[channel_id]
        if metadata and metadata['type']:
            return ChannelTypes(metadata['type'])
        return ChannelTypes.UNKNOWN

    async def fetch_channel_map(self, guild) -> dict[str, PublicChannel]:
        channels = await guild.fetch_channel_list()
        channels = {channel.id: channel for channel in channels}
        return channels
