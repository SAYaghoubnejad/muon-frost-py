from common.libp2p_base import Libp2pBase
from common.dns import DNS
from common.temp_config import PROTOCOLS_ID
from common.TSS.tss import TSS
from common.utils import Utils
from gateway.temp_config import GATEWAY_TOKEN
from error_handler import ErrorHandler
from typing import List, Dict
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from libp2p.peer.id import ID as PeerID
from pprint import pprint

import trio
import logging
import json

class Gateway(Libp2pBase):
    """
    Gateway class inherits from Libp2pBase, provides functionality for DKG (Distributed Key Generation)
    protocol over a libp2p network.
    """

    def __init__(self, address: Dict[str, str], secret: str, dns: DNS) -> None:
        """
        Initialize a new Gateway instance.
        
        :param address: A dictionary containing the IP and port for the gateway node.
        :param secret: Secret key for the gateway node.
        :param dns: DNS resolver instance.
        """
        super().__init__(address, secret)
        self.dns_resolver: DNS = dns
        self.__nonces: Dict[str, list[Dict]] = {}
        self.error_handler = ErrorHandler()

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

    # TODO: update app_name
    async def request_dkg(self, threshold: int, n: int, party: List[str], app_name: str) -> Dict:
        """
        Initiates the DKG protocol with the specified parties.

        :param threshold: The threshold number of parties needed to reconstruct the key.
        :param num_parties: The total number of parties involved in the DKG.
        :param party_ids: List of party identifiers.
        :param app_name: The name of app for which the key is generated.
        :return: A dictionary containing the DKG public key and shares.
        """
        dkg_id = Utils.generate_random_uuid()
        # Execute Round 1 of the protocol
        call_method = "round1"
        data = {
            "request_id": f"{dkg_id}_{call_method}",
            "method": call_method,
            'gateway_authorization': GATEWAY_TOKEN,
            "parameters": {
                "party": party,
                "dkg_id": dkg_id,
                'app_name': app_name,
                'threshold': threshold,
                'n': n
            },
        }
        round1_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, round1_response)

        is_complete = self.error_handler.check_responses(round1_response)

        if not is_complete:
            return {
                'result': 'FAIL'
            }
        
        # TODO: error handling (if verification failed)
        # check validation of each node
        for peer_id, data in round1_response.items():
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(self.dns_resolver.lookup(peer_id)['public_key'])
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            logging.info(f'Verification of sent data from {peer_id}: {public_key.verify(data_bytes, validation)}')

        # Execute Round 2 of the protocol
        call_method = "round2"
        data = {
            "request_id": f"{dkg_id}_{call_method}",
            "method": call_method,
            'gateway_authorization': GATEWAY_TOKEN,
            "parameters": {
                "dkg_id": dkg_id,
                'broadcasted_data': round1_response
            },
        }
        round2_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, round2_response)

        is_complete = self.error_handler.check_responses(round2_response)

        if not is_complete:
            return {
                'result': 'FAIL'
            }

        # Execute Round 3 of the protocol
        call_method = "round3"
        
        round3_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                data = {
                    "request_id": f"{dkg_id}_{call_method}",
                    "method": call_method,
                    'gateway_authorization': GATEWAY_TOKEN,
                    "parameters": {
                        "dkg_id": dkg_id,
                        'send_data': self._gather_round2_data(peer_id, round2_response)
                    },
                }
                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, round3_response)
                
        is_complete = self.error_handler.check_responses(round3_response)

        if not is_complete:
            return {
                'result': 'FAIL'
            }

        for id1, data1 in round3_response.items():
            for id2, data2 in round3_response.items():
                # TODO: handle this assertion
                assert data1['data']['dkg_public_key'] == data2['data']['dkg_public_key'],\
                    f'The DKG key of node {id1} is not consistance with the DGK key of node {id2}'
        
        public_key = round3_response[party[0]]['data']['dkg_public_key']
        public_shares = {}
        for id, data in round3_response.items():
            public_shares[int.from_bytes(PeerID.from_base58(id).to_bytes(), 'big')] = data['data']['public_share']
        response = {
            'dkg_id': dkg_id,
            'public_key': public_key,
            'public_shares': public_shares,
            'party': party,
            'result': 'SUCCESSFUL'
        }
        return response
    
    async def maintain_nonces(self, peer_ids: List[str], min_number_of_nonces: int=10, sleep_time: int=2) -> None:
        """
        Continuously maintains a list of nonces for each peer.

        :param peer_ids: List of peer IDs to maintain nonces for.
        :param min_nonce_count: Minimum number of nonces to maintain for each peer.
        :param sleep_duration: Duration to sleep before checking again (in seconds).
        """
        call_method = "generate_nonces"
        while True:
            for peer_id in peer_ids:
                if len(self.__nonces.setdefault(peer_id, [])) >= min_number_of_nonces:
                    continue

                req_id = Utils.generate_random_uuid()
                data = {
                "method": call_method,
                "request_id": f"{req_id}_{call_method}",
                'gateway_authorization': GATEWAY_TOKEN,
                "parameters": {
                    'number_of_nonces': min_number_of_nonces * 10,
                    },
                }
                nonces = {}
                destination_address = self.dns_resolver.lookup(peer_id)
                await self.send(destination_address, peer_id, PROTOCOLS_ID[call_method], data, nonces)

                self.error_handler.check_responses(nonces)

                self.__nonces[peer_id] += nonces[peer_id]['nonces']
            await trio.sleep(sleep_time)

    def get_commitments(self, party: List[str]) -> Dict:
        """
        Retrieves a dictionary of commitments from the nonces for each party.

        :param party: List of party identifiers.
        :return: A dictionary of commitments for each party.
        """
        # TODO: what if nonces are not ready? (race condition!)
        commitments_dict = {}
        for peer_id in party:
            commitment = self.__nonces[peer_id].pop()
            commitments_dict[peer_id] = commitment
        return commitments_dict
    

    async def request_signature(self, dkg_key: Dict, sign_party_num: int) -> Dict:
        """
        Requests signatures from the specified parties for a given message.

        :param dkg_key: The DKG key information.
        :param sign_party_num: number of parties to sign the message.
        :return: The aggregated signature.
        """
        call_method = "sign"
        dkg_id = dkg_key['dkg_id']
        party = dkg_key['party']
        sign_party = self.error_handler.get_new_party(party, sign_party_num)
        commitments_dict = self.get_commitments(sign_party)
        # TODO: add a function or wrapper to handle data
        data = {
        "method": call_method,
        "request_id": f"{dkg_id}_{call_method}",
        'gateway_authorization': GATEWAY_TOKEN,
        "parameters": {
            "dkg_id": dkg_id,
            'commitments_list': commitments_dict,
        },
        }
        signatures = {}
        async with trio.open_nursery() as nursery:
            for peer_id in sign_party:
                destination_address = self.dns_resolver.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, signatures)
        
        is_complete = self.error_handler.check_responses(signatures)

        if not is_complete:
            return {
                'result': 'FAIL'
            }

        # Extract individual signatures and aggregate them
        signs = [i['signature_data'] for i in signatures.values()]
        # TODO: check if all signed messages are equal
        message = [i['data'] for i in signatures.values()][0]
        encoded_message = json.dumps(message)
        aggregatedSign = TSS.frost_aggregate_signatures(signs, dkg_key['public_shares'], encoded_message, commitments_dict, dkg_key['public_key'])
        
        if TSS.frost_verify_group_signature(aggregatedSign):
            aggregatedSign['result'] = 'SUCCESSFUL'
            logging.warning('Signature is verified:)')
        else:
            aggregatedSign['result'] = 'NOT_VERIFIED'

        return aggregatedSign