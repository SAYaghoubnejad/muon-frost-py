from libp2p.network.stream.net_stream_interface import INetStream

class UnpackedStream:
    def __init__(self, stream: INetStream) -> None:
        self.raw_data = None
        self.sender_id = stream.muxed_conn.peer_id
        self.stream = stream

    async def read(self):
        if self.raw_data is None:
            self.raw_data = await self.stream.read()
        print(self.raw_data)
        return self.raw_data