from libp2p.typing import TProtocol

PROTOCOLS_ID = {
    'round1': TProtocol("/muon/1.0.0/round1"),
    'round2': TProtocol("/muon/1.0.0/round2"),
    'peerExchange': TProtocol("/muon/1.0.0/peer-exchange"),
    'generateNonces': TProtocol("/muon/1.0.0/generate-nonces"),
    'sign': TProtocol("/muon/1.0.0/sign"),
}