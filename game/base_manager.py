import json
import logging
from abc import ABC, abstractmethod


class BaseManager(ABC):
    def __init__(self):
        self.config_name = './config/{0}.json'.format(self.__class__.__name__.lower())
        try:
            with open(self.config_name, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                logging.info("Config: {0} \n {1}".format(self.__class__.__name__, self.config))
        except FileNotFoundError:
            self.config = self.default_config()
            self.write_config()
        self.config_loaded()

    def write_config(self):
        with open(self.config_name, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4, default=lambda o: o.__dict__)
            logging.info("Config: {0} created".format(self.__class__.__name__))

    @abstractmethod
    def default_config(self):
        pass

    @abstractmethod
    def config_loaded(self):
        pass

    @abstractmethod
    def save_config(self):
        pass
