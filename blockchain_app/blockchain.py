from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
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
        self.blocks = []

    def create_genesis_block(self, db: Session):

        block = {}
        block['block'] = 1
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
            block=block['block'], transactions=block['transactions'], nonce=block['nonce'], prev_hash=block['prev_hash'], hash=block['hash'])

        self.blocks.append(genesis_block)
        # add the new block to the block chain

        db_chain = models.Blockchain(
            blocks=self.blocks
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

        db_transaction = models.Transaction(
            transaction_id=transaction.transaction_id, data=transaction_string, pub_key=transaction.pub_key, signature=transaction.signature)
        db.add(db_transaction)

        try:
            db.commit()
            db.refresh(db_transaction)

            return db_transaction

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

    def add_transaction(self, pub_key, new_transaction, signature, transaction_id, db: Session):
        db_transaction = self.get_transaction_by_id(
            db, transaction_id=transaction_id)
        if db_transaction:
            print('transaction {} already exists in the pool'.format(new_transaction))

            return
        transaction_string = json.dumps(
            new_transaction, sort_keys=True).encode()
        string_signature = json.dumps(signature)

        db_transaction = models.Transaction(
            transaction_id=transaction_id, data=transaction_string, signature=string_signature, pub_key=pub_key)
        db.add(db_transaction)

        try:
            db.commit()
            db.refresh(db_transaction)

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

        chain = self.get_blocks(db)

        return len(chain) + 1

    def mine(self, transactions, db: Session):
        """
        This function serves as an interface to add the pending
        transactions from the pool to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """

        last_block = self.get_last_block(db)  # self.blocks[-1]

        previous_hash = last_block['hash']

        current_index = last_block['block'] + 1

        # When the node creates blocks, we create a Merkle tree of 100 messages.
        # This produces Merkle root hash. Sign this hash and persist it.
        # Ignoring this for now
        block = {}
        block['block'] = current_index
        block['nonce'] = 123
        block['prev_hash'] = previous_hash
        block['transactions'] = transactions

        proof = self.proof_of_work(block)
        added = self.add_block(block, proof, db=db)

        if added:

            print("Block #{} is mined.".format(current_index))

        return False

    def proof_of_work(self, db: Session):
        # Let us verify all the transactions in the pool
        verified_transactions = self.check_valid_transactions(db)

        last_block = self.get_last_block(db)  # self.blocks[-1]

        previous_hash = last_block['hash']

        current_index = last_block['block'] + 1

        # When the node creates blocks, we create a Merkle tree of 100 messages.
        # This produces Merkle root hash. Sign this hash and persist it.
        # Ignoring this for now
        block = {}
        block['block'] = current_index
        block['nonce'] = 123
        block['prev_hash'] = previous_hash
        # Create the merkle root hash
        block['transactions'] = verified_transactions

        mining = False
        while mining is False:
            encoded_block = json.dumps(block, sort_keys=True).encode()
            new_hash = hashlib.sha256(encoded_block).hexdigest()

            if new_hash[:5] == '00009':
                mining = True
            else:
                block['nonce'] += 1

                encoded_block = json.dumps(block, sort_keys=True).encode()
                new_hash = hashlib.sha256(encoded_block).hexdigest()

        block['hash'] = new_hash

        # Append and persist the new block to the block chain
        self.blocks.append(block)

        # New block is mined, persist it to the chain, with the new hash
        db_block = models.Block(
            block=block['block'], transactions=block['transactions'], nonce=block['nonce'], prev_hash=block['prev_hash'], hash=block['hash'])

        try:
            db.add(db_block)
            db.commit()
            db.refresh(db_block)

            return block

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

    def add_block(self, block, db: Session):
        db_block = models.Block(
            block=block['block'], transactions=block['transactions'], nonce=block['nonce'], prev_hash=block['prev_hash'], hash=block['hash'], timestamp=block['timestamp'])

        try:
            db.add(db_block)
            db.commit()
            db.refresh(db_block)

            return True

        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))

    def get_transactions(self, db: Session,  skip: int = 0, limit: int = 100):
        return db.query(models.Transaction).offset(skip).limit(limit).all()

    def get_transaction_by_id(self, db: Session, transaction_id: int):
        return db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()

    def get_blocks(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Block).offset(skip).limit(limit).all()

    def get_block_by_id(self, db: Session, blockIndex: int):
        return db.query(models.Block).filter(models.Block.block == blockIndex).first()

    def get_last_block(self, db: Session):
        blocks = self.get_blocks(db)

        chain_length = len(blocks)
        last_block = self.get_block_by_id(db=db, blockIndex=chain_length)

        return last_block

    def get_nodes(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Nodes).offset(skip).limit(limit).all()

    @property
    def last_block(self):
        return self.chain[-1]

    @classmethod
    def is_valid_proof(cls, block, proof):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        encoded_block = json.dumps(block, sort_keys=True).encode()
        new_hash = hashlib.sha256(encoded_block).hexdigest()

        return (proof.startswith('00009') and proof == new_hash)

    def check_valid_transactions(self, db: Session):
        verified_transactions = []

        transactions = self.get_transactions(db)

        for trx in transactions:
            id = trx.id
            data = json.loads(trx['data'])
            signature_string = trx.signature
            string_transaction = json.dumps(data, sort_keys=True).encode()
            signature = eval(signature_string)

            pub, key2 = keys.get_public_keys_from_sig(
                signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

            is_valid = ecdsa.verify(
                signature, string_transaction, pub, curve.secp256k1, ecdsa.sha256)

            if is_valid:
                verified_transactions.append(data)
                # Prune/Delete the record from the transaction pool
                db.query(models.Transaction).filter(
                    models.Transaction.id == id).delete()
                db.commit()

        return verified_transactions

    def is_valid_chain(self, chain, db: Session):
        first_block = chain[0]

        genesis_block = self.get_transaction_by_id(db, transaction_id=1)

        # Check that received chain has same Genesis block as our chain
        encoded_block_1 = json.dumps(first_block, sort_keys=True).encode()
        hash_1 = hashlib.sha256(encoded_block_1).hexdigest()

        encoded_block_2 = json.dumps(genesis_block, sort_keys=True).encode()
        hash_2 = hashlib.sha256(encoded_block_2).hexdigest()

        if not hash_1 == hash_2:
            print('validity failed comparing genesis blocks')
            return False

        blockchain = self.get_blocks(db)
        # Now we check for the hash signature of every block in the chain - comparing it to our own . . . .

        block_index = 1
        while block_index < len(blockchain):
            block = chain[block_index]
            our_block = blockchain[block_index]

            encoded_block_1 = json.dumps(block, sort_keys=True).encode()
            hash_1 = hashlib.sha256(encoded_block_1).hexdigest()

            encoded_block_2 = json.dumps(our_block, sort_keys=True).encode()
            hash_2 = hashlib.sha256(encoded_block_2).hexdigest()

            if not hash_1 == hash_2:
                print('validity failed comparing #hash for block at index {}'.format(
                    block_index))
                return False

            if not block['nonce'] == our_block['nonce']:
                print('validity failed comparing the nonce values and index {}'.format(
                    block_index))
                return False

            previous_block = block
            block_index += 1

        db.close()

        return True
