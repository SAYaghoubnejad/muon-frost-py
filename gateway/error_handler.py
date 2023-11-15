from typing import Dict, List
from gateway_config import PENALTY_LIST, REMOVE_THRESHOLD

import time
import numpy as np


# TODO: Use data manager to store information
# TODO: Penalty should be
class Penalty:
    def __init__(self, id: str) -> None:
        self.id = id
        self.__time = 0
        self.__weight = 0

    def add_penalty(self, error_type: str) -> None:
        self.__time = int(time.time())
        self.__weight += PENALTY_LIST[error_type]

    def get_score(self) -> int:
        current_time = int(time.time())
        return self.__weight * np.exp(self.__time - current_time)

class ErrorHandler:
    def __init__(self) -> None:
        self.penalties: Dict[str, Penalty] = {}

    # TODO: use dkg_id -> party
    def get_new_party(self, old_party: List[str], n: int=None) -> List[str]:       
        below_threshold = 0
        for peer_id in old_party:
            if peer_id not in self.penalties.keys():
                self.penalties[peer_id] = Penalty(peer_id)
            if self.penalties[peer_id].get_score() < REMOVE_THRESHOLD:
                below_threshold += 1

        
        score_party = sorted(old_party, 
                       key=lambda x: self.penalties[x].get_score(), 
                       reverse=True)
        
        if n is None or n >= len(old_party) - below_threshold:
            n = len(old_party) - below_threshold
        return score_party[:n]

    def check_responses(self, responses: Dict[str, Dict]) -> bool:
        is_complete = True
        for peer_id, data in responses.items():
            data_status = data['status']
            if data_status != 'SUCCESSFUL':
                is_complete = False

            if data_status == 'COMPLAINT':
                # TODO: MHS
                guilty_id = '1'
            else:
                guilty_id = peer_id
            
            self.penalties[guilty_id].add_penalty(data_status)
        
        return is_complete

