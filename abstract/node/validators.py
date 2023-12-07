import types
from typing import List, Dict
from abc import ABC, abstractmethod
from libp2p.typing import TProtocol

class Validators(ABC):
    @staticmethod
    @abstractmethod
    def caller_validator(sender_id: str, protocol: TProtocol):
        pass

    @staticmethod
    @abstractmethod
    def data_validator(self, sign_function: types.FunctionType, commitment_list: Dict, input_data: Dict):
        pass