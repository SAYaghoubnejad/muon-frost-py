from muon_frost_py.common.libp2p_base import Libp2pBase
from muon_frost_py.abstract.dns import DNS
from muon_frost_py.common.libp2p_config import PROTOCOLS_ID
from muon_frost_py.common.TSS.tss import TSS
from muon_frost_py.common.utils import Utils

from muon_frost_py.common.utils import RequestObject
from muon_frost_py.sa.utils import Wrappers
from typing import List, Dict, Type
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from libp2p.peer.id import ID as PeerID

import types
import pprint
import trio
import logging
import json
import timeit

class SA(Libp2pBase):
    """
    SignatureAggregator class inherits from Libp2pBase, provides functionality for DKG (Distributed Key Generation)
    protocol over a libp2p network.
    """

    def __init__(self, address: Dict[str, str], secret: str, dns: DNS,
                  data_manager: object, penalty_class_type: Type,
                  node_evaluator_type: Type, registry_url: str,
                  max_workers: int = 0, default_timeout: int = 200) -> None:
        """
        Initialize a new SignatureAggregator instance.
        
        :param address: A dictionary containing the IP and port for the SignatureAggregator node.
        :param secret: Secret key for the SignatureAggregator node.
        :param dns: DNS resolver instance.
        """
        super().__init__(address, secret)
        self.dns_resolver: DNS = dns
        self.__nonces: Dict[str, list[Dict]] = {}
        self.node_evaluator = node_evaluator_type(data_manager, penalty_class_type)
        self.registry_url = registry_url
        self.token = ''
        if max_workers != 0:
            self.semaphore = trio.Semaphore(max_workers)
        else:
            self.semaphore = None
        self.default_timeout = default_timeout
    def salam(self):
        logging.info('salam!')
    async def maintain_nonces(self, min_number_of_nonces: int=10, sleep_time: int=2) -> None:
        """
        Continuously maintains a list of nonces for each peer.

        :param peer_ids: List of peer IDs to maintain nonces for.
        :param min_nonce_count: Minimum number of nonces to maintain for each peer.
        :param sleep_duration: Duration to sleep before checking again (in seconds).
        """
        call_method = "generate_nonces"
        self.node_evaluator.data_manager.setup_table('nonces')
        while True:
            average_time = []
            peer_ids = self.dns_resolver.get_all_nodes()
            for peer_id in peer_ids:
                self.__nonces.setdefault(peer_id, [])
                if len(self.__nonces[peer_id]) >= min_number_of_nonces:
                    continue
                
                start_time = timeit.default_timer()
                req_id = Utils.generate_random_uuid()

                parameters = {
                    'number_of_nonces': min_number_of_nonces * 10,
                }
                request_object = RequestObject(req_id, call_method, self.token, parameters)

                nonces = {}
                destination_address = self.dns_resolver.lookup_node(peer_id)
                await self.send(destination_address, peer_id,
                                    PROTOCOLS_ID[call_method], request_object.get(), nonces, self.default_timeout, self.semaphore)

                logging.debug(f'Nonces dictionary response: \n{pprint.pformat(nonces)}')
                is_completed = self.node_evaluator.evaluate_responses('nonces', peer_id, nonces)

                if is_completed:
                    self.__nonces[peer_id] += nonces[peer_id]['nonces']
                
                end_time = timeit.default_timer()
                logging.debug(f'Getting nonces from peer ID {peer_id} takes {end_time - start_time} seconds.')
                average_time.append(end_time-start_time)
                await trio.sleep(sleep_time)
            average_time = sum(average_time) / len(average_time)
            logging.info(f'Nonce generation average time from all nodes: {average_time}')
    
    async def maintain_dkg_list(self):
        self.node_evaluator.data_manager.setup_table('dkg_list')
        while True:
            new_data: Dict = Utils.get_request(self.registry_url)
            if not new_data:
                await trio.sleep(0.5)
                continue
            for id, data in new_data.items():
                self.node_evaluator.data_manager.save_data('dkg_list', id, data)
            await trio.sleep(5 * 60) # wait for 5 mins


    async def get_commitments(self, party: List[str], timeout: int = 5) -> Dict:
        """
        Retrieves a dictionary of commitments from the nonces for each party.

        :param party: List of party identifiers.
        :return: A dictionary of commitments for each party.
        """
        commitments_dict = {}
        peer_ids_with_timeout = {}
        for peer_id in party:
            with trio.move_on_after(timeout) as cancel_scope:
                while not self.__nonces.get(peer_id):
                    await trio.sleep(0.1)
                
                commitment = self.__nonces[peer_id].pop()
                commitments_dict[peer_id] = commitment
        
            if cancel_scope.cancelled_caught:
                timeout_response = {
                    "status": "TIMEOUT",
                    "error": "Communication timed out",
                }
                peer_ids_with_timeout[peer_id] = timeout_response
        
        
        if len(peer_ids_with_timeout) > 0:
            self.node_evaluator.evaluate_responses('nonces', peer_id, peer_ids_with_timeout)
            logging.warning(f'get_commitments => Timeout error occurred. peer ids with timeout: {peer_ids_with_timeout}')
        return commitments_dict
    
    
        
    async def request_signature(self, dkg_key: Dict, sign_party_num: int, 
                                app_request_id: str, app_method: str, 
                                app_params: Dict, app_sign_params: Dict, 
                                app_hash: str, app_result: Dict) -> Dict:
        """
        Requests signatures from the specified parties for a given message.

        :param dkg_key: The DKG key information.
        :param sign_party_num: number of parties to sign the message.
        :return: The aggregated signature.
        """
        call_method = "sign"
        dkg_id = dkg_key['dkg_id']
        party = dkg_key['party']
        sign_party = self.node_evaluator.get_new_party(dkg_id, 'get_new_party', party, sign_party_num)
        commitments_dict = await self.get_commitments(sign_party, self.default_timeout)
        
        while len(commitments_dict) < len(sign_party):
            logging.warning('Retrying to get commitments with the new signing party...')
            sign_party = self.node_evaluator.get_new_party(dkg_id, 'get_new_party', party, sign_party_num)
            if len(sign_party) < sign_party_num:
                logging.error(f'DKG id {dkg_id} has FAILED due to insufficient number of available nodes')
                return {
                'result': 'FAIL',
                }
            commitments_dict = await self.get_commitments(sign_party, self.default_timeout)

                
        parameters = {
            "dkg_id": dkg_id,
            'commitments_list': commitments_dict,
        }
        app_data = {
            'app_request_id': app_request_id,
            'app_method': app_method,
            'app_params': app_params,
            'app_result': app_result,
            'app_sign_params': app_sign_params,
            'app_hash': app_hash,
        }
        request_object = RequestObject(dkg_id, call_method, self.token, parameters, app_data)

        signatures = {}
        async with trio.open_nursery() as nursery:
            for peer_id in sign_party:
                destination_address = self.dns_resolver.lookup_node(peer_id)

                
                nursery.start_soon(Wrappers.sign, self.send, dkg_key, destination_address, peer_id, 
                                   PROTOCOLS_ID[call_method], request_object.get(), signatures, 
                                   self.default_timeout, self.semaphore)
        
        now = timeit.default_timer()
        logging.debug(f'Signatures dictionary response: \n{pprint.pformat(signatures)}')
        
        

        

        message = [i['data'] for i in signatures.values()][0]
        encoded_message = json.dumps(message)
        signs = [i['signature_data'] for i in signatures.values()]
        aggregated_public_nonces = [i['signature_data']['aggregated_public_nonce'] for i in signatures.values()]
        if not Utils.check_list_equality(aggregated_public_nonces):
            aggregated_public_nonce = TSS.frost_aggregate_nonce(encoded_message, commitments_dict, dkg_key['public_key'])
            aggregated_public_nonce = TSS.pub_to_code(aggregated_public_nonce)
            for peer_id, data in signatures.items():
                if data['signature_data']['aggregated_public_nonce'] != aggregated_public_nonce:
                    data['status'] = 'MALICIOUS'
        
        is_complete = self.node_evaluator.evaluate_responses(dkg_id, 'sign', signatures)

        if not is_complete:
            response = {
                'result': 'FAIL'
            }
            logging.info(f'Signature response: {response}')
            return response
        aggregated_public_nonce = TSS.code_to_pub(aggregated_public_nonces[0])
        aggregated_sign = TSS.frost_aggregate_signatures(encoded_message, signs, 
                                                        aggregated_public_nonce, 
                                                        dkg_key['public_key'])
        if TSS.frost_verify_group_signature(aggregated_sign):
            aggregated_sign['result'] = 'SUCCESSFUL'
            logging.info(f'Signature request response: {aggregated_sign["result"]}')
            then = timeit.default_timer()
            logging.debug(f'Aggregating the signatures takes {then - now} seconds.')
        else:
            aggregated_sign['result'] = 'NOT_VERIFIED'

        return aggregated_sign
