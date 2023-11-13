from typing import Dict, List
from gateway_config import PENALTY_LIST, REMOVE_THRESHOLD

import time
import numpy as np


# TODO: Use data manager to store information
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
        self.penalties: Dict[str, Penalty] = {}

    # TODO: use dkg_id -> party
    def get_new_party(self, old_party: List[str], n: int=None) -> List[str]:
        # TODO
        if n is None or n > len(old_party):
            n = len(old_party)
        
        penalties = {}
        for peer_id in old_party:
            if peer_id not in self.penalties.keys():
                self.penalties[peer_id] = Penalty(peer_id)
                penalties[peer_id] = self.penalties[peer_id].copy()

        current_time = int(time.time())
        for id, penalty in penalties.items():
            # TODO: move scoring to panalty class (as an interface)
            if penalty.weight * np.exp(penalty.time - current_time) < REMOVE_THRESHOLD:
                del penalties[id]
        
        score_party = sorted(penalties.keys(), 
                       key=lambda x: penalties[x].weight * np.exp(penalties[x].time - current_time), 
                       reverse=True)
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

