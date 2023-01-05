from typing import List
import requests
import config
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastecdsa import curve, ecdsa, keys, point
from fastecdsa.keys import export_key, import_key, gen_keypair
import json
import os
import time
import logging
import threading
import zmq
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse

from . import models, schemas, blockchain, wallet, p2pserver

from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# app.config.from_object(config.config['development'])

session = requests.Session()
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

# Dependency
chain = blockchain.Blockchain()
account = wallet.Wallet()
peerserver = p2pserver.Peer2PeerServer()

# Initialise ZMQ Context
context = zmq.Context()

# Set up the publishers
transaction_publisher = peerserver.bind_transaction_broadcast_port(context)
chain_publisher = peerserver.bind_chain_broadcast_port(context)

# Set up the subscribers
transaction_subscriber = context.socket(zmq.SUB)
chain_subscriber = context.socket(zmq.SUB)

account.generate_key_pair()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Construct a transaction

@app.get("/")
async def root():
    return {"message": "Welcome to the Python Blockchain"}


@app.post("/create-genesis-block", response_model=schemas.Block)
async def create_genesis_block(db: Session = Depends(get_db)):
    genesis_block = chain.create_genesis_block(db)

    return genesis_block

# endpoint to submit a new transaction. This will be used by
# our application to add new data  to the blockchain


@app.post('/new-transaction', response_model=schemas.Transaction)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    new_transaction = transaction
    db_transaction = chain.get_transaction_by_id(
        db, transaction_id=new_transaction.transaction_id)
    if db_transaction:
        raise HTTPException(
            status_code=400, detail="Transaction already exists")

    trx = chain.create_transaction(db=db, transaction=new_transaction)

    return trx


@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = chain.get_transaction_by_id(
        db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction


@app.get("/check-transactions", response_model=schemas.Transaction)
def get_valid_transactions(db: Session = Depends(get_db)):
    valid_transactions = chain.check_valid_transactions(db=db)

    return valid_transactions


def initializeLeaderNode(db):
    # Start by Creating the Genesis Block
    chain.create_genesis_block(db)

    # Set a timeline for mining a new block
    # Check the transactions pool, if they are more than 100,
    # wait for 60 seconds and mine again
    while True:
        transactions = chain.get_transactions(db)

        print(f"Mining a new transaction: #{len(transactions)}")
        if len(transactions) > 10:
            mined_block = chain.proof_of_work(db)

            blockchain = chain.get_blocks(db)

            # broadcast the new chain
            peerserver.broadcast_chain(blockchain, chain_publisher)

            print(
                'Just mined a block and broadcasted the new chain {}'.format(len(transactions)))

        # wait for one minute before checking again
        print("Checking if we have 100 transactions in the pool after 60 seconds: ", transactions)
        time.sleep(10)


def await_transaction_broadcast(db):
    while True:
        trans_response = transaction_subscriber.recv_json()
        transaction = json.loads(trans_response)
        if "signature" in transaction:
            # Add the Transaction to the pool
            string_signature = transaction['signature']
            signature = eval(string_signature)

            transaction.pop('signature')

            string_transaction = json.dumps(
                transaction, sort_keys=True).encode()
            key1, key2 = keys.get_public_keys_from_sig(
                signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

            chain.add_transaction(
                key1, transaction, signature, transaction['transaction_id'], db=db)
            print('Just received transaction broadcast {}: and added it to transaction pool'.format(
                transaction))


def await_chain_broadcast(db: Session):
    while True:
        chain_result = chain_subscriber.recv_json()
        new_chain = json.loads(chain_result)

        print('We just received a new chain \n {}'.format(new_chain))

        if not 'signature' in new_chain:
            # Get the chain from the database
            blockchain = chain.get_blocks(db)

            if blockchain == []:
                # The chain table is empty
                for blk in new_chain:
                    new_block = {}
                    new_block['block'] = blk['block']
                    new_block['nonce'] = blk['nonce']
                    new_block['hash'] = blk['hash']
                    new_block['transactions'] = blk['transactions']

                    db_block = models.Block(
                        block=new_block['block'], transactions=new_block['transactions'], nonce=new_block['nonce'], prev_hash=new_block['prev_hash'], hash=new_block['hash'])
                    db.add(db_block)

                try:
                    db.commit()
                    db.refresh(db_block)
                    pass
                except SQLAlchemyError as e:
                    db.rollback()
                    logging.error(
                        "Failed to Commit because of {error}. Doing Rollback".format(error=e))
            else:
                db.close()

                if len(new_chain) > len(blockchain):
                    # We already have a chain table in our database saved - we just need to confirm the new chain is valid
                    if chain.is_valid_chain(new_chain, db=get_db()):
                        # The received chain is valid - genesis blocks match and all block hashes and nonces also match
                        new_transactions = new_chain[len(
                            new_chain)-1]['transactions']

                        verified_transactions = []

                        for trx in new_transactions:
                            id = trx['id']
                            data = json.loads(trx['data'])
                            signature_string = trx['signature']
                            string_transaction = json.dumps(
                                data, sort_keys=True).encode()
                            signature = eval(signature_string)

                            pub, key2 = keys.get_public_keys_from_sig(
                                signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

                            is_valid = ecdsa.verify(
                                signature, string_transaction, pub, curve.secp256k1, ecdsa.sha256)
                            if is_valid:
                                verified_transactions.append(data)
                                print('Valid Transaction -> {}'.format(data))
                            else:
                                print(
                                    'The following transaction is not valid, cannot accept this new chain: {}'.format(trx))
                                pass
                        # Replace our chain with new chain - if chain is valid and all transactions in the last block are also valid
                        db = get_db()
                        # Start by deleting the current chain from database
                        db.query(models.Block).delete()
                        db.commit()
                        # We also need to delete everything from the transaction table - because the transactions have been mined in this block.
                        db.query(models.Transaction).delete()
                        db.commit()
                        # then save new blockchain in to our database
                        for blk in new_chain:
                            new_block = {}
                            new_block['block'] = blk['block']
                            new_block['nonce'] = blk['nonce']
                            new_block['hash'] = blk['hash']
                            new_block['prev_hash'] = blk['prev_hash']
                            new_block['transactions'] = blk['transactions']

                            db_block = models.Block(
                                block=new_block['block'], transactions=new_block['transactions'], nonce=new_block['nonce'], prev_hash=new_block['prev_hash'], hash=new_block['hash'])
                            db.add(db_block)

                        try:
                            db.commit()
                            db.refresh(db_block)
                            pass
                        except SQLAlchemyError as e:
                            db.rollback()
                            logging.error(
                                "Failed to Commit because of {error}. Doing Rollback".format(error=e))
                        db.close()

                    else:
                        # Received chain is not valid
                        print('Received chain is not valid --> DISCARD')
                        pass
                else:
                    print(
                        'Received chain is shorter than or equal to the chain we already have -- > DISCARD')
                    pass
        else:
            # This is a transaction - transaction function will handle . . . .
            pass

# Connect Node Function - From the Connecting Nodes


def createBlockchainConnection(db):
    # Create a POST Request to the ALPHA NODE .....
    url = app.config['ALPHA_NODE'] + 'connect-node'
    data = {'node': app.config['THIS_NODE']}
    r = requests.post(url, json=data)
    response = json.loads(r.text)

    # Subscribe to the Alpha Node
    peerserver.add_transaction_subscribe_socket(
        app.config['ALPHA_NODE'], transaction_subscriber, '22344')
    peerserver.add_chain_subscribe_socket(
        app.config['ALPHA_NODE'], chain_subscriber, '21344')

    if len(response['nodes']) > 0:
        # We already have more than one Node connected
        # Send Connections to all the nodes in the list
        for node in response['nodes']:
            requests.post("http://{}/connect-node".format(node), json=data)
            # Subscribe to all the nodes in the list
            peerserver.add_transaction_subscribe_socket(
                "http://{}/".format(node), transaction_subscriber, '22344')
            peerserver.add_chain_subscribe_socket(
                "http://{}/".format(node), chain_subscriber, '21344')

    while True:
        # Get the Transactions
        transactions = chain.get_transactions(db)

        # Check if we have more than 100 Transactions in the pool
        if len(transactions) > 100:
            chain.proof_of_work(db)

            blockchain = chain.get_blocks(db)

            # broadcast the new chain
            peerserver.broadcast_chain(blockchain, chain_publisher)
            print(
                'Just mined a block and broadcasted the new chain {}'.format(blockchain))

        db.close()

        # wait for one minute before checking again
        time.sleep(app.config['WAIT_TIME'])

# Connecting new nodes - New nodes will hit this route to get connected


@app.post('/connect-node', response_model=schemas.Node)
def connect_node(request: Request, db: Session = Depends(get_db)):
    data = request.body()
    node = data['node']

    # http://the-ip-address:PORT

    # Get the new chain
    blockchain = chain.get_blocks(db)

    # Get the Nodes - We need to send the IP addresses so this node can also subscribe to them .....
    nodes = chain.get_nodes(db)

    # We need to do a check that the node does not already exists in our database before we add it
    for x in nodes:
        parsed_x = urlparse(x)
        parsed_node = urlparse(node)
        if parsed_x.netloc == parsed_node.netloc:
            # This URL is already in our database
            print('This URL is already in our database')
            return 'FAILED: ALREADY IN DATABASE'

    # If the URL does not already exist - we can proceed with adding it to the database
    # Add the node to the database
    peerserver.add_peer(node, db)
    peerserver.add_node(node, db)

    # We then need to subscribe to this new node -
    peerserver.add_transaction_subscribe_socket(
        node, transaction_subscriber, '22344')
    peerserver.add_chain_subscribe_socket(node, chain_subscriber, '21344')

    # Send everyone a copy of the chain - so the new connection can have it.
    if blockchain > 0:
        peerserver.broadcast_chain(chain, chain_publisher)

    response = {'nodes': nodes}
    db.close()
    return response


def test_send_transaction():

    start = time.time()
    timeout = start + 60
    while start < timeout:

        # receiver_priv_key = account.generate_private_key()
        # receiver_pub_key = account.generate_public_key(receiver_priv_key)

        data = "Buy me a coffee"
        priv_key, pub_key = import_key(
            os.path.join("blockchain/keys/secp256k1.key"))

        transaction = account.create_transaction(data)
        string_transaction = json.dumps(transaction, sort_keys=True).encode()
        signature = ecdsa.sign(string_transaction, priv_key,
                               curve=curve.secp256k1, hashfunc=ecdsa.sha256)

        transaction['signature'] = json.dumps(signature)
        transaction['pub_key'] = json.dumps((pub_key.x, pub_key.y))

        to_send = json.dumps(transaction, sort_keys=True)

        verified = account.validate_transaction(to_send)

        if verified:
            trx = requests.post(
                "http://new-transaction", transaction)
            print('Just received transaction broadcast {}: and added it to transaction pool'.format(
                trx))
        else:
            print("You have sent an invalid transaction")

        start += 1
        time.sleep(10)


# If you were not the Alpha node
# t1 = threading.Thread(target=createBlockchainConnection, daemon=True, args=get_db())
thread1 = threading.Thread(
    target=initializeLeaderNode, daemon=True, args=get_db())
thread2 = threading.Thread(
    target=await_transaction_broadcast, daemon=True, args=get_db())
thread3 = threading.Thread(
    target=await_chain_broadcast, daemon=True, args=get_db())
thread4 = threading.Thread(
    target=test_send_transaction, daemon=True)

thread1.start()
thread2.start()
thread3.start()
# thread4.start()
