from abc import ABC, abstractmethod
from typing import Dict, List

class DataManager(ABC):
    @abstractmethod
    def get_nonces(self) -> List:
        pass
    
    @abstractmethod
    def set_nonces(self, nonces_list: List) -> None:
        
        pass
    
    @abstractmethod
    def set_dkg_key(self,  key, value) -> None:
        pass
    
    @abstractmethod
    def get_dkg_key(self, key):
        pass
