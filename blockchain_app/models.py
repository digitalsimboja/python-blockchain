import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base

class BlockchainChain(Base):
    __tablename__ = "blockchain_chain"

    id = Column(Integer, primary_key=True, index=True)
    block = Column(Integer, unique=True, index=True)
    nonce = Column(Integer, unique=True)
    prev_hash = Column(String)
    data = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    hash = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]
    
    

# Model for creating transaction pool
class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True)
    pub_key = Column(String)
    signature = Column(String)    
    transaction = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def __getitem__(self, field):
        return self.__dict__[field]

