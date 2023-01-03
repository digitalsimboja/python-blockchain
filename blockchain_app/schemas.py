from typing import List
from datetime import datetime

from pydantic import BaseModel


class BlockBase(BaseModel):
    block: int
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
    data: str
    pub_key: str
    signature: str
    timestamp: datetime = None


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int

    class Config:
        orm_mode = True


class BlockchainBase(BaseModel):
    blocks: list


class BlockchainCreate(BlockchainBase):
    pass


class Blockchain(BlockchainBase):
    id: int

    class Config:
        orm_mode = True


class NodeBase(BaseModel):
    url: str


class NodeBaseCreate(NodeBase):
    pass


class Node(NodeBase):
    id: int

    class Config:
        orm_mode = True

class PeerBase(BaseModel):
    ip: str


class PeerBaseCreate(PeerBase):
    pass


class Peer(PeerBase):
    id: int

    class Config:
        orm_mode = True



