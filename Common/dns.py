from libp2p.peer.id import ID


class DNS:
    lookup_table = {
        "Qme3TyH6tPKgcEi8SUh3T5At8P1ogXf8b35j34H7BT3Ao2": {
            "ip": "127.0.0.1",
            "port": "4000",
        },
        "QmS9xUMXu8KpbH2AWNEYbMh2NFyN93exGdkGF2qmBbvjoq": {
            "ip": "127.0.0.1",
            "port": "5000",
        },
        "QmUX3cED2nL6nhmg8PtkaDxSmRVjv7F8BiFETS46rxdNGM": {
            "ip": "127.0.0.1",
            "port": "6000",
        },
        # Gateway
        "Qmec1kCE66ptPiKjYBycgvHKuxAiswx3jrjfiLLJ95J5N5": {
            "ip": "127.0.0.1",
            "port": "7000",
        }, }

    @staticmethod
    def lookup(id: str):
        return DNS.lookup_table[id]
