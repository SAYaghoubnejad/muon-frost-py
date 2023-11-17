# Importing necessary libp2p components
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
import trio
import multiaddr
import json

class Libp2pBase:
    """
    A base class for creating and managing a libp2p host.
    This class encapsulates functionalities like setting up a node, handling protocols,
    sending messages, and managing connections.
    """

    def __init__(self, address: Dict[str, str], secret: str) -> None:
        """
        Initializes the Libp2pBase instance.

        Parameters:
        address (Dict[str, str]): A dictionary containing the IP and port for the host.
        secret (str): A secret key for creating the RSA key pair.
        """
        # TODO: check this procedure to create host
        # Create RSA key pair from the secret
        self._key_pair = create_new_key_pair(bytes.fromhex(secret))
        self.peer_id: PeerID = PeerID.from_pubkey(self._key_pair.public_key)

        # Initialize peer store and add key pair
        peer_store = PeerStore()
        peer_store.add_key_pair(self.peer_id, self._key_pair)

        # Configure transport and security protocols
        muxer_transports_by_protocol = {MPLEX_PROTOCOL_ID: Mplex}
        noise_key = ed25519.create_new_key_pair()
        security_transports_by_protocol = {
            TProtocol(secio.ID): secio.Transport(self._key_pair),
            TProtocol(noise.PROTOCOL_ID): noise.Transport(self._key_pair, noise_key.private_key)
        }
        upgrader = TransportUpgrader(security_transports_by_protocol, muxer_transports_by_protocol)
        transport = TCP()
        swarm = Swarm(self.peer_id, peer_store, upgrader, transport)

        # Initialize the host
        self.host: IHost = BasicHost(swarm)
        self.ip: str = address['ip']
        self.port: str = address['port']

        # Initialize protocol related attributes
        self.protocol_list: Dict[str, TProtocol] = {}
        self.protocol_handler: Dict[str, types.FunctionType] = {}
        self.__is_running = False

    def set_protocol_and_handler(self, protocol_list: Dict[str, TProtocol], protocol_handler: Dict[str, types.FunctionType]) -> None:
        """
        Sets the protocols and their respective handlers.

        Parameters:
        protocol_list (Dict[str, TProtocol]): A dictionary mapping protocol names to their TProtocol objects.
        protocol_handler (Dict[str, types.FunctionType]): A dictionary mapping protocol names to their handler functions.
        """
        self.protocol_list = protocol_list
        self.protocol_handler = protocol_handler

    async def run(self) -> None:
        """
        Starts the libp2p host and listens for incoming connections.
        """
        self.__is_running = True
        listen_addr = multiaddr.Multiaddr(f"/ip4/{self.ip}/tcp/{self.port}")
        async with self.host.run(listen_addrs=[listen_addr]):
            for protocol_name, handler in self.protocol_handler.items():
                self.host.set_stream_handler(self.protocol_list[protocol_name], handler)
            logging.info(f"API: /ip4/{self.ip}/tcp/{self.port}/p2p/{self.host.get_id().pretty()}")
            logging.info("Waiting for incoming connections...")
            while self.__is_running:
                await trio.sleep(1)

    def stop(self) -> None:
        """
        Stops the libp2p host.
        """
        self.__is_running = False

    async def send_with_semaphore(self, semaphore, destination_address: Dict[str, str], destination_peer_id: PeerID, protocol_id: TProtocol,
                   message: Dict, result: Dict = None, timeout: float = 5.0) -> None:
        async with semaphore:
            await self.send(destination_address, destination_peer_id, protocol_id,
                   message, result, timeout)

    async def send(self, destination_address: Dict[str, str], destination_peer_id: PeerID, protocol_id: TProtocol,
                   message: Dict, result: Dict = None, timeout: float = 5.0) -> None:
        """
        Sends a message to a destination peer using a specified protocol.

        Parameters:
        destination_address (Dict[str, str]): The address of the destination peer.
        destination_peer_id (PeerID): The peer ID of the destination.
        protocol_id (TProtocol): The protocol to use for the communication.
        message (Dict): The message to send.
        result (Dict, optional): A dictionary to store response from the destination. Defaults to None.
        timeout (float, optional): The timeout for the connection attempt in seconds. Defaults to 5.0.
        """
        
        destination = f"/ip4/{destination_address['ip']}/tcp/{destination_address['port']}/p2p/{destination_peer_id}"
        maddr = multiaddr.Multiaddr(destination)
        info = info_from_p2p_addr(maddr)

        with trio.move_on_after(timeout) as cancel_scope:
            try:
                # Establish connection with the destination peer
                await self.host.connect(info)
                logging.info(f"{destination_peer_id}{protocol_id} Connected to peer.")

                # Open a new stream for communication
                stream = await self.host.new_stream(info.peer_id, [protocol_id])
                logging.info(f"{destination_peer_id}{protocol_id} Opened a new stream to peer")

                # Send the message
                encoded_message = json.dumps(message).encode("utf-8")
                await stream.write(encoded_message)
                logging.info(f"{destination_peer_id}{protocol_id} Sent message: {encoded_message}")

                await stream.close()
                logging.info(f"{destination_peer_id}{protocol_id} Closed the stream")

                if result is not None:
                    response = await stream.read()
                    result[destination_peer_id] = json.loads(response.decode("utf-8"))
                    logging.info(f"{destination_peer_id}{protocol_id} Received response: {result[destination_peer_id]}")

            except Exception as e:
                logging.error(f'{destination_peer_id}{protocol_id} libp2p_base => Exception occurred: ', exc_info=True)
                response = {
                    "status": "ERROR",
                    "error": f"An exception occurred: {type(e).__name__}: {e}",
                }
                if result is not None:
                    result[destination_peer_id] = response

            if cancel_scope.cancelled_caught:
                logging.error(f'{destination_peer_id}{protocol_id} libp2p_base => Timeout error occurred')
                timeout_response = {
                    "status": "TIMEOUT",
                    "error": "Communication timed out",
                }
                if result is not None:
                    result[destination_peer_id] = timeout_response

