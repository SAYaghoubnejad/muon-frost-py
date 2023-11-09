from common.libp2p_base import Libp2pBase
from common.libp2p_config import PROTOCOLS_ID
from common.dns import DNS
from common.data_manager import DataManager
from distributed_key import DistributedKey
from libp2p.network.stream.net_stream_interface import INetStream
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from typing import Dict, List

import json
import logging

# TODO: remove dkg upon complaint

# TODO: add requset caller (sender) validation
class Node(Libp2pBase):
    def __init__(self, data_manager: DataManager, address: Dict[str, str], secret: str, dns: DNS) -> None:
        super().__init__(address, secret)
        self.dns: DNS = dns
        self.distributed_keys: Dict[str, DistributedKey] = {}

        # Define handlers for various protocol methods
        handlers = {
            'round1': self.round1_handler,
            'round2': self.round2_handler,
            'round3': self.round3_handler,
            'generate_nonces': self.generate_nonces_handler,
            'sign': self.sign_handler,
        }
        self.set_protocol_and_handler(PROTOCOLS_ID, handlers)
        self.data_manager: DataManager = data_manager
        self.data_manager.setup_database('common_data')

    def __add_new_key(self, dkg_id: str, threshold, n, party: List[str]) -> None:
        assert len(party) == n, f'There number of node in party must be equal to n for app {dkg_id}'
        assert self.peer_id in party, f'This node is not amoung specified party for app {dkg_id}'
        assert threshold <= n, f'Threshold must be <= n for app {dkg_id}'
        # TODO: check if this node is included in party
        partners = party
        partners.remove(self.peer_id)
        self.distributed_keys[dkg_id] = DistributedKey(self.data_manager, dkg_id, threshold, n, self.peer_id, partners) 
    
    async def round1_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)
        
        # Extract requestId, method, and parameters from the message
        request_id = data["requestId"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']

        logging.info(f'{sender_id}{PROTOCOLS_ID["round1"]} Got message: {message}')

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
            logging.info(f'{sender_id}{PROTOCOLS_ID["round1"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error('node => Exception occured :', exc_info=True)
        
        await stream.close()

    async def round2_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract requestId, method, and parameters from the message
        request_id = data["requestId"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        whole_broadcasted_data = parameters['broadcasted_data']

        logging.info(f'{sender_id}{PROTOCOLS_ID["round2"]} Got message: {message}')

        broadcasted_data = []
        for peer_id, data in whole_broadcasted_data.items():
            # TODO: error handling (if verification failed)
            # check validation of each node
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(self.dns.lookup(peer_id)['public_key'])
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            broadcasted_data.append(data['broadcast'])
            logging.info(f'Verification of sent data from {peer_id}: {public_key.verify(data_bytes, validation)}')

        round2_broadcast_data = self.distributed_keys[dkg_id].round2(broadcasted_data)

        data = {
            "broadcast": round2_broadcast_data,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.info(f'{sender_id}{PROTOCOLS_ID["round2"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error('node => Exception occured: ', exc_info=True)
        
        await stream.close()

    async def round3_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract requestId, method, and parameters from the message
        request_id = data["requestId"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        send_data = parameters['send_data']

        logging.info(f'{sender_id}{PROTOCOLS_ID["round3"]} Got message: {message}')
        
        round3_data = self.distributed_keys[dkg_id].round3(send_data)
        
        data = {
            'data': round3_data,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.info(f'{sender_id}{PROTOCOLS_ID["round3"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error('node => Exception occured :', exc_info=True)
        
        await stream.close()

    async def generate_nonces_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract requestId, method, and parameters from the message
        request_id = data["requestId"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        number_of_nonces = parameters['number_of_nonces']

        logging.info(f'{sender_id}{PROTOCOLS_ID["generate_nonces"]} Got message: {message}')
        nonces = DistributedKey.generate_nonces(self.data_manager, self.peer_id, number_of_nonces)

        data = {
            'nonces': nonces,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.info(f'{sender_id}{PROTOCOLS_ID["generate_nonces"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error('node=> Exception occured :', exc_info=True)
        
        await stream.close()

    async def sign_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract requestId, method, and parameters from the message
        request_id = data["requestId"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        commitments_list = parameters['commitments_list']
        message = parameters['message']

        logging.info(f'{sender_id}{PROTOCOLS_ID["sign"]} Got message: {message}')

        signature = self.distributed_keys[dkg_id].frost_sign(commitments_list, message)

        data = {
            'data': signature,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.info(f'{sender_id}{PROTOCOLS_ID["sign"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error('node=> Exception occured :', exc_info=True)
        
        await stream.close()