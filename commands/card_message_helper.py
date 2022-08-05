import logging
import uuid
from dataclasses import dataclass
from pprint import pprint
from typing import Callable, Any, Awaitable

import ipdb
from dataclasses_json import dataclass_json, LetterCase

from base.config_class import ConfigClass
from khl import EventTypes, Bot, Event
from khl.card import CardMessage, Card, Module, Element, Types


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CardMessageMetadata:
    internal_id: str
    message_id: str
    pass


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CardMessageButtonData:
    card_message_internal_id: str
    allowed_user_ids: list[id]
    action: str
    additional_data: dict[str, Any]


class CardMessageHelperCallbacks:
    def __init__(self, remove_reference: Callable[[], bool]):
        # returns if removing reference succeeded
        self.remove_reference = remove_reference


CardMessageCallback = Callable[[CardMessageButtonData, Bot, Event, CardMessageHelperCallbacks], Awaitable[Any]]
EXPIRED_MSG = CardMessage(
    Card(
        Module.Header("消息已过期"),
        theme=Types.Theme.WARNING
    ))


class CardMessageHelper(ConfigClass):
    def save_config(self):
        self.config['metadata'] = self.metadata
        super().write_config()

    def config_loaded(self):
        pprint(self.config)
        for k, v in self.config['metadata'].items():
            self.metadata.update({k: CardMessageMetadata.from_dict(v)})

    def default_config(self):
        return {
            'metadata': {}
        }

    def __init__(self, bot):
        bot.add_event_handler(EventTypes.MESSAGE_BTN_CLICK, self.onclick)
        self.metadata: dict[str, CardMessageMetadata] = {}
        self.action_registry: dict[str, CardMessageCallback] = {}
        super().__init__()

    async def onclick(self, bot: Bot, e: Event):
        pprint(e.body)
        # if self.metadata
        try:
            message: CardMessageButtonData = CardMessageButtonData.from_json(e.body['value'])
            pprint(message)
            if e.body['user_id'] not in message.allowed_user_ids:
                return
            if message.card_message_internal_id not in self.metadata:
                await bot.client.update_message(e.body['msg_id'], EXPIRED_MSG)
                return
            if message.action in self.action_registry:
                def remove_reference():
                    try:
                        return True
                    except KeyError:
                        return False
                self.metadata.pop(message.card_message_internal_id)
                self.save_config()
                await self.action_registry[message.action](
                    message, bot, e,
                    CardMessageHelperCallbacks(
                        remove_reference=remove_reference
                    ))
        finally:
            pass

    def register_action(self, action: str, func: CardMessageCallback):
        self.action_registry.update({action: func})

    def get_new_internal_id(self) -> str:
        return str(uuid.uuid4())

    def add_new_message(self, internal_id: str, message_id: str):
        self.metadata.update({internal_id: CardMessageMetadata(internal_id, message_id)})
        logging.info('New card message: {0} - {1}'.format(internal_id, message_id))
        self.save_config()
