from typing import List
from abc import ABC, abstractmethod

class NodePenalty:
   
    @abstractmethod
    def add_penalty(self, error_type: str) -> None:
        pass
    
    @abstractmethod
    def get_score(self) -> int:
        pass