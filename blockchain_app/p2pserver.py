from uuid import uuid4
from urllib.parse import urlparse
import zmq
import json
import pickle
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from . import models, serialize


class Peer2PeerServer:
    def __init__(self):
        self.uuid = str(uuid4()).replace('-', '')
        self.address = "tcp://localhost"
        self.broadcast_trans_port = 22344
        self.broadcast_chain_port = 21344

    def add_peer(self, address, db: Session):
        parsed_url = urlparse(address)
        net = parsed_url.netloc
        net_object = net.split(':')
        peer_ip = net_object[0]

        db_peer = models.Peer(
            ip=peer_ip
        )
        db.add(db_peer)

        try:
            db.commit()
            db.refresh(db_peer)
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))
        finally:
            db.close()

        return

    def add_node(self, address, db: Session):
        parsed_url = urlparse(address)

        db_node = models.Node(
            url=parsed_url
        )
        db.add(db_node)

        try:
            db.commit()
            db.refresh(db_node)
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(
                "Failed to Commit because of {error}. Doing Rollback".format(error=e))
        finally:
            db.close()

        return

    def bind_transaction_broadcast_port(self, context):
        publisher = context.socket(zmq.PUB)
        publisher.bind('tcp://*:{}'.format(self.broadcast_trans_port))
        return publisher

    def bind_chain_broadcast_port(self, context):
        publisher = context.socket(zmq.PUB)
        publisher.bind('tcp://*:{}'.format(self.broadcast_chain_port))
        return publisher

    def broadcast_transaction(self, transaction, publisher):
        j_transaction = json.dumps(transaction, sort_keys=True).encode()
        publisher.send_json(j_transaction)
        print('Just broadcasted transaction: {}'.format(j_transaction))
        return

    def broadcast_chain(self, chain, publisher):
        j_chain = serialize.serialize(chain)
        publisher.send_json(j_chain)
        print('Just broadcasted chain: {}'.format(j_chain))
        return

    # ChainSubscriber channel
    def add_chain_subscribe_socket(self, address, chain_sub, chain_port):
        parsed_url = urlparse(address)
        net = parsed_url.netloc
        net_object = net.split(':')
        peer = net_object[0]

        chain_sub.connect("tcp://{}:{}".format(peer, chain_port))
        chain_sub.setsockopt_string(zmq.SUBSCRIBE, '')
        print('waiting for the chain from {} on Port: {}'.format(peer, chain_port))
        return

    # Transaction subscriber channel
    def add_transaction_subscribe_socket(self, address, trans_sub, trans_port):
        parsed_url = urlparse(address)
        net = parsed_url.netloc
        net_object = net.split(':')
        peer = net_object[0]

        trans_sub.connect("tcp://{}:{}".format(peer, trans_port))
        trans_sub.setsockopt_string(zmq.SUBSCRIBE, '')
        print('waiting for transactions from {} on Port: {}'.format(peer, trans_port))
        return
