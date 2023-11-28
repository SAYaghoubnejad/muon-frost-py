from typing import List
from abc import ABC, abstractmethod


class GatewayValidators(ABC):
    @staticmethod
    @abstractmethod
    def get_valid_seed() -> bool:
        pass

