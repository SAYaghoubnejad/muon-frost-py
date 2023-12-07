from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.peer.id import ID as PeerID


import logging
import uuid
import secrets
import random
from typing import List, Dict
import requests
import datetime 

class Utils:
    def __init__(self) -> None:
        pass


        
    @staticmethod
    def generate_random_uuid() -> str:
        """
        Generates a random UUID.

        Returns:
        str: A randomly generated UUID.
        """
        return str(uuid.uuid4())
    
    
    @staticmethod
    def get_new_random_subset(list: List, seed: int, subset_size: int) -> None:
        random.seed(seed)  
        random_subset = random.sample(list, subset_size)
        return random_subset

    
    @staticmethod
    def get_today_last_block_hash(hour: int) -> str:
        current = datetime.datetime.utcnow()
        desired = datetime.time(hour, 0)
        date = datetime.datetime(current.year, current.month, 
                                        current.day, desired.hour, desired.minute, 
                                        desired.second, tzinfo = datetime.timezone.utc)
        
        delta = date - datetime.timedelta(hours = 1)
        period = f'{delta.strftime("%Y-%m-%d %H:%M:%S")}..{date.strftime("%Y-%m-%d %H:%M:%S")}'
        api_url = f"https://api.blockchair.com/bitcoin/blocks?q=time({period})&limit=1&sort=time_desc"
        response = requests.get(api_url)
        data = response.json()
        block_data = data['data'][0]
        block_hash = block_data['hash']
        return block_hash
        

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
    def check_list_equality(list) -> bool:
        if len(set(list)) == 1:
            return True
        else:
            return False
    
    @staticmethod
    def get_request(url) -> Dict:
        try:
            result = requests.get(url).json()
            return result
        except Exception as e:
            return None


class RequestObject:
    def __init__(self, request_id: str, call_method: str, parameters: Dict,
                 app_data: Dict = None) -> None:
        self.request_id: str = request_id
        self.call_method: str = call_method
        self.parameters: Dict = parameters
        self.app_data = app_data

    def get(self):
        result = {
            "request_id": f"{self.request_id}_{self.call_method}",
            "method": self.call_method,
            "parameters": self.parameters
        }
        if self.app_data:
            result['app_data'] = self.app_data
        return result