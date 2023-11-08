from gateway import Gateway
from gateway_config import PRIVATE
from common.dns import DNS

from pprint import pprint

import trio

async def run(id: str, threshold: int, n: int) -> None: 
    dns = DNS()
    party = [
        '16Uiu2HAm7Sx71kCEvgK8drUWZACPhU2WiUftZPSKjbAC5accWqwE',
        '16Uiu2HAmBep4CggnrJX36oQ1S5z8T9VTrjXS66Tskx2QzQJonkr2',
        '16Uiu2HAmUSf3PjDQ6Y1eBPU3TbDFXQzsf9jmj4qyc7wXMGKceo2K'
    ]
    gateway = Gateway(dns.lookup(id) ,PRIVATE, dns)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(gateway.run)
        nursery.start_soon(gateway.maintain_nonces, party)
        await trio.sleep(3)
        dkg_key = await gateway.requset_dkg(threshold, n, party)

        signature = await gateway.requset_signature(dkg_key, party, 'Hi there!')

        print('signature:')
        pprint(signature)
        gateway.stop()


if __name__ == "__main__":

    id = '16Uiu2HAmGVUb3nZ3yaKNpt5kH7KZccKrPaHmG1qTB48QvLdr7igH'
    threshold = 2
    n = 3
    try:
        # Run the libp2p node
        trio.run(run, id, threshold, n)
    except KeyboardInterrupt:
        pass