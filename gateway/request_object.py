from typing import Dict

class RequestObject:
    def __init__(self, dkg_id: str, call_method: str, gateway_authorization: str, parameters: Dict) -> None:
        self.dkg_id: str = dkg_id
        self.call_method: str = call_method
        self.gateway_authorization: str = gateway_authorization
        self.parameters: Dict = parameters


    def get(self):
        result = {
            "request_id": f"{self.dkg_id}_{self.call_method}",
            "method": self.call_method,
            'gateway_authorization': self.gateway_authorization,
            "parameters": self.parameters
        }
        return result