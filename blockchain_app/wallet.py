from fastecdsa import curve, ecdsa, keys
from fastecdsa.keys import export_key, import_key, gen_keypair
from datetime import datetime
from uuid import uuid4
import json
from time import time
import os

class Wallet:

    def generate_key_pair(self):
        priv_key, pub_key = gen_keypair(curve.secp256k1)
        if not os.path.exists("blockchain/keys"):
            os.umask(0)
            os.makedirs("blockchain/keys")
            
        export_key(priv_key, curve=curve.secp256k1,
                   filepath=os.path.join("blockchain/keys/secp256k1.key"))
        export_key(pub_key, curve=curve.secp256k1,
                   filepath=os.path.join("blockchain/keys/secp256k1.pub"))
        return True

    def generate_private_key(self):
        private_key = keys.gen_private_key(curve.secp256k1)
        return private_key

    def generate_public_key(self, private_key):
        public_key = keys.get_public_key(private_key, curve.secp256k1)
        return public_key

    def create_transaction(self, data: str):
        """
        Creates a transaction from a sender's public key to a receiver's public key
        :param private_key: The Sender's private key
        :param public_key: The Sender's public key
        :param receiver: The Receiver's public key
        :param data: The message from the sender
        :return: <dict> The transaction dict
        """
        transaction_id = str(uuid4()).replace('-', '')
        timing = datetime.now()
        timestamp = timing.strftime('%Y-%m-%d %H:%M:%S.%f')

        transaction = {}
        transaction['transaction_id'] = transaction_id
        transaction['timestamp'] = timestamp
        transaction['data'] = data

        return transaction

    def get_signature(self, transaction, private_key):
        encoded_transaction = json.dumps(transaction, sort_keys=True).encode()
        signature = ecdsa.sign(encoded_transaction, private_key,
                               curve.secp256k1, ecdsa.sha256)
        return signature

    def validate_transaction(self, transaction):
        trans_result = transaction
        transaction1 = json.loads(trans_result)

        string_signature1 = transaction1['signature']
        signature1 = eval(string_signature1)

        transaction1.pop('signature')
        string_transaction1 = json.dumps(transaction1, sort_keys=True).encode()

        key1, key2 = keys.get_public_keys_from_sig(
            signature1, string_transaction1, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

        is_valid = ecdsa.verify(signature1, string_transaction1,
                                key1, curve.secp256k1, ecdsa.sha256)

        return is_valid