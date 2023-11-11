import os
from gateway import Gateway
from gateway_config import PRIVATE
from common.dns import DNS

import trio
import logging


async def run(gateway_id: str, threshold: int, n: int) -> None: 
    """
    Sets up and runs a gateway node in a distributed network using libp2p.

    :param gateway_id: Identifier of the gateway node.
    :param threshold: Threshold number of parties for the DKG protocol.
    :param n: Total number of nodes in party in the DKG protocol.
    """
    dns = DNS()

    # List of peer IDs in the network
    party_ids = [
        '16Uiu2HAm7Sx71kCEvgK8drUWZACPhU2WiUftZPSKjbAC5accWqwE',
        '16Uiu2HAmBep4CggnrJX36oQ1S5z8T9VTrjXS66Tskx2QzQJonkr2',
        '16Uiu2HAmUSf3PjDQ6Y1eBPU3TbDFXQzsf9jmj4qyc7wXMGKceo2K'
    ]

    # Initialize the Gateway with DNS lookup for the current node
    gateway = Gateway(dns.lookup(gateway_id), PRIVATE, dns)

    async with trio.open_nursery() as nursery:
        # Start gateway and maintain nonce values for each peer
        nursery.start_soon(gateway.run)
        nursery.start_soon(gateway.maintain_nonces, party_ids)

        # Sleep to ensure initialization is complete
        await trio.sleep(3)

        # Begin DKG protocol
        dkg_key = await gateway.request_dkg(threshold, n, party_ids)

        # Request signature using the generated DKG key
        signature = await gateway.request_signature(dkg_key, party_ids, 'Hi there!')

        # Log the generated signature
        logging.info(f'Signature: {signature}')

        # Stop the gateway
        gateway.stop()
        nursery.cancel_scope.cancel()


if __name__ == "__main__":


    # Define logging basic configurations
    log_formatter = logging.Formatter('%(asctime)s - %(message)s', )
    root_logger = logging.getLogger()

    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    log_file_path = f"logs/gateway.log"
    with open(log_file_path, "w"):
        pass

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    root_logger.setLevel(logging.INFO)

    # Define the node identifier and DKG parameters
    node_id = '16Uiu2HAmGVUb3nZ3yaKNpt5kH7KZccKrPaHmG1qTB48QvLdr7igH'
    dkg_threshold = 2
    num_parties = 3

    try:
        # Run the gateway with specified parameters
        trio.run(run, node_id, dkg_threshold, num_parties)
    except KeyboardInterrupt:
        # Handle graceful shutdown on keyboard interrupt
        pass
