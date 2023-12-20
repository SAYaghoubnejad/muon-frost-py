from typing import List
from abc import ABC, abstractmethod


class NodeInfo(ABC):
    @abstractmethod
    def lookup_node(self, peer_id: str):
        pass

    @abstractmethod
    def get_all_nodes(self, n: int = None) -> List[str]:
        pass
