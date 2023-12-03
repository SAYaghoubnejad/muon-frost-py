from typing import List
from abc import ABC, abstractmethod


class Validators(ABC):

    @staticmethod
    @abstractmethod
    def validate_seed(seed: int) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def validate_gateway(data, sender_id):
        pass

    @abstractmethod
    def app_interactor(self, message):
        pass