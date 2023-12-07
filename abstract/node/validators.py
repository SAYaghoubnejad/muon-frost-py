import types
from typing import List, Dict
from abc import ABC, abstractmethod


class Validators(ABC):
    @staticmethod
    @abstractmethod
    def validate_caller(data, sender_id):
        pass
    
    @abstractmethod
    def data_validator(self, sign_function: types.FunctionType, commitment_list: Dict, input_data: Dict):
        pass