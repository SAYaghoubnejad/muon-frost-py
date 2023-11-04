from Common.TSS.tss import TSS
from Common.TSS.polynomial import Polynomial
from libp2p.peer.id import ID as PeerID
from web3 import Web3
from typing import List, Dict


class DistributedKey:
    def __init__(self, dkg_id: str, threshold: int, n: int, node_id: str, partners: List[str], coefficient0: str = None) -> None:
        self.threshold: int = threshold
        self.n: int = n
        self.dkg_id: str = dkg_id
        self.node_id: str = node_id
        self.partners: List[str] = partners
        self.coefficient0 = coefficient0
        self.store = {}
        self.malicious = []

    # Interface
    def save_data(self, key, value):
        self.store[key] = value

    # Interface
    def get_data(self, key):
        return self.store[key]

    def round1(self) -> Dict:
        secret_key = TSS.generate_random_private()
        public_key = secret_key.get_public_key()
        secret_nonce = TSS.generate_random_private()
        public_nonce = secret_nonce.get_public_key()
        secret_pop_hash = Web3.solidity_keccak(
            [
                "string",
                "string",
                "uint8",
                "uint8"
            ],
            [
                str(self.node_id),
                self.dkg_id,
                TSS.pub_to_code(public_key),
                TSS.pub_to_code(public_nonce)
            ],
        )

        secret_pop_sign = TSS.schnorr_sign(
            secret_key, secret_nonce, public_nonce, int.from_bytes(
                secret_pop_hash, "big")
        )

        secret_signature = {
            "nonce": TSS.pub_to_code(public_nonce),
            "signature": TSS.stringify_signature(secret_pop_sign),
        }

        # Generate DKG polynomial
        fx = Polynomial(self.threshold, TSS.curve, self.coefficient0)
        public_fx = fx.coef_pub_keys()
        
        coef0_nonce = TSS.generate_random_private()
        public_coef0_nonce = coef0_nonce.get_public_key()
        coef0_pop_hash = Web3.solidity_keccak(
            [
                "string", 
                "string", 
                "uint8", 
                "uint8"
                ],
            [
                str(self.node_id), 
                self.dkg_id, 
                TSS.pub_to_code(public_fx[0]), 
                TSS.pub_to_code(public_coef0_nonce)
                ],
        )
        coef0_pop_sign = TSS.schnorr_sign(
            fx.coefficients[0], coef0_nonce, public_coef0_nonce, int.from_bytes(coef0_pop_hash, "big")
        )

        coef0_signature = {
            "nonce": TSS.pub_to_code(public_coef0_nonce),
            "signature": TSS.stringify_signature(coef0_pop_sign),
        }

        broadcast = {
            "sender_id": str(self.node_id),
            "public_fx": [TSS.pub_to_code(s) for s in public_fx],
            "coefficient0_signature": coef0_signature,
            "public_key": TSS.pub_to_code(public_key),
            "secret_signature": secret_signature
        }
        
        self.save_data('secret_key', secret_key)
        self.save_data("fx", fx)
        self.save_data("public_fx", public_fx)             
        self.save_data("coef0_signature", coef0_signature)
        return broadcast

    def round2(self) -> List[Dict]:
        fx: Polynomial = self.get_data("fx")
        partners_public_keys = {}
        secret_key = self.get_data('secret_key')
        round1_broadcasted_data = self.get_data('round1_broadcasted_data')
        for data in round1_broadcasted_data:
            sender_id = data["sender_id"]

            if sender_id == self.node_id:
                continue

            sender_public_fx = data["public_fx"]
            sender_coef0_nonce = data["coef0_signature"]["nonce"]
            sender_coef0_signature = data["coef0_signature"]["nonce"]

            coef0_pop_hash = Web3.solidity_keccak(
                ["string",  "string",       "uint8",                "uint8"],
                [sender_id, self.dkg_id,    sender_public_fx[0],    sender_coef0_nonce]
            )

            coef0_verification = TSS.schnorr_verify(
                TSS.code_to_pub(sender_public_fx[0]), 
                int.from_bytes(coef0_pop_hash, "big"), 
                sender_coef0_signature
            )
        
            sender_public_key = data["public_key"]
            sender_secret_nonce = data["secret_signature"]["nonce"]
            sender_secret_signature = data["secret_signature"]["signature"]

            secret_pop_hash = Web3.solidity_keccak(
                ["string",  "string",   "uint8",            "uint8"],
                [sender_id, self.dkg_id, sender_public_key, sender_secret_nonce]
            )

            secret_verification = TSS.schnorr_verify(
                TSS.code_to_pub(sender_public_key), 
                int.from_bytes(secret_pop_hash, "big"), 
                sender_secret_signature
            )

            if not secret_verification or not coef0_verification:
                # TODO: handle complient
                self.malicious.append({"id": sender_id, "complient": data})                
            partners_public_keys[sender_id] = sender_public_key

        qualified = self.partners
        for node in self.malicious:
            try:
                qualified.remove(node["id"])
            except:
                pass
        send = []
        for id in qualified:
            encryption_key = TSS.generate_hkdf_key(secret_key , TSS.code_to_pub(partners_public_keys[id]))
            id_as_int = int.from_bytes(PeerID.from_base58(id).to_bytes(), 'big')
            data = {
                'receiver_id': id,
                'data': TSS.encrypt(
                    {"receiver_id": id, "f": fx.evaluate(id_as_int).d},
                    encryption_key
                )
            }
            send.append(data)
        self.save_data("partners_public_keys", partners_public_keys)
        return send