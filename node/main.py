from common.dns import DNS
from common.data_manager import DataManager
from node import Node
from node_config import PRIVATES

import logging
import sys
import trio


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


async def run(id: str) -> None:
    dns = DNS()
    data_manager = DataManager()
    node = Node(data_manager, dns.lookup(id), PRIVATES[id], dns)
    await node.run()

if __name__ == "__main__":
    id_to_peer_id = {
        '1': '16Uiu2HAm7Sx71kCEvgK8drUWZACPhU2WiUftZPSKjbAC5accWqwE',
        '2': '16Uiu2HAmBep4CggnrJX36oQ1S5z8T9VTrjXS66Tskx2QzQJonkr2',
        '3': '16Uiu2HAmUSf3PjDQ6Y1eBPU3TbDFXQzsf9jmj4qyc7wXMGKceo2K'
    }

    id = id_to_peer_id[sys.argv[1]]
    t = 2
    n = 3
    try:
        # Run the libp2p node
        trio.run(run, id)
    except KeyboardInterrupt:
        pass