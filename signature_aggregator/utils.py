from common.TSS.tss import TSS
from common.libp2p_config import PROTOCOLS_ID
from libp2p.peer.id import ID as PeerID
from libp2p.typing import TProtocol

from typing import Dict, List
import trio
import types
import json
import logging

class RequestObject:
    def __init__(self, request_id: str, call_method: str, gateway_authorization: str, parameters: Dict) -> None:
        self.request_id: str = request_id
        self.call_method: str = call_method
        self.gateway_authorization: str = gateway_authorization
        self.parameters: Dict = parameters


    def get(self):
        result = {
            "request_id": f"{self.request_id}_{self.call_method}",
            "method": self.call_method,
            'gateway_authorization': self.gateway_authorization,
            "parameters": self.parameters
        }
        return result



class Wrappers:
    @staticmethod
    async def sign(send: types.FunctionType, dkg_key, destination_address: Dict[str, str], destination_peer_id: PeerID, protocol_id: TProtocol,
                   message: Dict, result: Dict = None, timeout: float = 5.0, semaphore: trio.Semaphore = None):
        
        await send(destination_address, destination_peer_id, protocol_id,
                                      message, result,timeout, semaphore)
        
        if result[destination_peer_id]['status'] != 'SUCCESSFUL':
            return
        
        sign = result[destination_peer_id]['signature_data']
        msg = result[destination_peer_id]['data']
        encoded_message = json.dumps(msg)
        commitments_dict = message['parameters']['commitments_list']
        aggregated_public_nonce = TSS.code_to_pub(sign['aggregated_public_nonce'])
        
        res = TSS.frost_verify_single_signature(sign['id'], encoded_message, 
                                                commitments_dict,
                                                aggregated_public_nonce, 
                                                dkg_key['public_shares'][sign['id']], 
                                                sign, dkg_key['public_key'])
        if not res:
            result[destination_peer_id]['status'] = 'MALICIOUS'
