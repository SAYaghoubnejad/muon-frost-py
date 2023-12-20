from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.peer.id import ID as PeerID

import logging
import uuid
import secrets
import random
from typing import List, Dict
import requests


class Utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def generate_random_uuid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def get_new_random_subset(list: List, seed: int, subset_size: int) -> None:
        random.seed(seed)
        random_subset = random.sample(list, subset_size)
        return random_subset

    @staticmethod
    def generate_secret_and_peer_id() -> Dict[str, str]:
        secret = secrets.token_bytes(32)
        key_pair = create_new_key_pair(secret)
        peer_id: PeerID = PeerID.from_pubkey(key_pair.public_key)
        return {
            'secret': secret.hex(),
            'private_key': key_pair.private_key.serialize().hex(),
            'public_key': key_pair.public_key.serialize().hex(),
            'peer_id': peer_id.to_base58()
        }

    @staticmethod
    def get_request(url) -> Dict:
        try:
            result = requests.get(url).json()
            return result
        except Exception as e:
            logging.error(
                f'get_request => Exception occurred: {type(e).__name__}: {e}')
            return None


class RequestObject:
    def __init__(self, request_id: str, call_method: str, parameters: Dict,
                 input_data: Dict = None) -> None:
        self.request_id: str = request_id
        self.call_method: str = call_method
        self.parameters: Dict = parameters
        self.input_data = input_data

    def get(self):
        result = {
            'request_id': f'{self.request_id}_{self.call_method}',
            'method': self.call_method,
            'parameters': self.parameters
        }
        if self.input_data:
            result['input_data'] = self.input_data
        return result
