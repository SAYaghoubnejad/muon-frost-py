from Common.dns import DNS
from Node.node import Node
from Node.node_config import PRIVATES

import sys
import trio

async def run(id: str) -> None:
    node = Node(DNS.lookup(id), PRIVATES[id])
    await node.run()

if __name__ == "__main__":
    id_to_peer_id = {
        '1': 'Qme3TyH6tPKgcEi8SUh3T5At8P1ogXf8b35j34H7BT3Ao2',
        '2': 'QmS9xUMXu8KpbH2AWNEYbMh2NFyN93exGdkGF2qmBbvjoq',
        '3': 'QmUX3cED2nL6nhmg8PtkaDxSmRVjv7F8BiFETS46rxdNGM'
    }

    id = id_to_peer_id[sys.argv[1]]
    t = 2
    n = 3
    try:
        # Run the libp2p node
        trio.run(run, id)
    except KeyboardInterrupt:
        pass