from libp2p.peer.id import ID


class DNS:
    lookup_table = {
        "16Uiu2HAm7Sx71kCEvgK8drUWZACPhU2WiUftZPSKjbAC5accWqwE": {
            "ip": "127.0.0.1",
            "port": "4000",
            'public_key': '0802122102b2a00e5201570c9fe5ee76ddf41cdb3a9b8ba1bc1305b55349bf493d74d43ce1'
        },
        "16Uiu2HAmBep4CggnrJX36oQ1S5z8T9VTrjXS66Tskx2QzQJonkr2": {
            "ip": "127.0.0.1",
            "port": "5000",
            'public_key': '0802122102f118ac4442d9421a27acf18063f21fee8200d13aa8f186908342c42ddd2a4cef'
        },
        "16Uiu2HAmUSf3PjDQ6Y1eBPU3TbDFXQzsf9jmj4qyc7wXMGKceo2K": {
            "ip": "127.0.0.1",
            "port": "6000",
            'public_key': '0802122103ea923057d66a68614b69ead773a7b5982ce51bed269542f7b18a82eef44dacbc'
        },
        # Gateway
        "16Uiu2HAmGVUb3nZ3yaKNpt5kH7KZccKrPaHmG1qTB48QvLdr7igH": {
            "ip": "127.0.0.1",
            "port": "7000",
            'public_key': '080212210338fede176f44704dc4fdcdace7c35108a126d8b77ad33ee7af09c0e18d56376a'
        }, }

    @staticmethod
    def lookup(id: str):
        return DNS.lookup_table[id]
