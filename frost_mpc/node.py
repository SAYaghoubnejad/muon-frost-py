from .common.libp2p_base import Libp2pBase
from .common.pyfrost.frost import Frost
from .common.libp2p_protocols import PROTOCOLS_ID
from .abstract.node_info import NodeInfo
from .abstract.data_manager import DataManager

from libp2p.network.stream.net_stream_interface import INetStream
from libp2p.peer.id import ID as PeerID
from libp2p.crypto.secp256k1 import Secp256k1PublicKey

from typing import Dict, List

import json
import logging
import types


def auth_decorator(handler):
    async def wrapper(self, stream: INetStream):
        try:
            if self.caller_validator(stream.muxed_conn.peer_id.to_base58(), stream.get_protocol()):
                return await handler(self, stream)
            else:
                logging.error('Node Decorator => Exception occurred. Unauthorized SA.')
                raise Exception("Unauthorized SA")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON data")
    return wrapper


class Node(Libp2pBase):
    def __init__(self, data_manager: DataManager, address: Dict[str, str],
                  secret: str, node_info: NodeInfo, caller_validator: types.FunctionType,
                  data_validator: types.FunctionType) -> None:
        super().__init__(address, secret)
        self.node_info: NodeInfo = node_info
        self.frost_nodes: Dict[str, Frost] = {}
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
        
    def update_distributed_key(self, dkg_id: str) -> None:
        result = self.frost_nodes.get(dkg_id)
        if result is not None:
            return
        # TODO: Implement for retrieve distributed key object
        
    def add_new_key(self, dkg_id: str, threshold, party: List[str], app_name: str) -> None:
        assert self.peer_id in party, f'This node is not amoung specified party for app {dkg_id}'
        assert threshold <= len(party), f'Threshold must be <= n for app {dkg_id}'
        partners = []
        for peer_id in party:
            if peer_id == self.peer_id:
                continue
            partners.append(str(int.from_bytes(PeerID.from_base58(peer_id).to_bytes(), 'big')))
        self.dkg_data[dkg_id] = {'app_name': app_name}

        peer_id_as_int = int.from_bytes(self.peer_id.to_bytes(), 'big')

        self.frost_nodes[dkg_id] = Frost(dkg_id, threshold, len(party), str(peer_id_as_int), partners)
    
    def remove_key(self, dkg_id: str) -> None:
        if self.frost_nodes.get(dkg_id) is not None:
            del self.frost_nodes[dkg_id]
        


        
    
    @auth_decorator
    async def round1_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)
        
        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        app_name = parameters['app_name']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["round1"]} Got message: {message}')

        self.add_new_key(
            dkg_id, 
            parameters['threshold'], 
            parameters['party'],
            app_name
            )
        
        self.update_distributed_key(dkg_id)
        round1_broadcast_data, save_data = self.frost_nodes[dkg_id].dkg_round1()
        self.dkg_data[dkg_id] = save_data
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
            logging.debug(f'{sender_id}{PROTOCOLS_ID["round1"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node => Exception occurred: {type(e).__name__}: {e}')
        
        await stream.close()

    @auth_decorator
    async def round2_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = stream.muxed_conn.peer_id
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

        self.update_distributed_key(dkg_id)
        round2_broadcast_data, save_data = self.frost_nodes[dkg_id].dkg_round2(broadcasted_data, 
                                                                               self.dkg_data[dkg_id]['data'])
        self.dkg_data[dkg_id]['data'].update(save_data['data'])
        self.dkg_data[dkg_id]['round1_broadcasted_data'] = broadcasted_data
        data = {
            "broadcast": round2_broadcast_data,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["round2"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node => Exception occurred: {type(e).__name__}: {e}')
        
        await stream.close()

    @auth_decorator
    async def round3_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        send_data = parameters['send_data']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["round3"]} Got message: {message}')
        
        self.update_distributed_key(dkg_id)
        round3_data = self.frost_nodes[dkg_id].dkg_round3(self.dkg_data[dkg_id]['round1_broadcasted_data'],
                                                          send_data, self.dkg_data[dkg_id]['data'])
        
        if round3_data['status'] == 'COMPLAINT':
            self.remove_key(dkg_id)
        
        round3_data['validation'] = None
        if round3_data['status'] == 'SUCCESSFUL':
            sign_data = json.dumps(round3_data['data']).encode('utf-8')
            round3_data['validation'] = self._key_pair.private_key.sign(sign_data).hex()

        data = {
            "data": round3_data['data'],
            "status": round3_data['status'],
            "validation": round3_data['validation']
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["round3"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node => Exception occurred: {type(e).__name__}: {e}')
        
        await stream.close()

    @auth_decorator
    async def generate_nonces_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        number_of_nonces = parameters['number_of_nonces']

        logging.debug(f'{sender_id}{PROTOCOLS_ID["generate_nonces"]} Got message: {message}')
        peer_id_as_int = int.from_bytes(self.peer_id.to_bytes(), 'big')
        nonces, save_data = Frost.nonce_preprocess(peer_id_as_int, number_of_nonces)
        self.data_manager.set_nonces(save_data)
        data = {
            'nonces': nonces,
            "status": "SUCCESSFUL",
        }
        response = json.dumps(data).encode("utf-8")
        try:
            await stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["generate_nonces"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node=> Exception occurred: {type(e).__name__}: {e}')
        await stream.close()

    @auth_decorator
    async def sign_handler(self, stream: INetStream) -> None:
        # Read and decode the message from the network stream
        message = await stream.read()
        message = message.decode("utf-8")
        data = json.loads(message)

        # Extract request_id, method, and parameters from the message
        request_id = data["request_id"]
        sender_id = stream.muxed_conn.peer_id
        method = data["method"]
        parameters = data["parameters"]
        dkg_id = parameters['dkg_id']
        commitments_list = parameters['commitments_list']
        input_data = data['input_data']


        logging.debug(f'{sender_id}{PROTOCOLS_ID["sign"]} Got message: {message}')
        result = {}
        try:
            result = self.data_validator(input_data)
            self.update_distributed_key(dkg_id)
            nonces = self.data_manager.get_nonces()
            result['signature_data'], remove_data = self.frost_nodes[dkg_id].sign(commitments_list, result['hash'], nonces)
            nonces.remove(remove_data)
            self.data_manager.set_nonces(nonces)
            result['status'] = 'SUCCESSFUL'
        except Exception as e:
            logging.error(f'Node=> Exception occurred: {type(e).__name__}: {e}')
            result = {
                'status': 'FAILED'
            }  
        response = json.dumps(result).encode("utf-8")
        try:
            await stream.write(response)
            logging.debug(f'{sender_id}{PROTOCOLS_ID["sign"]} Sent message: {response.decode()}')
        except Exception as e:
            logging.error(f'Node=> Exception occurred: {type(e).__name__}: {e}')
        
        await stream.close()