from typing import List, Dict
from datetime import datetime

from pydantic import BaseModel


class BlockchainChainBase(BaseModel):
    block: int
    nonce: int
    hash: str
    prev_hash: str
    timestamp: datetime = None
    data: dict = None


class BlockchainChainCreate(BlockchainChainBase):
    pass

class BlockchainChain(BlockchainChainBase):
    id: int

    class Config:
        orm_mode = True


class BlockchainTransactionBase(BaseModel):
    transaction_id: str
    signature: str
    transaction: dict = None
    pub_key: str
    timestamp: datetime = None


class BlockchainTransactionCreate(BlockchainTransactionBase):
    pass


class BlockchainTransaction(BlockchainTransactionBase):
    id: int

    class Config:
        orm_mode = True
