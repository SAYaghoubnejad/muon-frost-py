from common.libp2p_base import Libp2pBase
from abstract.dns import DNS
from common.libp2p_config import PROTOCOLS_ID
from common.TSS.tss import TSS
from common.utils import Utils

from common.utils import RequestObject
from typing import List, Dict, Type
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from libp2p.peer.id import ID as PeerID

import types
import pprint
import trio
import logging
import json
import timeit

class DkgApplicator(Libp2pBase):
    """
    SignatureAggregator class inherits from Libp2pBase, provides functionality for DKG (Distributed Key Generation)
    protocol over a libp2p network.
    """

    def __init__(self, address: Dict[str, str], secret: str, dns: DNS,
                  data_manager: object, penalty_class_type: Type,
                  node_evaluator_type: Type,
                  max_workers: int = 0, default_timeout: int = 200) -> None:
        """
        Initialize a new SignatureAggregator instance.
        
        :param address: A dictionary containing the IP and port for the SignatureAggregator node.
        :param secret: Secret key for the SignatureAggregator node.
        :param dns: DNS resolver instance.
        """
        super().__init__(address, secret)
        self.dns_resolver: DNS = dns
        self.node_evaluator = node_evaluator_type(data_manager, penalty_class_type)
        self.token = ''
        if max_workers != 0:
            self.semaphore = trio.Semaphore(max_workers)
        else:
            self.semaphore = None
        self.default_timeout = default_timeout

    def _gather_round2_data(self, peer_id: str, data: Dict) -> List:
        """
        Collects round 2 data for a specific peer_id.

        :param peer_id: The ID of the peer.
        :param data: The data dictionary from round 1.
        :return: A list of data entries for the specified peer.
        """
        round2_data = []
        for _, round_data in data.items():
            for entry in round_data['broadcast']:
                if entry['receiver_id'] == peer_id:
                    round2_data.append(entry)
        return round2_data

    async def request_dkg(self, threshold: int, n: int, all_nodes: List[str], app_name: str, seed: int) -> Dict:
        """
        Initiates the DKG protocol with the specified parties.

        :param threshold: The threshold number of parties needed to reconstruct the key.
        :param num_parties: The total number of parties involved in the DKG.
        :param party_ids: List of party identifiers.
        :param app_name: The name of app for which the key is generated.
        :return: A dictionary containing the DKG public key and shares.
        """
        # Choose subnet from node peer IDs.
        party = Utils.get_new_random_subset(all_nodes, seed, n)
        logging.debug(f'Chosen peer IDs: {party}')

        dkg_id = Utils.generate_random_uuid()
        self.node_evaluator.data_manager.setup_table(dkg_id)
        party = self.node_evaluator.get_new_party(dkg_id, 'get_new_party', party)

        if len(party) < threshold:
            response = {
                'result': 'FAIL',
                "dkg_id": None,
            }
            logging.error(f'DKG id {dkg_id} has FAILED due to insufficient number of available nodes')
            return response
        
        
        
        # Execute Round 1 of the protocol
        call_method = "round1"

        parameters = {
            "party": party,
            "dkg_id": dkg_id,
            'app_name': app_name,
            'threshold': threshold,
        }
        request_object = RequestObject(dkg_id, call_method, self.token, parameters)
        round1_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, 
                                   PROTOCOLS_ID[call_method], request_object.get(), round1_response, self.default_timeout, self.semaphore)

        logging.debug(f'Round1 dictionary response: \n{pprint.pformat(round1_response)}')
        is_complete = self.node_evaluator.evaluate_dkg(dkg_id, 'round1', round1_response)
        
        if not is_complete:
            response = {
                'result': 'FAIL',
                "dkg_id": dkg_id,
            }
            logging.info(f'DKG request response: {response}')
            return response
        
        # TODO: error handling (if verification failed)
        # check validation of each node
        for peer_id, data in round1_response.items():
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(self.dns_resolver.lookup(peer_id)['public_key'])
            
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            logging.debug(f'Verification of sent data from {peer_id}: {public_key.verify(data_bytes, validation)}')

        # Execute Round 2 of the protocol
        call_method = "round2"
        parameters = {
            "dkg_id": dkg_id,
            'broadcasted_data': round1_response
        }
        request_object = RequestObject(dkg_id, call_method, self.token, parameters)

        round2_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, 
                                   PROTOCOLS_ID[call_method], request_object.get(), round2_response, self.default_timeout, self.semaphore)

        logging.debug(f'Round2 dictionary response: \n{pprint.pformat(round2_response)}')
        is_complete = self.node_evaluator.evaluate_dkg(dkg_id, 'round2', round2_response)

        if not is_complete:
            response = {
                'result': 'FAIL',
                "dkg_id": dkg_id,
            }
            logging.info(f'DKG request response: {response}')
            return response

        # Execute Round 3 of the protocol
        call_method = "round3"
        
        round3_response = {}
        
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                parameters = {
                    "dkg_id": dkg_id,
                    'send_data': self._gather_round2_data(peer_id, round2_response)
                }
                request_object = RequestObject(dkg_id, call_method, self.token, parameters)

                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, 
                                   PROTOCOLS_ID[call_method], request_object.get(), round3_response, self.default_timeout, self.semaphore)

        logging.debug(f'Round3 dictionary response: \n{pprint.pformat(round3_response)}')
        
        is_complete = self.node_evaluator.evaluate_dkg(dkg_id, 'round3', round3_response, round1_response, round2_response)

        if not is_complete:
            response = {
                'result': 'FAIL',
                "dkg_id": dkg_id,
            }
            logging.info(f'DKG request response: {response}')
            return response

        for id1, data1 in round3_response.items():
            for id2, data2 in round3_response.items():
                # TODO: handle this assertion
                assert data1['data']['dkg_public_key'] == data2['data']['dkg_public_key'],\
                    f'The DKG key of node {id1} is not consistance with the DKG key of node {id2}'
        
        public_key = list(round3_response.values())[0]['data']['dkg_public_key']
        public_shares = {}
        validations = {}
        for id, data in round3_response.items():
            public_shares[int.from_bytes(PeerID.from_base58(id).to_bytes(), 'big')] = data['data']['public_share']
            validations[int.from_bytes(PeerID.from_base58(id).to_bytes(), 'big')] = data['validation']
        
        response = {
            'dkg_id': dkg_id,
            'public_key': public_key,
            'public_shares': public_shares,
            'party': party,
            'validations': validations,
            'result': 'SUCCESSFUL'
        }
        logging.info(f'DKG response: {response}')
        return response
    

    