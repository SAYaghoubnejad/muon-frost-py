from Common.TSS.tss import TSS, ECPublicKey, ECPrivateKey
from Common.TSS.polynomial import Polynomial
from libp2p.peer.id import ID as PeerID
from web3 import Web3
from typing import List, Dict
from pprint import pprint

import json


class DistributedKey:
    def __init__(self, dkg_id: str, threshold: int, n: int, node_id: PeerID, partners: List[str], coefficient0: str = None) -> None:
        self.threshold: int = threshold
        self.n: int = n
        self.dkg_id: str = dkg_id
        self.node_id: PeerID = node_id
        self.partners: List[str] = partners
        self.coefficient0 = coefficient0
        self.store = {}
        self.malicious: Dict[List] = []

    # TODO: use class for these interface
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
                self.node_id.to_base58(), 
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
            sender_coef0_nonce = data["coefficient0_signature"]["nonce"]
            sender_coef0_signature = data["coefficient0_signature"]["signature"]

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
                'sender_id': self.node_id.to_base58(),
                'data': TSS.encrypt(
                    {"receiver_id": id, "f": fx.evaluate(id_as_int).d},
                    encryption_key
                )
            }
            send.append(data)
        self.save_data("partners_public_keys", partners_public_keys)
        return send

    def round3(self):
        secret_key = self.get_data('secret_key')
        partners_public_keys = self.get_data("partners_public_keys")
        round1_broadcasted_data = self.get_data('round1_broadcasted_data')
        round2_encrypted_data = self.get_data('round2_encrypted_data')
        round2_data = []

        for message in round2_encrypted_data:
            sender_id = message['sender_id']
            receiver_id = message['receiver_id']
            encrypted_data = message['data']
            encryption_key = TSS.generate_hkdf_key(secret_key , TSS.code_to_pub(partners_public_keys[sender_id]))
            # TODO: logging
            assert receiver_id == self.node_id.to_base58(), "ERROR: receiverID does not matched."

            data = json.loads(TSS.decrypt(encrypted_data, encryption_key))
            round2_data.append(data)
            for round1_data in round1_broadcasted_data:
                if round1_data["sender_id"] == sender_id:
                    public_fx = round1_data["public_fx"]

                    point1 = TSS.calc_poly_point(
                        list(map(TSS.code_to_pub, public_fx)),
                        int.from_bytes(self.node_id.to_bytes(), 'big')
                    )
                    
                    point2 = TSS.curve.mul_point(
                        data["f"], 
                        TSS.curve.generator
                    )

                    if point1 != point2:
                        # TODO: handle complient
                        self.malicious.append({
                            "id": receiver_id, 
                            "complient": {
                                "public_fx": public_fx, 
                                "f": data["f"]
                                }
                            }
                        )

        # TODO: return status
        if len(self.malicious) != 0:
            return self.malicious
        
        fx: Polynomial = self.get_data("fx")
        my_fragment = fx.evaluate(int.from_bytes(self.node_id.to_bytes(), 'big')).d
        share_fragments = [my_fragment]
        for data in round2_data:
            share_fragments.append(data["f"])

        public_fx = [self.get_data("public_fx")[0]]
        for data in round1_broadcasted_data:
            if data["sender_id"] in self.partners:
                public_fx.append(TSS.code_to_pub(data["public_fx"][0]))

        # TODO: renameing F
        F = public_fx[0].W
        for i in range(1, len(public_fx)):
            F = TSS.curve.add_point(F, public_fx[i].W)
        # TODO: removing nInv 
        n_inverse = TSS.mod_inverse(self.n, TSS.N)
        total_Fx = ECPublicKey(TSS.curve.mul_point(n_inverse, F))
        share = ECPrivateKey(sum(share_fragments) * n_inverse, TSS.curve)
        self.dkg_key_pair = {"share": share, "PublicKey": total_Fx}
        return {"Group_PublicKey": TSS.pub_to_code(total_Fx) , "Share_PublicKey" : TSS.pub_to_code(share.get_public_key())}