from Common.libp2p_base import Libp2pBase
from Common.libp2p_config import PROTOCOLS_ID
from Common.dns import DNS
from Node.distributed_key import DistributedKey
from libp2p.network.stream.net_stream_interface import INetStream
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from typing import Dict, List

import json


class Node(Libp2pBase):
    def __init__(self, address: Dict[str, str], secret: str, dns: DNS) -> None:
        super().__init__(address, secret)
        self.dns: DNS = dns
        self.distributed_keys: Dict[str, DistributedKey] = {}

        # Define handlers for various protocol methods
        handlers = {
            'round1': self.round1_handler,
            'round2': self.round2_handler,
            'round3': self.round3_handler,
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
        
        round1_broadcast_data = self.distributed_keys[dkg_id].round1()
        broadcast_bytes = json.dumps(round1_broadcast_data).encode('utf-8')
        # Prepare the response data
        data = {
            "broadcast": round1_broadcast_data,
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

    async def round2_handler(self, stream: INetStream) -> None:
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
        whole_broadcasted_data = parameters['broadcasted_data']

        broadcasted_data = []
        for peer_id, data in whole_broadcasted_data.items():
            # TODO: logging
            # TODO: error handling (if verification failed)
            # check validation of each node
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(self.dns.lookup(peer_id)['public_key'])
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            print(f'Verification of sent data from {peer_id}: ', public_key.verify(data_bytes, validation))
            broadcasted_data.append(data['broadcast'])

        self.distributed_keys[dkg_id].save_data('round1_broadcasted_data', broadcasted_data)

        round2_broadcast_data = self.distributed_keys[dkg_id].round2()

        data = {
            "broadcast": round2_broadcast_data,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
        except Exception as e:
            # TODO: use logging
            print(f"An exception of type {type(e).__name__} occurred: {e}")
        
        await stream.close()

    async def round3_handler(self, stream: INetStream) -> None:
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
        send_data = parameters['send_data']

        self.distributed_keys[dkg_id].save_data('round2_encrypted_data', send_data)

        round3_data = self.distributed_keys[dkg_id].round3()

        data = {
            'data': round3_data,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
        except Exception as e:
            # TODO: use logging
            print(f"An exception of type {type(e).__name__} occurred: {e}")
        
        await stream.close()