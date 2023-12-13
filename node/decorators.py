from libp2p.network.stream.net_stream_interface import INetStream
from .unpacked_stream import UnpackedStream

import logging
import json


def auth_decorator(handler):
    async def wrapper(self, stream: INetStream):
        unpacked_stream = UnpackedStream(stream)
        raw_data = await unpacked_stream.read()
        try:
            if self.caller_validator(unpacked_stream.sender_id.to_base58(), 
                                     unpacked_stream.stream.get_protocol()):
                return await handler(self, unpacked_stream)
            else:
                logging.error('Node Decorator => Exception occurred. Unauthorized SA.')
                raise Exception("Unauthorized SA")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON data")
        
    return wrapper




