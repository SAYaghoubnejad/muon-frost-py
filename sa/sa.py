from muon_frost_py.common.libp2p_base import Libp2pBase
from muon_frost_py.abstract.node.node_info import NodeInfo
from muon_frost_py.common.libp2p_config import PROTOCOLS_ID
from muon_frost_py.common.pyfrost.tss import TSS
from muon_frost_py.common.utils import Utils

from muon_frost_py.common.utils import RequestObject
from muon_frost_py.sa.utils import Wrappers
from typing import List, Dict

from libp2p.host.host_interface import IHost

import pprint
import trio
import logging
import json


class SA(Libp2pBase):
    """
    SignatureAggregator class inherits from Libp2pBase, provides functionality for DKG (Distributed Key Generation)
    protocol over a libp2p network.
    """

    def __init__(self, address: Dict[str, str], secret: str, node_info: NodeInfo,
                  max_workers: int = 0, default_timeout: int = 200, host: IHost = None) -> None:
       
        super().__init__(address, secret, host)
        self.node_info: NodeInfo = node_info
        self.token = ''
        if max_workers != 0:
            self.semaphore = trio.Semaphore(max_workers)
        else:
            self.semaphore = None
        self.default_timeout = default_timeout
    
    async def request_nonces(self, party: List, number_of_nonces: int = 10):
        nonces = {}
        for peer_id in party:
            req_id = Utils.generate_random_uuid()
            call_method = "generate_nonces"
            parameters = {
                'number_of_nonces': number_of_nonces,
            }
            request_object = RequestObject(req_id, call_method, parameters)
            
            destination_address = self.node_info.lookup_node(peer_id)
            await self.send(destination_address, peer_id,
                                PROTOCOLS_ID[call_method], request_object.get(), nonces, self.default_timeout, self.semaphore)

            logging.debug(f'Nonces dictionary response: \n{pprint.pformat(nonces)}')
        return nonces
    
    async def request_signature(self, dkg_key: Dict, commitments_dict: Dict,
                                input_data: Dict, sign_party: List) -> Dict:
        call_method = "sign"
        dkg_id = dkg_key['dkg_id']
        
        if not set(sign_party).issubset(set(dkg_key['party'])):
            response = {
                'result': 'FAILED',
                'signatures': None
            }
            return response
        
        parameters = {
            "dkg_id": dkg_id,
            'commitments_list': commitments_dict,
        }
        request_object = RequestObject(dkg_id, call_method, parameters, input_data)

        signatures = {}
        async with trio.open_nursery() as nursery:
            for peer_id in sign_party:
                destination_address = self.node_info.lookup_node(peer_id)
                nursery.start_soon(Wrappers.sign, self.send, dkg_key, destination_address, peer_id, 
                                   PROTOCOLS_ID[call_method], request_object.get(), signatures, 
                                   self.default_timeout, self.semaphore)
        logging.debug(f'Signatures dictionary response: \n{pprint.pformat(signatures)}')
        
        message = [i['data'] for i in signatures.values()][0]
        str_message = json.dumps(message)
        signs = [i['signature_data'] for i in signatures.values()]
        aggregated_public_nonces = [i['signature_data']['aggregated_public_nonce'] for i in signatures.values()]
        response = {
            'result': 'SUCCESSFUL',
            'signatures': None
        }
        if not Utils.check_list_equality(aggregated_public_nonces):
            aggregated_public_nonce = TSS.frost_aggregate_nonce(str_message, commitments_dict, dkg_key['public_key'])
            aggregated_public_nonce = TSS.pub_to_code(aggregated_public_nonce)
            for peer_id, data in signatures.items():
                if data['signature_data']['aggregated_public_nonce'] != aggregated_public_nonce:
                    data['status'] = 'MALICIOUS'
                    response['result'] = 'FAILED'
        
        
        
        if response['result'] == 'FAILED':
            response = {
                'result': 'FAILED',
                'signatures': signatures
            }
            logging.info(f'Signature response: {response}')
            return response
        aggregated_public_nonce = TSS.code_to_pub(aggregated_public_nonces[0])
        aggregated_sign = TSS.frost_aggregate_signatures(str_message, signs, 
                                                        aggregated_public_nonce, 
                                                        dkg_key['public_key'])
        aggregated_sign['signatures'] = signatures
        if TSS.frost_verify_group_signature(aggregated_sign):
            aggregated_sign['result'] = 'SUCCESSFUL'
            logging.info(f'Signature request response: {aggregated_sign["result"]}')
        else:
            aggregated_sign['result'] = 'FAILED'
        return aggregated_sign
