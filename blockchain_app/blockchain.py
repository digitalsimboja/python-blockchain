from sqlalchemy.orm import Session

from . import models, schemas

def get_chain(db: Session, chain_block: int):
    return db.query(models.BlockchainChain).filter(models.BlockchainChain.id == chain_block).first()

def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BlockchainTransaction).offset(skip).limit(limit).all()

def create_chain(db: Session, chain: schemas.BlockchainChainCreate):
    db_chain = models.BlockchainChain(block=chain.block, nonce=chain.nonce, hash=chain.hash, prev_hash=chain.prev_hash, timestamp=chain.timestamp, data=chain.data)
    db.add(db_chain)
    db.commit()
    db.refresh(db_chain)

    return db_chain

def add_blockchain_transaction(db: Session, transaction: schemas.BlockchainTransaction):
    db_transaction = models.BlockchainTransaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction