from common.dns import DNS
from common.data_manager import DataManager
from common.configuration_settings import ConfigurationSettings
from node import Node
from node_config import SECRETS

import logging
import sys
import trio

async def run(node_number: int) -> None:
    dns = DNS()
    id = dns.get_all_nodes()[node_number]
    data_manager = DataManager()
    node = Node(data_manager, dns.lookup(id), SECRETS[id], dns)
    await node.run()

if __name__ == "__main__":


    # Define the logging configurations
    ConfigurationSettings.set_logging_options \
                        ('logs', f'node{sys.argv[1]}.log')

    node_number = int(sys.argv[1])
    t = 2
    n = 3
    try:
        # Run the libp2p node
        trio.run(run, node_number)
    except KeyboardInterrupt:
        pass