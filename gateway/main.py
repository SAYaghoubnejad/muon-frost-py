import time
from gateway import Gateway
from gateway_config import PRIVATE
from common.configuration_settings import ConfigurationSettings
from common.dns import DNS
from common.utils import Utils
from common.decorators import get_valid_random_seed
from typing import List

import sys
import trio
import logging

async def run_dkg(gateway : Gateway, all_nodes: List[str], threshold: int, n: int, app_name: str, seed: int=42) -> None:
    # Choose subnet from node peer IDs.
    party_ids = Utils.get_new_random_subset(all_nodes, seed, n)
    logging.info(f'Chosen peer IDs: {party_ids}')

    # Begin DKG protocol
    is_completed = False
    dkg_key = None
    while not is_completed:
        party_ids = gateway.error_handler.get_new_party(party_ids)
        if len(party_ids) < threshold:
            dkg_id = dkg_key['dkg_id']
            logging.error(f'DKG id {dkg_id} has FAILED due to insufficient number of availadle nodes')
            exit()
        
        dkg_key = await gateway.request_dkg(threshold, n, party_ids, app_name)
        result = dkg_key['result']
        logging.info(f'The DKG result is {result}')
        if result == 'SUCCESSFUL':
            is_completed = True

    return dkg_key

async def run(gateway_id: str, total_node_number: int, threshold: int, n: int, num_signs: int) -> None:
    """
    Sets up and runs a gateway node in a distributed network using libp2p.

    :param gateway_id: Identifier of the gateway node.
    :param threshold: Threshold number of parties for the DKG protocol.
    :param n: Total number of nodes in party in the DKG protocol.
    """
    dns = DNS()

    # List of peer IDs in the network
    all_nodes = dns.get_all_nodes(total_node_number)

    # Initialize the Gateway with DNS lookup for the current node
    gateway = Gateway(dns.lookup_gatewat(gateway_id), PRIVATE, dns)
    app_name = 'sample_oracle'

    async with trio.open_nursery() as nursery:
        # Start gateway and maintain nonce values for each peer
        nursery.start_soon(gateway.run)

        nursery.start_soon(gateway.maintain_nonces, all_nodes)
        await trio.sleep(2 * total_node_number)
        
        dkg_key = await run_dkg(gateway, all_nodes, threshold, n, app_name)
        await trio.sleep(total_node_number)

        # Request signature using the generated DKG key
        dkg_id = dkg_key['dkg_id']
        for i in range(num_signs):
            logging.info(f'Get signature {i} for app {app_name} with DKG id {dkg_id}')

            now = time.time()
            signature = await gateway.request_signature(dkg_key, threshold)
            then = time.time()

            # Log the generated signature
            logging.info(f'Requesting signature {i} takes {then - now} seconds')
            logging.info(f'Signature: {signature}')

        # Stop the gateway
        gateway.stop()
        nursery.cancel_scope.cancel()


if __name__ == "__main__":

    # Define the logging configurations
    ConfigurationSettings.set_logging_options('logs', 'gateway.log')

    # Define the gateway identifier and DKG parameters
    gateway_peer_id = '16Uiu2HAmGVUb3nZ3yaKNpt5kH7KZccKrPaHmG1qTB48QvLdr7igH'
    total_node_number = int(sys.argv[1])
    dkg_threshold = int(sys.argv[2])
    num_parties = int(sys.argv[3])
    num_signs = int(sys.argv[4])

    try:
        # Run the gateway with specified parameters
        trio.run(run, gateway_peer_id, total_node_number, dkg_threshold, num_parties, num_signs)
    except KeyboardInterrupt:
        # Handle graceful shutdown on keyboard interrupt
        pass
