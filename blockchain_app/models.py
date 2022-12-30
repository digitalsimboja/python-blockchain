import datetime
from sqlalchemy import Column, Integer, String, DateTime, PickleType

from .database import Base

class BlockchainChain(Base):
    __tablename__ = "blockchain_chain"

    id = Column(Integer, primary_key=True, index=True)
    block = Column(Integer, unique=True, index=True)
    nonce = Column(Integer, unique=True)
    hash = Column(String)
    prev_hash = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(PickleType)

# Model for creating transaction pool
class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True)
    pub_key = Column(String)
    signature = Column(String)    
    transaction = Column(PickleType)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
