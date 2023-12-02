from typing import List
from abc import ABC, abstractmethod

class DNS(ABC):
    """
    A DNS-like class for managing and resolving peer network information.
    It maintains a lookup table mapping peer IDs to their respective network details.

    Note: If one wishes to use other data structures or another form of data, one 
    can inherit from this class and use the modified class. 
    """
    @abstractmethod
    def lookup_deployer(self, peer_id:str):
        pass
    

    @abstractmethod
    def lookup_gateway(self, peer_id:str):
        pass
    
    @abstractmethod
    def lookup_node(self, peer_id: str):
        """
        Resolves the network details for a given peer ID.

        Parameters:
        peer_id (str): The peer ID whose details are to be resolved.

        Returns:
        A dictionary containing the network details (IP, port, public key) of the specified peer ID.
        """
        pass
    
    @abstractmethod
    def get_all_nodes(self, n:int = None) -> List[str]:
        pass
