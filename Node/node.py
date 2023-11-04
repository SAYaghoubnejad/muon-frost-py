from Common.libp2p_base import Libp2pBase
from Common.libp2p_config import PROTOCOLS_ID
from Node.distributed_key import DistributedKey
from libp2p.network.stream.net_stream_interface import INetStream
from typing import Dict, List

import json


class Node(Libp2pBase):
    def __init__(self, address: Dict[str, str], secret: str) -> None:
        super().__init__(address, secret)
        self.distributed_keys: Dict[str, DistributedKey] = {}

        # Define handlers for various protocol methods
        handlers = {
            'round1': self.round1_handler,
            # 'round2': lambda stream: _round2(stream, node),
            # 'peerExchange': lambda stream: _peerExchange(stream, node),
            # 'generateNonces': lambda stream: _generateNonces(stream, node),
            # 'sign': lambda stream: _sign(stream, node),
        }
        self.set_protocol_and_handler(PROTOCOLS_ID, handlers)

    # Interface
    def __add_new_key(self, dkg_id: str, threshold, n, party: List[str]) -> None:
        assert len(party) == n, f'There number of node in party must be equal to n for app {dkg_id}'
        assert self.peer_id in party, f'This node is not amoung specified party for app {dkg_id}'
        assert threshold <= n, f'Threshold must be <= n for app {dkg_id}'

        partners = party
        partners.remove(self.peer_id)
        self.distributed_keys[dkg_id] = DistributedKey(dkg_id, threshold, n, self.peer_id, partners) 

    # Interface
    def get_distributed_key(self, dkg_id: str) -> DistributedKey:
        return self.distributed_keys[dkg_id]
    
    async def round1_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        msg = await stream.read()
        msg = msg.decode("utf-8")
        data = json.loads(msg)

        # Extract requestId, method, and parameters from the message
        request_id = data["requestId"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']

        self.__add_new_key(
            dkg_id, 
            parameters['threshold'], 
            parameters['n'],
            parameters['party']
            )
        
        broadcast_data = self.distributed_keys[dkg_id].round1()
        broadcast_bytes = json.dumps(broadcast_data).encode('utf-8')
        # Prepare the response data
        data = {
            "broadcast": broadcast_data,
            'validation': self._key_pair.private_key.sign(broadcast_bytes).hex(),
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
        except Exception as e:
            # TODO: use logging
            print(f"An exception of type {type(e).__name__} occurred: {e}")
        
        await stream.close()