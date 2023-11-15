class DNS:
    """
    A DNS-like class for managing and resolving peer network information.
    It maintains a lookup table mapping peer IDs to their respective network details.

    Note: If one wishes to use other data structures or another form of data, one 
    can inherit from this class and use the modified class. 
    """

    def __init__(self):
        """
        Initializes the DNS with a pre-defined lookup table containing peer IDs and their details.
        """
        self.lookup_table = {
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
            "16Uiu2HAm4zhoM9y3oZnSVr3z3sL2SmEDbMfB6k3pS548o2jY5PRH": {
                "ip": "127.0.0.1",
                "port": "6500",
                'public_key': '08021221028e2f682512a15da808b0e5cc17cab77ce65b0a057d0f8f97ef79b414085156a8'
            },
            # Gateway
            "16Uiu2HAmGVUb3nZ3yaKNpt5kH7KZccKrPaHmG1qTB48QvLdr7igH": {
                "ip": "127.0.0.1",
                "port": "7000",
                'public_key': '080212210338fede176f44704dc4fdcdace7c35108a126d8b77ad33ee7af09c0e18d56376a'
            }
        }

    def lookup(self, peer_id: str):
        """
        Resolves the network details for a given peer ID.

        Parameters:
        peer_id (str): The peer ID whose details are to be resolved.

        Returns:
        A dictionary containing the network details (IP, port, public key) of the specified peer ID.
        """
        return self.lookup_table.get(peer_id, None)
