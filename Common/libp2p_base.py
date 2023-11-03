import uuid
import base64
import trio
import multiaddr
import json
import Crypto.PublicKey.RSA as RSA
from libp2p_config import TProtocol
from libp2p.peer.id import ID
import libp2p.crypto.ed25519 as ed25519
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.crypto.keys import KeyPair, PrivateKey
from libp2p.crypto.rsa import RSAPrivateKey
from libp2p.host.basic_host import BasicHost
from libp2p.network.swarm import Swarm
from libp2p.peer.id import ID as PeerID
from libp2p.peer.peerstore import PeerStore
import libp2p.security.secio.transport as secio
import libp2p.security.noise.transport as noise
from libp2p.stream_muxer.mplex.mplex import MPLEX_PROTOCOL_ID, Mplex
from libp2p.transport.tcp.tcp import TCP
from libp2p.transport.upgrader import TransportUpgrader
from libp2p.host.host_interface import IHost
from typing import Dict


class Libp2pBase:
    def __init__(self, ip: str, port: str, secret: str) -> None:
        # TODO: check this procedure to creat host
        # Deserialize the private key and create RSA key pair
        private_key_data = base64.b64decode(secret)
        private_key = PrivateKey.deserialize_from_protobuf(private_key_data)
        private_key = RSA.import_key(private_key.data)
        private_key = RSAPrivateKey(private_key)
        public_key = private_key.get_public_key()
        self.peer_id: ID = PeerID.from_pubkey(public_key)
        self.key_pair = KeyPair(private_key, public_key)

        # Set up the peer store with the key pair
        peer_store = PeerStore()
        peer_store.add_key_pair(self.peer_id, self.key_pair)

        # Set up the transport and the swarm
        muxer_transports_by_protocol = {MPLEX_PROTOCOL_ID: Mplex}
        noise_key = ed25519.create_new_key_pair()
        security_transports_by_protocol = {
            TProtocol(secio.ID): secio.Transport(self.key_pair),
            TProtocol(noise.PROTOCOL_ID): noise.Transport(self.key_pair, noise_key.private_key)
        }
        upgrader = TransportUpgrader(
            security_transports_by_protocol, muxer_transports_by_protocol)
        transport = TCP()
        swarm = Swarm(self.peer_id, peer_store, upgrader, transport)

        self.host: IHost = BasicHost(swarm)
        self.ip: str = ip
        self.port: str = port

    async def run(self, protocol_list: Dict[str, TProtocol], protocol_handler: Dict[str, function]):
        self.protocol_list: Dict[str, TProtocol] = protocol_list
        self.protocol_handler: Dict[str, function] = protocol_handler
        if protocol_list is None or protocol_handler is None:
            self.protocol_list: Dict[str, TProtocol] = {}
            self.protocol_handler: Dict[str, function] = {}

        # Receiving functionality
        listen_addr = multiaddr.Multiaddr(f"/ip4/{self.ip}/tcp/{self.port}")
        # Run the host and set up the stream handler for the specified protocol methods
        async with self.host.run(listen_addrs=[listen_addr]):
            for method in self.protocol_handler.keys():
                self.host.set_stream_handler(
                    self.protocol_list[method], self.protocol_handler[method])

            print(
                "API:", f"/ip4/{self.ip}/tcp/{self.port}/p2p/{self.host.get_id().pretty()}'")
            print("Waiting for incoming connections...")
            await trio.sleep_forever()

    async def send(self, destination_ip: str, destination_port: str, destination_peer_id: ID, protocolId: TProtocol,
                   message: Dict, timeout: float = 5.0, get_response: bool = True) -> Dict:

        # Create the destination multiaddress
        destination = f"/ip4/{destination_ip}/tcp/{destination_port}/p2p/{destination_peer_id}"
        maddr = multiaddr.Multiaddr(destination)
        info = info_from_p2p_addr(maddr)

        # Use trio's timeout to limit the connection attempt
        with trio.move_on_after(timeout) as cancelScope:
            try:
                # Connect to the recipient's peer
                await self.host.connect(info)

                # Create a new stream for communication
                stream = await self.host.new_stream(info.peer_id, [protocolId])

                # Write the message to the stream
                await stream.write(message)

                # Close the stream
                await stream.close()

                # If get_response is true, read the response
                if get_response:
                    response = await stream.read()
                    response = response.decode("utf-8")
                    response = json.loads(response)
                else:
                    response = {}

            except Exception as e:
                # TODO: use logging
                print(f"An exception of type {type(e).__name__} occurred: {e}")
                # Prepare an error response
                response = {
                    "status": "ERROR",
                    "error": f"ERROR: failed to complete communication with node {id} invoking protocol {protocolId}; "
                                f"An exception of type {type(e).__name__} occurred: {e}",
                }

        # Check if the operation was canceled tdue to a timeout
        if cancelScope.cancelled_caught:
            # TODO: use logging
            print(f"TIMEOUT: ...")
            response = {
                "status": "TIMEOUT",
                "error": f"TIMEOUT: failed to complete communication with node {id} invoking protocol {protocolId}",
            }

        return response

    @staticmethod
    def generate_random_uuid() -> str:
        return str(uuid.uuid4())
