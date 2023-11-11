from libp2p.network.stream.net_stream_interface import INetStream
from common. unpacked_stream import UnpackedStream

import json

def auth_decorator(handler):
    async def wrapper(self, stream: INetStream):
        unpacked_stream = UnpackedStream(stream)
        raw_data = await unpacked_stream.read()
        try:
            data = json.loads(raw_data)
            # Perform validation and authorization checks
            if validate_gateway(data, unpacked_stream.sender_id):
                return await handler(self, unpacked_stream)
            else:
                # TODO: use logging
                raise Exception("Unauthorized gateway")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON data")
        
    return wrapper

# Interface
def validate_gateway(data, sender_id):
    # Implement your validation logic here
    # For example, check if the client's token is valid
    request_id = data["request_id"]
    token = data["gateway_authorization"]
    method = data["method"]
    return sender_id == '16Uiu2HAmGVUb3nZ3yaKNpt5kH7KZccKrPaHmG1qTB48QvLdr7igH'

