from Common.libp2p_base import Libp2pBase
from Common.dns import DNS
from Common.libp2p_config import PROTOCOLS_ID
from typing import List, Dict
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from pprint import pprint

import trio
import logging
import json

class Gateway(Libp2pBase):
    def __init__(self, address: Dict[str, str], secret: str, dns: DNS) -> None:
        super().__init__(address, secret)
        self.dns: DNS = dns

    def __round2_data_for_peer_id(self, peer_id: str, data: Dict) -> List:
        result = []
        for _, data in data.items():
            for entry in data['broadcast']:
                if entry['receiver_id'] == peer_id:
                    result.append(entry)
        return result 


    async def requset_dkg(self, threshold: int, n: int, party: List[str]):
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
        pprint(round3_response)
        