from typing import List
from datetime import datetime

from pydantic import BaseModel


class BlockBase(BaseModel):
    index: int
    transactions: list
    timestamp: datetime = None
    nonce: int
    prev_hash: str
    hash: str


class BlockCreate(BlockBase):
    pass

class Block(BlockBase):
    id: int

    class Config:
        orm_mode = True


class TransactionBase(BaseModel):
    transaction_id: str
    pub_key: str
    signature: str
    data: str
    timestamp: datetime = None


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int

    class Config:
        orm_mode = True


class Blockchain(BaseModel):
    id: int
    chain: list