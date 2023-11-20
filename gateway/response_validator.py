from typing import Dict, List
from gateway_config import PENALTY_LIST, REMOVE_THRESHOLD
from common.TSS.tss import TSS
from common.data_manager import DataManager

from web3 import Web3

import time
import json
import numpy as np


# TODO: Use data manager to store information
# TODO: Penalty should be Interface
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

class ResponseValidator:
    def __init__(self) -> None:
        self.penalties: Dict[str, Penalty] = {}
        self.data_manager = DataManager()
        self.data_manager.setup_database('Responses')
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

    def validate_responses(self, responses: Dict[str, Dict]) -> bool:
        is_complete = True
        for peer_id, data in responses.items():
            data_status = data['status']
            if data_status != 'SUCCESSFUL':
                is_complete = False

            if data_status == 'COMPLAINT':
                # TODO: use exclude_complaint function to determine which node is guilty
                
                guilty_id = '1'
            else:
                guilty_id = peer_id
            
            try:
                self.penalties[guilty_id].add_penalty(data_status)
            except:
                self.penalties[guilty_id] = Penalty(peer_id)
                self.penalties[guilty_id].add_penalty(data_status)
        
        return is_complete

    
    def exclude_complaint(self, complaint, public_keys):
        complaint_pop_hash = Web3.solidity_keccak(
            [
                "uint8", 
                "uint8", 
                "uint8", 
                "uint8",
                "uint8"
                ],
            [
                public_keys[complaint['complaintant']],
                public_keys[complaint['malicious']],
                complaint['encryption_key'],
                complaint['public_nonce'],
                complaint['commitment']
                ],
            )
        pop_verification = TSS.complaint_verify(
            TSS.code_to_pub(public_keys[complaint['complaintant']]),
            TSS.code_to_pub(public_keys[complaint['malicious']]),
            TSS.code_to_pub(complaint['encryption_key']),
            complaint['proof'],
            complaint_pop_hash
        )
        
        if not pop_verification:
            return complaint['complaintant']
        
        encryption_key = TSS.generate_hkdf_key(complaint['encryption_key'])
        encrypted_data = b'' # TODO
        data = json.loads(TSS.decrypt(encrypted_data, encryption_key))
        round1_broadcasted_data = [] # TODO
        for round1_data in round1_broadcasted_data: 
            if round1_data["sender_id"] == complaint['complaintant']:
                public_fx = round1_data["public_fx"]

                point1 = TSS.calc_poly_point(
                    list(map(TSS.code_to_pub, public_fx)),
                    int.from_bytes(self.node_id.to_bytes(), 'big')
                )
                
                point2 = TSS.curve.mul_point(
                    data["f"], 
                    TSS.curve.generator
                )

                if point1 != point2:
                    return complaint['malicious']
                else:
                    return complaint['complaintant']