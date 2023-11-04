from Common.TSS.tss import TSS
from Common.TSS.polynomial import Polynomial
from web3 import Web3
from typing import List


class DistributedKey:
    def __init__(self, dkg_id: str, threshold: int, n: int, node_id: str, partners: List[str], coefficient0: str = None) -> None:
        self.threshold: int = threshold
        self.n: int = n
        self.dkg_id: str = dkg_id
        self.node_id: str = node_id
        self.partners: List[str] = partners
        self.coefficient0 = coefficient0
        self.store = {}

    # Interface
    def save_data(self, key, value):
        self.store[key] = value

    # Interface
    def get_data(self, key):
        return self.store[key]

    def round1(self):
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
        self.save_data("Fx", public_fx)             
        self.save_data("poly_sig", coef0_signature)
        return broadcast
