import json
import logging
from abc import ABC, abstractmethod


class ConfigClass(ABC):
    def __init__(self, config_name: str = None):
        self.config_name = config_name if config_name else self.__class__.__name__.lower()
        self.config_file_name = './config/{0}.json'.format(self.config_name)
        try:
            with open(self.config_file_name, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                logging.info("Config: {0} \n {1}".format(config_name, self.config))
        except FileNotFoundError:
            self.config = self.default_config()
            self.write_config()
        self.config_loaded()

    def write_config(self):
        with open(self.config_file_name, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4, default=lambda o: o.__dict__)
            logging.info("Config: {0} created".format(self.config_name))

    @abstractmethod
    def default_config(self):
        pass

    @abstractmethod
    def config_loaded(self):
        pass

    @abstractmethod
    def save_config(self):
        pass
