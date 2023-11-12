from typing import Dict, List
from gateway_config import PENALTY_LIST, REMOVE_THRESHOLD

import time
import numpy as np


class Penalty:
    def __init__(self, id: str) -> None:
        self.id = id
        self.time = 0
        self.weight = 0

    def add_penalty(self, error_type: str) -> None:
        self.time = int(time.time())
        self.weight += PENALTY_LIST[error_type]

class ErrorHandler:
    def __init__(self) -> None:
        self.penaltys: Dict[str, Penalty] = {}

    def get_new_party(self, old_party: List[str], n: int=None) -> List[str]:
        if n is None or n > len(old_party):
            n = len(old_party)
        
        for peer_id in old_party:
            if peer_id not in self.penaltys.keys():
                self.penaltys[peer_id] = Penalty(peer_id)

        penaltys = self.penaltys.copy()
        current_time = int(time.time())
        for id, penalty in penaltys.items():
            if penalty.weight * np.exp(penalty.time - current_time) < REMOVE_THRESHOLD:
                del penaltys[id]
        
        score_party = sorted(penaltys.keys(), 
                       key=lambda x: penaltys[x].weight * np.exp(penaltys[x].time - current_time), 
                       reverse=True)
        return score_party[:n]

    def check_response(self, response: Dict[str, Dict]) -> bool:
        is_complete = True
        for peer_id, data in response.items():
            data_status = data['status']
            if data_status != 'SUCCESSFUL':
                is_complete = False

            if data_status == 'COMPLAINT':
                # TODO: MHS
                guilty_id = '1'
            else:
                guilty_id = peer_id
            
            self.penaltys[guilty_id].add_penalty(data_status)
        
        return is_complete

