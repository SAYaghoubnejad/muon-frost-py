from Common.dns import DNS
from Node.node import Node
from Node.node_config import PRIVATES

import sys
import trio

async def run(id: str) -> None:
    dns = DNS()
    node = Node(dns.lookup(id), PRIVATES[id], dns)
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