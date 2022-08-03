import json
import logging

from commands import Commands
from khl import Message, Bot, Channel, api, ChannelTypes
from khl.guild import ChannelCategory


class Main:

    def load_config(self, path: str):
        logging.basicConfig(level='INFO')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def start(self):
        config = self.load_config('./config/config.json')
        bot = Bot(token=config['token'])

        commands = Commands(bot)
        commands.register()

        @bot.task.add_date()
        async def startup_tasks():
            await commands.startup()

        bot.command.update_prefixes('.')
        bot.run()


main = Main()
main.start()
