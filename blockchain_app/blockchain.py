from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import random
import time
import logging

import hashlib
import json
from fastecdsa import curve, ecdsa, keys

from . import models, schemas


class Blockchain:
    def __init__(self) -> None:
        self.transaction_pool = []
        self.chain = []

    def create_genesis_block(self, db: Session):

        block = {}
        block['index'] = 1
        block['nonce'] = 123
        block['prev_hash'] = '0000000000'
        block['transactions'] = [
            "This is the genesis block of the python blockchain"]

        # TODO: Create a hash of the transactions and sign the hash

        encode_block = json.dumps(block, sort_keys=True).encode()
        new_hash = hashlib.sha256(encode_block).hexdigest()

        block['hash'] = new_hash

        # Persist the genesis block to the blockchain
        genesis_block = models.Block(
            index=block['index'], transactions=block['transactions'], nonce=block['nonce'], prev_hash=block['prev_hash'], hash=block['hash'])

        self.chain.append(genesis_block)
        # add the new block to the block chain

        db_chain = models.Blockchain(
            chain=self.chain
        )

        try:
            db.add_all([genesis_block, db_chain])
            db.commit()
            db.refresh(genesis_block)
            db.refresh(db_chain)

            return genesis_block
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

    def create_transaction(self, db: Session, transaction: schemas.Transaction):

        transaction_string = json.dumps(
            transaction.data, sort_keys=True).encode()
        transaction_signature = json.dumps(transaction.signature)

        db_transaction = models.Transaction(
            transaction_id=transaction.transaction_id, signature=transaction_signature, data=transaction_string, pub_key=transaction.pub_key)
        db.add(db_transaction)

        try:
            db.commit()
            db.refresh(db_transaction)

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

        # get instance of  the transaction pool and check if the pool has reached 100
        if len(self.transaction_pool) + 1 == 5:
            self.transaction_pool.append(transaction.data)

            self.mine(self.transaction_pool, db=db)

        else:
            self.transaction_pool.append(transaction.data)
            print("Transaction pool checked, not mining a new block....",
                  len(self.transaction_pool))

        return db_transaction

    def mine(self, transactions, db: Session):
        """
        This function serves as an interface to add the pending
        transactions from the pool to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """

        last_block = self.get_last_block(db)

        previous_hash = last_block['hash']

        current_index = last_block['index'] + 1

        # When the node creates blocks, we create a Merkle tree of 100 messages.
        # This produces Merkle root hash. Sign this hash and persist it.
        # Ignoring this for now
        block = {}
        block['index'] = current_index
        block['nonce'] = 123
        block['prev_hash'] = previous_hash
        block['transactions'] = transactions

        proof = self.proof_of_work(block)
        self.add_block(block, proof, db=db)

        self.transaction_pool = []
        print("Block #{} is mined.".format(current_index))

        return block

    @staticmethod
    def proof_of_work(block):
        mining = False
        while mining is False:
            # encode the new block received
            print("Mining a new block with the nonce: ", block['nonce'])
            encode_block = json.dumps(block, sort_keys=True).encode()
            new_hash = hashlib.sha256(encode_block).hexdigest()

            if new_hash[:5] == '00009':
                mining = True
            else:
                block['nonce'] += 1
                encoded_block = json.dumps(block, sort_keys=True).encode()
                new_hash = hashlib.sha256(encoded_block).hexdigest()

        block['hash'] = new_hash
        print("New block mined  with hash: ", block['hash'])

        return block['hash']

    def add_block(self, block, proof, db: Session):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """

        last_block = self.get_last_block(db)  # Also: self.chain[-1]
        previous_hash = last_block['hash']
        if previous_hash != block['prev_hash']:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        # New block is mined, persist it to the chain, with the new hash
        db_block = models.Block(
            index=block['index'], transactions=block['transactions'], nonce=block['nonce'], timestamp=block['timestamp'], prev_hash=block['prev_hash'], hash=proof)

        # Append and persist the new block to the block chain
        self.chain.append(block)
        db_chain = models.Blockchain(
            chain=self.chain
        )

        try:
            db.add_all([db_block, db_chain])
            db.commit()
            db.refresh(db_block)
            db.refresh(db_chain)

            return True

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

    def get_transaction_by_id(self, db: Session, transaction_id: int):
        return db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()

    def get_blocks(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Block).offset(skip).limit(limit).all()

    def get_block_by_id(self, db: Session, blockIndex: int):
        return db.query(models.Block).filter(models.Block.index == blockIndex).first()

    def get_last_block(self, db: Session):
        blocks = self.get_blocks(db)

        chain_length = len(blocks)
        last_block = self.get_block_by_id(db=db, blockIndex=chain_length)

        return last_block

    @property
    def last_block(self):
        return self.chain[-1]

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        encoded_block = json.dumps(block, sort_keys=True).encode()
        new_hash = hashlib.sha256(encoded_block).hexdigest()
        print(new_hash == block_hash)

        return (block_hash.startswith('00009') and block_hash == new_hash)


# def proof_of_work(block):
#     mining = False
#     while mining is False:
#         # encode the new block received
#         encode_block = json.dumps(block, sort_keys=True).encode()
#         new_hash = hashlib.sha256(encode_block).hexdigest()

#         if new_hash[:5] == '00009':
#             mining = True
#         else:
#             block['nonce'] += 1
#             encoded_block = json.dumps(block, sort_keys=True).encode()
#             new_hash = hashlib.sha256(encoded_block).hexdigest()

#     block['hash'] = new_hash

#     return block['hash']


# def add_block(block, proof):
#     pass


# def generate_keypair():
#     success = wallet.generate_key_pair()

#     return success

# def check_valid_transactions(db: Session):
#     verified_transactions = []

#     transactions = get_transactions(db)

#     print("Verified transactions: ", transactions)
#     for trx in transactions:
#         data = json.loads(trx['transaction'])
#         signature = trx['signature']
#         string_transaction = json.dumps(data, sort_keys=True).encode()
#         signature = eval(signature)

#         pub, key2 = keys.get_public_keys_from_sig(
#             signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

#         is_valid = ecdsa.verify(
#             signature, string_transaction, pub, curve.secp256k1, ecdsa.sha256)

#         if is_valid:
#             verified_transactions.append(data)

#     return verified_transactions


# def get_transactions(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.BlockchainTransaction).offset(skip).limit(limit).all()
