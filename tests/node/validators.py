from frost_mpc.abstract.validators import Validators
from node_confg import VALIDATED_CALLERS
from libp2p.typing import TProtocol

from typing import Dict
import hashlib
import json


class NodeValidators(Validators):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def caller_validator(sender_id: str, protocol: TProtocol):
        if protocol in VALIDATED_CALLERS.get(str(sender_id), {}):
            return True
        return False

    @staticmethod
    def data_validator(input_data: Dict):
        result = {
            'data': input_data
        }
        hash_obj = hashlib.sha3_256(json.dumps(result['data']).encode())
        hash_hex = hash_obj.hexdigest()
        result['hash'] = hash_hex
        return result
