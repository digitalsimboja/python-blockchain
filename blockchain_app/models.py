import datetime
from sqlalchemy import Column, Integer, String, DateTime, PickleType
from sqlalchemy.ext.mutable import MutableList

from .database import Base


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    block = Column(Integer, unique=True)
    transactions = Column(MutableList.as_mutable(PickleType), default=[])
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    nonce = Column(Integer, unique=True)
    prev_hash = Column(String)
    hash = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]


class Blockchain(Base):
    __tablename__ = "blockchain"

    id = Column(Integer, primary_key=True, index=True)
    blocks = Column(MutableList.as_mutable(PickleType), default=[])
    # hash = Column(String)
    # signed_hash = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String)
    pub_key = Column(String)
    data = Column(String)
    signature = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def __getitem__(self, field):
        return self.__dict__[field]


class Node(Base):
    __tablename__ = "nodes"

    id: id = Column(Integer, primary_key=True, index=True)
    url = Column(String)


class Peer(Base):
    __tablename__ = "peers"

    id: id = Column(Integer, primary_key=True, index=True)
    ip: Column(String)
