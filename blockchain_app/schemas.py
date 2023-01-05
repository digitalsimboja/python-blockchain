from typing import List
from datetime import datetime

from pydantic import BaseModel


class BlockBase(BaseModel):
    block: int
    nonce: int
    prev_hash: str
    root_hash: str
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


class TransactionCreate(TransactionBase):
    # transactions: list
    pass


class Transaction(TransactionBase):
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
