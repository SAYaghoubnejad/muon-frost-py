from common.libp2p_base import Libp2pBase
from common.dns import DNS
from common.libp2p_config import PROTOCOLS_ID
from common.TSS.tss import TSS
from typing import List, Dict
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from libp2p.peer.id import ID as PeerID
from pprint import pprint

import trio
import logging
import json

class Gateway(Libp2pBase):
    def __init__(self, address: Dict[str, str], secret: str, dns: DNS) -> None:
        super().__init__(address, secret)
        self.dns: DNS = dns
        self.__nonces: Dict[str, Dict[str, str]] = {}

    def __round2_data_for_peer_id(self, peer_id: str, data: Dict) -> List:
        result = []
        for _, data in data.items():
            for entry in data['broadcast']:
                if entry['receiver_id'] == peer_id:
                    result.append(entry)
        return result 


    async def requset_dkg(self, threshold: int, n: int, party: List[str]) -> Dict:
        # Execute Round 1 of the protocol
        call_method = "round1"
        dkg_id = Libp2pBase.generate_random_uuid()
        data = {
            "requestId": f"{dkg_id}:{call_method}",
            "method": call_method,
            "parameters": {
                "party": party,
                "dkg_id": dkg_id,
                'threshold': threshold,
                'n': n
            },
        }
        round1_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = self.dns.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, round1_response)

        # TODO: check if all responses are SUCCESSFUL and return false otherwise

        # TODO: logging
        # TODO: error handling (if verification failed)
        # check validation of each node
        for peer_id, data in round1_response.items():
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(self.dns.lookup(peer_id)['public_key'])
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            print(f'Verification of sent data from {peer_id}: ', public_key.verify(data_bytes, validation))

        # Execute Round 2 of the protocol
        call_method = "round2"
        data = {
            "requestId": f"{dkg_id}:{call_method}",
            "method": call_method,
            "parameters": {
                "dkg_id": dkg_id,
                'broadcasted_data': round1_response
            },
        }
        round2_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = self.dns.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, round2_response)

        # TODO: check if all responses are SUCCESSFUL and return false otherwise

        # Execute Round 3 of the protocol
        call_method = "round3"
        
        round3_response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                data = {
                    "requestId": f"{dkg_id}:{call_method}",
                    "method": call_method,
                    "parameters": {
                        "dkg_id": dkg_id,
                        'send_data': self.__round2_data_for_peer_id(peer_id, round2_response)
                    },
                }
                destination_address = self.dns.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, round3_response)
                
        # TODO: check if all responses are SUCCESSFUL and return false otherwise
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
            'public_shares': public_shares
        }
        return response
    
    async def maintain_nonces(self, peer_ids: List[str], min_number_of_nonces: int=10, sleep_time: int=2) -> None:
        call_method = "generate_nonces"
        while True:
            for peer_id in peer_ids:
                if len(self.__nonces.setdefault(peer_id, [])) >= min_number_of_nonces:
                    continue

                req_id = Libp2pBase.generate_random_uuid()
                data = {
                "method": call_method,
                "requestId": f"{req_id}_{call_method}",
                "parameters": {
                    'number_of_nonces': min_number_of_nonces * 5,
                    },
                }
                nonces = {}
                destination_address = self.dns.lookup(peer_id)
                await self.send(destination_address, peer_id, PROTOCOLS_ID[call_method], data, nonces)

                 # TODO: check if response is SUCCESSFUL and return false otherwise
                self.__nonces[peer_id] += nonces[peer_id]['nonces']
            await trio.sleep(sleep_time)

    def get_commitments_dict(self, party: List[str]) -> Dict:
        commitments_dict = {}
        for peer_id in party:
            commitment = self.__nonces[peer_id].pop()
            commitments_dict[peer_id] = commitment
        return commitments_dict
       

    # TODO: remove commitments_list
    async def requset_signature(self, dkg_key: Dict, sign_party: List[str], message: str) -> Dict:
        call_method = "sign"
        dkg_id = dkg_key['dkg_id']
        commitments_dict = self.get_commitments_dict(sign_party)
        # TODO: add a function or wrapper to handle data
        data = {
        "method": call_method,
        "requestId": f"{dkg_id}_{call_method}",
        "parameters": {
            "dkg_id": dkg_id,
            'commitments_list': commitments_dict,
            'message': message
        },
        }
        signatures = {}
        async with trio.open_nursery() as nursery:
            for peer_id in sign_party:
                destination_address = self.dns.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[call_method], data, signatures)
        # TODO: check if all responses are SUCCESSFUL and return false otherwise

        # Extract individual signatures and aggregate them
        signs = [i['data'] for i in signatures.values()]
        aggregatedSign = TSS.frost_aggregate_signatures(signs, dkg_key['public_shares'], message, commitments_dict, dkg_key['public_key'])
        
        if TSS.frost_verify_group_signature(aggregatedSign):
            print('Signature is verified:)')
        
        # TODO: handle the condition in which aggregatedSign is not verified 
        return aggregatedSign