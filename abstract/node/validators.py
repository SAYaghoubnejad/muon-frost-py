import types
from typing import List, Dict
from abc import ABC, abstractmethod


class Validators(ABC):

    @staticmethod
    @abstractmethod
    def validate_seed(seed: int) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def validate_sa(data, sender_id):
        pass

    @abstractmethod
    def app_interactor(self, sign_function: types.FunctionType, commitment_list: Dict, app_data: Dict):
        pass