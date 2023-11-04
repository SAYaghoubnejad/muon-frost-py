from Gateway.gateway import Gateway
from Gateway.gateway_config import PRIVATES
from Common.dns import DNS

import trio

async def run(id: str, threshold: int, n: int) -> None: 
    party = [
        'Qme3TyH6tPKgcEi8SUh3T5At8P1ogXf8b35j34H7BT3Ao2',
        'QmS9xUMXu8KpbH2AWNEYbMh2NFyN93exGdkGF2qmBbvjoq',
        'QmUX3cED2nL6nhmg8PtkaDxSmRVjv7F8BiFETS46rxdNGM'
    ]
    gateway = Gateway(DNS.lookup(id) ,PRIVATES[id])

    # async with trio.open_nursery() as nursery:
    #     nursery.start_soon(gateway.run)
    #     nursery.start_soon(gateway.requset_dkg, threshold, n, party)

    async with gateway.host.run(listen_addrs=[]):
        await gateway.requset_dkg(threshold, n, party)

if __name__ == "__main__":

    id = 'Qmec1kCE66ptPiKjYBycgvHKuxAiswx3jrjfiLLJ95J5N5'
    threshold = 2
    n = 3
    try:
        # Run the libp2p node
        trio.run(run, id, threshold, n)
    except KeyboardInterrupt:
        pass