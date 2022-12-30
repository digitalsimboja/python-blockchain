from datetime import datetime
from sqlalchemy.orm import Session
import random

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


def mine_block(db: Session, data: str):
    """
        Mines a new block and adds to the blockchain
    """
    previous_hash = ""
    block = {}
    # block['nonce'] = random.getrandbits(64)
    block['nonce'] = 123
    block['data'] = data

    # get the chains
    chain = get_chains(db)
    current_index = len(chain) + 1
    chain_length = len(chain)
    last_block = get_chain_by_id(db=db, chainId=chain_length)
    previous_hash = last_block['hash']

    block['index'] = current_index
    block['prev_hash'] = previous_hash

    mining = False
    while mining is False:
        encode_block = json.dumps(block, sort_keys=True).encode()
        new_hash = hashlib.sha256(encode_block).hexdigest()

        if new_hash[:5] == '00009':
            mining = True
        else:
            block['nonce'] += 1
            encoded_block = json.dumps(block, sort_keys=True).encode()
            new_hash = hashlib.sha256(encoded_block).hexdigest()

    block['hash'] = new_hash

    # New block is mined, persist it to the chain
    db_chain = models.BlockchainChain(
        block=block['index'], nonce=block['nonce'], prev_hash=block['prev_hash'], data=block['data'], hash=block['hash'])
    db.add(db_chain)
    db.commit()
    db.refresh(db_chain)
    
    return db_chain


def get_chains(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BlockchainChain).offset(skip).limit(limit).all()


def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BlockchainTransaction).offset(skip).limit(limit).all()


def get_transaction_by_id(db: Session, transaction_id: int):
    return db.query(models.BlockchainTransaction).filter(models.BlockchainTransaction.transaction_id == transaction_id).first()


def get_chain_by_id(db: Session, chainId: int):
    return db.query(models.BlockchainChain).filter(models.BlockchainChain.id == chainId).first()


# def create_chain(db: Session, chain: schemas.BlockchainChainCreate):
#     db_chain = models.BlockchainChain(block=chain.block, nonce=chain.nonce, hash=chain.hash,
#                                       prev_hash=chain.prev_hash, timestamp=chain.timestamp, data=chain.data)
#     db.add(db_chain)
#     db.commit()
#     db.refresh(db_chain)

#     return db_chain
