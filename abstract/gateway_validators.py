from typing import List
from abc import ABC, abstractmethod


class GatewayValidators(ABC):

    @staticmethod
    @abstractmethod
    def validate_seed(seed: int) -> bool:
        pass

