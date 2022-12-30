from datetime import datetime
from sqlalchemy.orm import Session

import hashlib
import json

from . import models, schemas


def create_genesis_block(db: Session):

    block = {}
    block['index'] = 1
    block['nonce'] = 123
    block['prev_hash'] = '0000000000'
    block['data'] = "This is the genesis block of the python blockchain"

    encode_block = json.dumps(block, sort_keys=True).encode()
    new_hash = hashlib.sha256(encode_block).hexdigest()

    block['hash'] = new_hash

    # Persist the genesis block to the blockchain
    db_chain = models.BlockchainChain(
        block=block['index'], nonce=block['nonce'], prev_hash=block['prev_hash'], data=block['data'], hash=block['hash'])
    db.add(db_chain)
    db.commit()
    db.refresh(db_chain)

    return db_chain


def add_blockchain_transaction(db: Session, transaction: schemas.BlockchainTransaction):
    # Transaction does not exist so add to Database
    transaction_string = json.dumps(
            transaction.transaction, sort_keys=True).encode()
    transaction_signature = json.dumps(transaction.signature)
    db_transaction = models.BlockchainTransaction(
        transaction_id=transaction.transaction_id, signature=transaction_signature, transaction=transaction_string, pub_key=transaction.pub_key)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction


def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BlockchainTransaction).offset(skip).limit(limit).all()


def get_transaction_by_id(db: Session, transaction_id: int):
    return db.query(models.BlockchainTransaction).filter(models.BlockchainTransaction.transaction_id == transaction_id).first()


def mine_block(db: Session, data: str):
    # Get the first 100 transactions
    transactions = get_transactions(db)
    


# def get_chain(db: Session, chain_block: int):
#     return db.query(models.BlockchainChain).filter(models.BlockchainChain.id == chain_block).first()


# def create_chain(db: Session, chain: schemas.BlockchainChainCreate):
#     db_chain = models.BlockchainChain(block=chain.block, nonce=chain.nonce, hash=chain.hash,
#                                       prev_hash=chain.prev_hash, timestamp=chain.timestamp, data=chain.data)
#     db.add(db_chain)
#     db.commit()
#     db.refresh(db_chain)

#     return db_chain
