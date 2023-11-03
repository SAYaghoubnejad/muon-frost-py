from Common.libp2p_base import Libp2pBase
from typing import List, Dict
from Common.dns import DNS
from Common.libp2p_config import PROTOCOLS_ID

import trio
import logging

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
        response = {}
        async with trio.open_nursery() as nursery:
            for peer_id in party:
                destination_address = DNS.lookup(peer_id)
                nursery.start_soon(self.send, destination_address, peer_id, PROTOCOLS_ID[callMethod], data, response)

        