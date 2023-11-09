from libp2p.typing import TProtocol
import libp2p.crypto.ed25519 as ed25519
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.crypto.secp256k1 import create_new_key_pair
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

import types
import logging
import uuid
import trio
import multiaddr
import json

class Libp2pBase:
    def __init__(self, address: Dict[str, str], secret: str) -> None:
        # TODO: check this procedure to create host
        # Deserialize the private key and create RSA key pair
        self._key_pair = create_new_key_pair(bytes.fromhex(secret))
        self.peer_id: PeerID = PeerID.from_pubkey(self._key_pair.public_key)

        # private_key_data = base64.b64decode(secret)
        # private_key = PrivateKey.deserialize_from_protobuf(private_key_data)
        # private_key = RSA.import_key(private_key.data)
        # private_key = RSAPrivateKey(private_key)
        # public_key = private_key.get_public_key()
        # self.peer_id: ID = PeerID.from_pubkey(public_key)
        # self._key_pair = KeyPair(private_key, public_key)

        # Set up the peer store with the key pair
        peer_store = PeerStore()
        peer_store.add_key_pair(self.peer_id, self._key_pair)

        # Set up the transport and the swarm
        muxer_transports_by_protocol = {MPLEX_PROTOCOL_ID: Mplex}
        noise_key = ed25519.create_new_key_pair()
        security_transports_by_protocol = {
            TProtocol(secio.ID): secio.Transport(self._key_pair),
            TProtocol(noise.PROTOCOL_ID): noise.Transport(self._key_pair, noise_key.private_key)
        }
        upgrader = TransportUpgrader(
            security_transports_by_protocol, muxer_transports_by_protocol)
        transport = TCP()
        swarm = Swarm(self.peer_id, peer_store, upgrader, transport)

        self.host: IHost = BasicHost(swarm)
        self.ip: str = address['ip']
        self.port: str = address['port']
        self.protocol_list: Dict[str, TProtocol] = {}
        self.protocol_handler: Dict[str, types.FunctionType] = {}
        self.__is_running = False

    def set_protocol_and_handler(self, protocol_list: Dict[str, TProtocol], protocol_handler: Dict[str, types.FunctionType]) -> None:
        self.protocol_list: Dict[str, TProtocol] = protocol_list
        self.protocol_handler: Dict[str, types.FunctionType] = protocol_handler

    async def run(self):
        self.__is_running = True

        # Receiving functionality
        listen_addr = multiaddr.Multiaddr(f"/ip4/{self.ip}/tcp/{self.port}")
        # Run the host and set up the stream handler for the specified protocol methods
        async with self.host.run(listen_addrs=[listen_addr]):
            for method in self.protocol_handler.keys():
                self.host.set_stream_handler(
                    self.protocol_list[method], self.protocol_handler[method])
            logging.info(f" API: /ip4/{self.ip}/tcp/{self.port}/p2p/{self.host.get_id().pretty()}")
            logging.info("Waiting for incoming connections...")
            while self.__is_running:
                await trio.sleep(1)

    def stop(self) -> None:
        self.__is_running = False

    async def send(self, destination_address: Dict[str, str], destination_peer_id: PeerID, protocol_id: TProtocol,
                   message: Dict, result: Dict = None, timeout: float = 5.0) -> None:

        # Create the destination multiaddress
        destination = f"/ip4/{destination_address['ip']}/tcp/{destination_address['port']}/p2p/{destination_peer_id}"
        maddr = multiaddr.Multiaddr(destination)
        info = info_from_p2p_addr(maddr)

        # Use trio's timeout to limit the connection attempt
        with trio.move_on_after(timeout) as cancel_scope:
            try:
                
                # Connect to the recipient's peer
                await self.host.connect(info)
                
                logging.info(f"{destination_peer_id}{protocol_id} Connected to peer.")

                # Create a new stream for communication
                stream = await self.host.new_stream(info.peer_id, [protocol_id])

                logging.info(f"{destination_peer_id}{protocol_id} Opened a new stream to peer")

                # Write the message to the stream
                message = json.dumps(message).encode("utf-8")
                await stream.write(message)

                logging.info(f"{destination_peer_id}{protocol_id} Sent message: {message}")
                # Close the stream
                await stream.close()

                logging.info(f"{destination_peer_id}{protocol_id} Closed the stream")


                logging.info(f"{destination_peer_id}{protocol_id} Closed the connection to the peer")

                # If get_response is true, read the response
                if result is not None:
                    response = await stream.read()
                    response = response.decode("utf-8")
                    response = json.loads(response)
                    logging.info(f"{destination_peer_id}{protocol_id} Got message: {response}")
                else:
                    response = {}

            except Exception as e:
                logging.error(f'{destination_peer_id}{protocol_id}' 
                               ' libp2p_base => Exception occured: ', exc_info=True)
                # Prepare an error response
                #
                response = {
                    "status": "ERROR",
                    "error": f"ERROR: failed to complete communication with node {destination_peer_id} invoking protocol {protocol_id}; "
                                f"An exception of type {type(e).__name__} occurred: {e}",
                }

        # Check if the operation was canceled tdue to a timeout
        if cancel_scope.cancelled_caught:
            logging.error(f'{destination_peer_id}{protocol_id} libp2p_base => Timeout error occurred')
            response = {
                "status": "TIMEOUT",
                "error": f"TIMEOUT: failed to complete communication with node {destination_peer_id} invoking protocol {protocol_id}",
            }

        # If aggregation is enabled, append the response to the dictionary
        if result is not None:
            result[destination_peer_id] = (response)

    @staticmethod
    def generate_random_uuid() -> str:
        return str(uuid.uuid4())
