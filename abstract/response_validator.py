from typing import Dict, List, Type
from abc import ABC, abstractmethod
from node_penalty import NodePenalty


class ResponseValidator(ABC):
    def __init__(self, data_manager, penalty_class_type: NodePenalty) -> None:
        self.penalties: Dict = {}
        self.data_manager = data_manager
        self.penalty_class_type = penalty_class_type

    @abstractmethod
    def get_new_party(self, table_name: str, key: str, seed: int, n: int=None):       
        pass
    
    @abstractmethod
    def validate_responses(self, table_name: str, key: str, responses: Dict[str, Dict], 
                           round1_response: Dict = None, round2_response: Dict = None):
        pass

    @abstractmethod
    def exclude_complaint(self, complaint: Dict, public_keys: Dict, round1_response: Dict, round2_response: Dict):
        pass