from typing import Dict, List
import trio
from common.TSS.tss import TSS
class RequestObject:
    def __init__(self, request_id: str, call_method: str, gateway_authorization: str, parameters: Dict) -> None:
        self.request_id: str = request_id
        self.call_method: str = call_method
        self.gateway_authorization: str = gateway_authorization
        self.parameters: Dict = parameters


    def get(self):
        result = {
            "request_id": f"{self.request_id}_{self.call_method}",
            "method": self.call_method,
            'gateway_authorization': self.gateway_authorization,
            "parameters": self.parameters
        }
        return result


class Wrappers:
    @staticmethod
    async def wrapper_frost_verify_single_signature(results: List, *args, **kwargs):
        result = await trio.to_thread.run_sync(
                 lambda:TSS.frost_verify_single_signature(*args, **kwargs)
                 )
        results[args[0]] = result