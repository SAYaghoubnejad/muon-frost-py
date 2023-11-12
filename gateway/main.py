from gateway import Gateway
from gateway_config import PRIVATE
from common.configuration_settings import ConfigurationSettings
from common.dns import DNS
from common.utils import Utils
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
    app_name = 'sample_oracle'

    async with trio.open_nursery() as nursery:
        # Start gateway and maintain nonce values for each peer
        nursery.start_soon(gateway.run)
        nursery.start_soon(gateway.maintain_nonces, party_ids)

        # Begin DKG protocol
        is_completed = False
        dkg_key = None
        while not is_completed:
            party_ids = gateway.error_handler.get_new_party(party_ids)
            if len(party_ids) < threshold:
                logging.error(f'DKG id {dkg_id} has FAILED due to insufficient number of availadle nodes')
                exit()
            
            dkg_key = await gateway.request_dkg(threshold, n, party_ids, app_name)
            result = dkg_key['result']
            logging.info(f'The DKG result is {result}')
            if result == 'SUCCESSFUL':
                is_completed = True

        dkg_id = dkg_key['dkg_id']
        logging.info(f'Get signature for app {app_name} with DKG id {dkg_id}')

        # Request signature using the generated DKG key
        signature = await gateway.request_signature(dkg_key, party_ids)

        # Log the generated signature
        logging.info(f'Signature: {signature}')

        # Stop the gateway
        gateway.stop()
        nursery.cancel_scope.cancel()


if __name__ == "__main__":

    # Define the logging configurations
    ConfigurationSettings.set_logging_options('logs', 'gateway.log')

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
