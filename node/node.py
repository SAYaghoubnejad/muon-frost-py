from muon_frost_py.common.libp2p_base import Libp2pBase
from muon_frost_py.common.libp2p_config import PROTOCOLS_ID
from muon_frost_py.abstract.node.node_info import NodeInfo
from muon_frost_py.abstract.node.data_manager import DataManager
from muon_frost_py.common.utils import Utils
from muon_frost_py.common.TSS.tss import TSS

from .decorators import auth_decorator
from .unpacked_stream import UnpackedStream
from .distributed_key import DistributedKey
from libp2p.network.stream.net_stream_interface import INetStream
from libp2p.crypto.secp256k1 import Secp256k1PublicKey
from typing import Dict, List

import json
import logging
import types

class Node(Libp2pBase):
    def __init__(self, data_manager: DataManager, address: Dict[str, str],
                  secret: str, node_info: NodeInfo, caller_validator: types.FunctionType,
                  data_validator: types.FunctionType) -> None:
        super().__init__(address, secret)
        self.node_info: NodeInfo = node_info
        self.distributed_keys: Dict[str, DistributedKey] = {}
        self.caller_validator = caller_validator
        self.data_validator = data_validator
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
        self.dkg_data = {}
        

    def __add_new_key(self, dkg_id: str, threshold, party: List[str], app_name: str) -> None:
        assert self.peer_id in party, f'This node is not amoung specified party for app {dkg_id}'
        assert threshold <= len(party), f'Threshold must be <= n for app {dkg_id}'
        # TODO: check if this node is included in party
        
        partners = party
        partners.remove(self.peer_id)
        self.dkg_data[dkg_id] = {'app_name': app_name}


        self.distributed_keys[dkg_id] = DistributedKey(self.data_manager, dkg_id, threshold, len(party), self.peer_id, partners) 
    
    def __remove_key(self, dkg_id: str) -> None:
        if self.distributed_keys.get(dkg_id) is not None:
            del self.distributed_keys[dkg_id]
        


        
    
    @auth_decorator
    async def round1_handler(self, unpacked_stream: UnpackedStream) -> None:
        # Read and decode the message from the network stream
        message = await unpacked_stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)
        
        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = unpacked_stream.sender_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        app_name = parameters['app_name']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["round1"]} Got message: {message}')

        self.__add_new_key(
            dkg_id, 
            parameters['threshold'], 
            parameters['party'],
            app_name
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
            await unpacked_stream.stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["round1"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node => Exception occurred: {type(e).__name__}: {e}')
        
        await unpacked_stream.stream.close()

    @auth_decorator
    async def round2_handler(self, unpacked_stream: UnpackedStream) -> None:
        # Read and decode the message from the network stream
        message = await unpacked_stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = unpacked_stream.sender_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        whole_broadcasted_data = parameters['broadcasted_data']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["round2"]} Got message: {message}')

        broadcasted_data = []
        for peer_id, data in whole_broadcasted_data.items():
            # TODO: error handling (if verification failed)
            # check validation of each node
            data_bytes = json.dumps(data['broadcast']).encode('utf-8')
            validation = bytes.fromhex(data['validation'])
            public_key_bytes = bytes.fromhex(self.node_info.lookup_node(peer_id)['public_key'])
            public_key = Secp256k1PublicKey.deserialize(public_key_bytes)
            broadcasted_data.append(data['broadcast'])
            logging.debug(f'Verification of sent data from {peer_id}: {public_key.verify(data_bytes, validation)}')

        round2_broadcast_data = self.distributed_keys[dkg_id].round2(broadcasted_data)

        data = {
            "broadcast": round2_broadcast_data,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await unpacked_stream.stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["round2"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node => Exception occurred: {type(e).__name__}: {e}')
        
        await unpacked_stream.stream.close()

    @auth_decorator
    async def round3_handler(self, unpacked_stream: UnpackedStream) -> None:
        # Read and decode the message from the network stream
        message = await unpacked_stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = unpacked_stream.sender_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        send_data = parameters['send_data']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["round3"]} Got message: {message}')
        
        round3_data = self.distributed_keys[dkg_id].round3(send_data)
        
        if round3_data['status'] == 'COMPLAINT':
            self.__remove_key(dkg_id)
        
        round3_data['validation'] = None
        if round3_data['status'] == 'SUCCESSFUL':
            round3_data['validation']: self._key_pair.private_key.sign(round3_data['data']).hex()

        data = {
            "data": round3_data['data'],
            "status": round3_data['status'],
            "validation": round3_data['validation']
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await unpacked_stream.stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["round3"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node => Exception occurred: {type(e).__name__}: {e}')
        
        await unpacked_stream.stream.close()

    @auth_decorator
    async def generate_nonces_handler(self, unpacked_stream: UnpackedStream) -> None:
        # Read and decode the message from the network stream
        message = await unpacked_stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = unpacked_stream.sender_id
        method = data["method"]
        parameters = data["parameters"]
        number_of_nonces = parameters['number_of_nonces']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["generate_nonces"]} Got message: {message}')
        nonces = DistributedKey.generate_nonces(self.data_manager, self.peer_id, number_of_nonces)

        data = {
            'nonces': nonces,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await unpacked_stream.stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["generate_nonces"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node=> Exception occurred: {type(e).__name__}: {e}')
        
        await unpacked_stream.stream.close()

    @auth_decorator
    async def sign_handler(self, unpacked_stream: UnpackedStream) -> None:
        # Read and decode the message from the network stream
        message = await unpacked_stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = unpacked_stream.sender_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        commitments_list = parameters['commitments_list']
        input_data = data['input_data']


        logging.debug(f'{sender_id}{PROTOCOLS_ID["sign"]} Got message: {message}')
        data = self.data_validator(self.distributed_keys[dkg_id].frost_sign, input_data, commitments_list)

        response = json.dumps(data).encode("utf-8")
        try:
            await unpacked_stream.stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["sign"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node=> Exception occurred: {type(e).__name__}: {e}')
        
        await unpacked_stream.stream.close()