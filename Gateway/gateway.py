from Common.libp2p_base import Libp2pBase
from Common.dns import DNS
from Common.libp2p_config import PROTOCOLS_ID
from typing import List, Dict
from libp2p.crypto.secp256k1 import Secp256k1PublicKey

import trio
import logging
import json

class Gateway(Libp2pBase):
    def __init__(self, address: Dict[str, str], secret: str) -> None:
        super().__init__(address, secret)

    async def requset_dkg(self, threshold: int, n: int, party: List[str]):
        # Execute Round 1 of the protocol
        callMethod = "round1"
        dkg_id = Libp2pBase.generate_random_uuid()
        data = {
            "requestId": f"{dkg_id}:{callMethod}",
            "method": callMethod,
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
                destination_address = DNS.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[callMethod], data, round1_response)

        # TODO: check if all responses are SUCCESSFUL and return false otherwise

        # check validation of each node
        for peer_id, data in round1_response.items():
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(DNS.lookup(peer_id)['public_key'])
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            print(f'Verification of sent data from {peer_id}: ', public_key.verify(data_bytes, validation))

        # Execute Round 2 of the protocol
        # callMethod = "round2"
        # dkg_id = Libp2pBase.generate_random_uuid()
        # data = {
        #     "requestId": f"{dkg_id}:{callMethod}",
        #     "method": callMethod,
        #     "parameters": {
        #         "party": party,
        #         "dkg_id": dkg_id,
        #         'threshold': threshold,
        #         'n': n
        #     },
        # }
        # round1_response = {}
        # async with trio.open_nursery() as nursery:
        #     for peer_id in party:
        #         destination_address = DNS.lookup(peer_id)
        #         nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[callMethod], data, round1_response)
        