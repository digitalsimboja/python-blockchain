import datetime
from sqlalchemy import Column, Integer, String, DateTime, func, TypeDecorator
from sqlalchemy.ext.mutable import MutableList


from .database import Base


def get_current_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Define a custom TypeDecorator class for the datetime field


class DatetimeType(TypeDecorator):
    impl = DateTime

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value

    def process_result_value(self, value, dialect):
        if isinstance(value, str):
            return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    block = Column(Integer, unique=True)
    timestamp = Column(String)
    nonce = Column(Integer, unique=True)
    prev_hash = Column(String)
    root_hash = Column(String)
    hash = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]

    def __setattr__(self, field, timestamp):
        # Allow assignment to the timestamp attributes except for the id
        if field != 'id':
            object.__setattr__(self, field, timestamp)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String)
    pub_key = Column(String)
    data = Column(String)
    signature = Column(String)
    timestamp = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]


class Node(Base):
    __tablename__ = "nodes"

    id: id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    timestamp = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]


class Peer(Base):
    __tablename__ = "peers"

    id: id = Column(Integer, primary_key=True, index=True)
    ip: Column(String)
    timestamp = Column(String)

    def __getitem__(self, field):
        return self.__dict__[field]
