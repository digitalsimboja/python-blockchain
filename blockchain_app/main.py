from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas, blockchain

from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
chain = blockchain.Blockchain()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Welcome to the Python Blockchain"}


@app.post("/", response_model=schemas.Block)
def create_genesis_block(db: Session = Depends(get_db)):
    genesis_block = chain.create_genesis_block(db)

    return genesis_block

# endpoint to submit a new transaction. This will be used by
# our application to add new data  to the blockchain
@app.post('/new_transaction', response_model=schemas.Transaction)
def add_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # Check if transaction already exists in the database
    # Validate the message/transaction
    #  1:   The message schema is valid.
    # 2:  The message is signed.
    # 3:  The signature is valid and the message indeed came from the client who sent it.
    # TODO: verify if the sender is actually the sender
    db_transaction = chain.get_transaction_by_id(
        db, transaction_id=transaction.transaction_id)
    if db_transaction:
        raise HTTPException(
            status_code=400, detail="Transaction already exists")
    trx = chain.create_transaction(db=db, transaction=transaction)

    return trx


# @app.post("/create-keypair")
# def generate_keypair():
#     success = blockchain.generate_keypair()
#     if success:
#         return True
#     else:
#         raise HTTPException(
#             status_code=400, detail="Failed to generate keypair")


# @app.get("/transactions/{transaction_id}", response_model=schemas.BlockchainTransaction)
# def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
#     db_transaction = blockchain.get_transaction_by_id(db, transaction_id=transaction_id)
#     if db_transaction is None:
#         raise HTTPException(status_code=404, detail="Transaction not found")
#     return db_transaction

# @app.post("/mine", response_model=schemas.BlockchainChain)
# def mine_block(data: str, db: Session = Depends(get_db)):
#     blk = blockchain.mine_block(data= data, db=db)

#     return blk

# @app.get("/check-transactions", response_model=schemas.BlockchainTransaction)
# def get_valid_transactions(db: Session = Depends(get_db)):
#     valid_transactions = blockchain.check_valid_transactions(db=db)

#     return valid_transactions


# from flask import Flask, render_template, request, jsonify
# from wallet import Wallet
# from blockchain import Blockchain
# from p2pserver import Peer2PeerServer
# from flask_mysqldb import MySQL
# import json
# from fastecdsa import curve, ecdsa, keys, point
# from fastecdsa.keys import export_key, import_key, gen_keypair
# from datetime import datetime
# from uuid import uuid4
# import hashlib
# import requests
# from urllib.parse import urlparse
# import zmq
# import threading
# import time


# def page_not_found(e):
#     return render_template('404.html'), 404


# app = Flask(__name__)

# app.register_error_handler(404, page_not_found)
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'blockchain'

# mysql = MySQL(app)

# wallet = Wallet()
# blockchain = Blockchain()
# peerserver = Peer2PeerServer()

# context = zmq.Context()

# #Set up the publishers
# transaction_publisher = peerserver.bind_transaction_broadcast_port(context)
# chain_publisher = peerserver.bind_chain_broadcast_port(context)

# #Set up the subscribers
# transaction_subscriber = context.socket(zmq.SUB)
# chain_subscriber = context.socket(zmq.SUB)

# @app.route('/')
# def index():
#     return render_template('index.html', **locals())


# @app.route('/test')
# def test():

#     data = {
#         "sender": "Sunday Mgbogu",
#         "contact": '2348063874746',
#         "messages": "This is a test transaction data"
#     }

#     priv_key, pub_key = import_key(
#         '/home/sunday/dev/keys/secp256k1.key')

#     transaction = wallet.create_transaction(data)

#     string_transaction = json.dumps(transaction, sort_keys=True).encode()
#     signature = ecdsa.sign(string_transaction, priv_key,
#                            curve=curve.secp256k1, hashfunc=ecdsa.sha256)

#     transaction['signature'] = json.dumps(signature)
#     to_send = json.dumps(transaction, sort_keys=True)

#     trans_result = to_send
#     transaction1 = json.loads(trans_result)

#     string_signature1 = transaction1['signature']
#     signature1 = eval(string_signature1)

#     transaction1.pop('signature')
#     string_transaction1 = json.dumps(transaction1, sort_keys=True).encode()

#     key1, key2 = keys.get_public_keys_from_sig(
#         signature1, string_transaction1, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

#     is_valid = ecdsa.verify(signature1, string_transaction1,
#                             key1, curve.secp256k1, ecdsa.sha256)

#     print('Just received transaction broadcast {}: and added it to transaction pool'.format(
#         transaction1))

#     return "<h3>If this is true, the signatures did match - or else. ---> {}</h3>".format(is_valid)


# # Get the list of transactions
# @app.route('/get-transactions', methods=['GET'])
# def get_transactions():

#     # Get the Transactions
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM blockchain_transactions")
#     transactions = cur.fetchall()

#     response = {'transactions': transactions}

#     cur.close()
#     return jsonify(response), 200


# @app.route('/get-chain', methods=['GET'])
# def get_chain():

#     # Get the Transactions
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM blockchain_chain")
#     chain = cur.fetchall()

#     response = chain

#     cur.close()
#     return jsonify(response), 200


# # Connecting new nodes - New nodes will hit this route to get connected
# @app.route('/connect-node', methods=['POST'])
# def connect_node():
#     data = request.get_json()
#     node = data['node']

#     # Get the new chain
#     cur = mysql.connection.cursor()
#     result = cur.execute("SELECT * FROM blockchain_chain")
#     chain = cur.fetchall()

#     # Get the Nodes - We need to send the IP addresses so this node can also subscribe to them .....
#     cur.execute("SELECT * FROM blockchain_nodes")
#     nodes = cur.fetchall()

#     # We need to do a check that the node does not already exists in our database before we add it
#     for x in nodes:
#         parsed_x = urlparse(x)
#         parsed_node = urlparse(node)
#         if parsed_x.netloc == parsed_node.netloc:
#             # This URL is already in our database
#             print('This URL is already in our database')
#             return 'FAILED: ALREADY IN DATABASE'

#     # If the URL does not already exist - we can proceed with adding it to the database
#     # Add the node to the database
#     peerserver.add_peer(node, mysql)
#     peerserver.add_node(node, mysql)

#     # We then need to subscribe to this new node -
#     peerserver.add_transaction_subscribe_socket(
#         node, transaction_subscriber, '22344')
#     peerserver.add_chain_subscribe_socket(node, chain_subscriber, '21344')

#     # Send everyone a copy of the chain - so the new connection can have it.
#     if result > 0:
#         peerserver.broadcast_chain(chain, chain_publisher)

#     response = {'nodes': nodes}
#     cur.close()
#     return jsonify(response), 201


# # Other Functions that the blockchain needs . . . . .
# # Initialise the ALPHA Node
# def initialiseAlphaNode():
#     # Start by Creating the Genesis Block
#     blockchain.create_genesis_block(mysql)

#     # Then Set a timeline for mining new blocks - 60 seconds, then check transactions - if they are more than 100 - mine a new block
#     while True:
#         # Get the Transactions
#         cur = mysql.connection.cursor()
#         result = cur.execute("SELECT * FROM blockchain_transactions")
#         transactions = cur.fetchall()

#         if result > 0:
#             # Check if we have more than 100 Transactions in the pool
#             if len(transactions) > 100:
#                 block_response = blockchain.proof_of_work(mysql)

#                 cur.execute("SELECT * FROM blockchain_chain")
#                 chain = cur.fetchall()

#                 # broadcast the new chain
#                 peerserver.broadcast_chain(chain, chain_publisher)
#                 print(
#                     'Just mined a block and broadcasted the new chain {}'.format(chain))

#         cur.close()

#         # wait for 1 minute before checking again
#         time.sleep(60)


# # Connect Node Function - From the Connecting Nodes
# def createBlockchainConnection():
#     # Create a POST Request to the ALPHA NODE .....
#     url = app.config['ALPHA_NODE'] + 'connect-node'
#     data = {'node': app.config['THIS_NODE']}
#     r = requests.post(url, json=data)
#     response = json.loads(r.text)

#     # Subscribe to the Alpha Node
#     peerserver.add_transaction_subscribe_socket(
#         app.config['ALPHA_NODE'], transaction_subscriber, '22344')
#     peerserver.add_chain_subscribe_socket(
#         app.config['ALPHA_NODE'], chain_subscriber, '21344')

#     if len(response['nodes']) > 0:
#         # We already have more than one Node connected
#         # Send Connections to all the nodes in the list
#         for node in response['nodes']:
#             requests.post("http://{}/connect-node".format(node), json=data)
#             # Subscribe to all the nodes in the list
#             peerserver.add_transaction_subscribe_socket(
#                 "http://{}/".format(node), transaction_subscriber, '22344')
#             peerserver.add_chain_subscribe_socket(
#                 "http://{}/".format(node), chain_subscriber, '21344')

#     while True:
#         # Get the Transactions
#         cur = mysql.connection.cursor()
#         result = cur.execute("SELECT * FROM blockchain_transactions")
#         transactions = cur.fetchall()

#         if result > 0:
#             # Check if we have more than 100 Transactions in the pool
#             if len(transactions) > 100:
#                 blockchain.proof_of_work(mysql)

#                 cur.execute("SELECT * FROM blockchain_chain")
#                 chain = cur.fetchall()

#                 # broadcast the new chain
#                 peerserver.broadcast_chain(chain, chain_publisher)
#                 print(
#                     'Just mined a block and broadcasted the new chain {}'.format(chain))

#         cur.close()

#         # wait for one minute before checking again
#         time.sleep(app.config['WAIT_TIME'])


# # When we receive a new Transaction
# def awaiting_transaction_broadcast():
#     while True:
#         trans_result = transaction_subscriber.recv_json()
#         transaction = json.loads(trans_result)
#         if 'signature' in transaction:
#             # Add the Transaction to the pool
#             string_signature = transaction['signature']
#             signature = eval(string_signature)

#             transaction.pop('signature')
#             string_transaction = json.dumps(
#                 transaction, sort_keys=True).encode()

#             key1, key2 = keys.get_public_keys_from_sig(
#                 signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

#             blockchain.add_transaction(
#                 key1, transaction, signature, transaction['transaction_id'], mysql)
#             print('Just received transaction broadcast {}: and added it to transaction pool'.format(
#                 transaction))


# def awaiting_chain_broadcast():
#     while True:
#         chain_result = chain_subscriber.recv_json()
#         new_chain = json.loads(chain_result)
#         print('We just received a new chain \n {}'.format(new_chain))

#         if not 'signature' in new_chain:
#             # Get our chain from the database
#             cur = mysql.connection.cursor()
#             result = cur.execute("SELECT * FROM blockchain_chain")
#             chain = cur.fetchall()

#             if chain == []:
#                 # The chain table is empty ..... save this chain to our database
#                 for new_block in new_chain:
#                     block = new_block['block']
#                     nonce = new_block['nonce']
#                     hash = new_block['hash']
#                     prev_hash = new_block['prev_hash']
#                     timestamp = new_block['timestamp']
#                     data = new_block['data']

#                     cur.execute("INSERT INTO blockchain_chain(block, nonce, hash, prev_hash, timestamp, data) VALUES(%s, %s, %s, %s, %s, %s)", (
#                         block, nonce, hash, prev_hash, timestamp, data))
#                 mysql.connection.commit()
#                 cur.close()
#                 pass
#             else:
#                 cur.close()

#                 if len(new_chain) > len(chain):
#                     # We already have a chain table in our database saved - we just need to confirm chain is valid
#                     if blockchain.is_chain_valid(new_chain, mysql):

#                         # The received chain is valid - genesis blocks match and all block hashes and nonces also match
#                         new_transactions = new_chain[len(new_chain)-1]['data']
#                         verified_transactions = []

#                         for transaction in new_transactions:
#                             id = transaction['id']
#                             data = json.loads(transaction['transaction'])
#                             signature_string = transaction['signature']

#                             string_transaction = json.dumps(
#                                 data, sort_keys=True).encode()

#                             signature = eval(signature_string)

#                             public, key2 = keys.get_public_keys_from_sig(
#                                 signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

#                             is_transaction_valid = ecdsa.verify(
#                                 signature, string_transaction, public, curve.secp256k1, ecdsa.sha256)
#                             if is_transaction_valid:
#                                 verified_transactions.append(data)
#                                 print('Valid Transaction -> {}'.format(data))
#                             else:
#                                 print('The following transaction is not valid, cannot accept this new chain: {}'.format(
#                                     transaction))
#                                 pass

#                         # Replace our chain with new chain - if chain is valid and all transactions in the last block are also valid
#                         cur = mysql.connection.cursor()

#                         # Start by deleting the current chain from database
#                         cur.execute("DELETE from blockchain_chain")
#                         mysql.connection.commit()
#                         # We also need to delete everything from the transaction table - because the transactions have been mined in this block.
#                         cur.execute("DELETE from blockchain_transactions")
#                         mysql.connection.commit()

#                         # then save new blockchain in to our database
#                         for new_block in new_chain:
#                             block = new_block['block']
#                             nonce = new_block['nonce']
#                             hash = new_block['hash']
#                             prev_hash = new_block['prev_hash']
#                             timestamp = new_block['timestamp']
#                             data = new_block['data']

#                             cur.execute("INSERT INTO blockchain_chain(block, nonce, hash, prev_hash, timestamp, data) VALUES(%s, %s, %s, %s, %s, %s)", (
#                                 block, nonce, hash, prev_hash, timestamp, data))
#                         mysql.connection.commit()
#                         cur.close()

#                     else:
#                         # Received chain is not valid
#                         print('Received chain is not valid --> DISCARD')
#                         pass

#                 else:
#                     print(
#                         'Received chain is shorter than or equal to the chain we already have -- > DISCARD')
#                     pass

#         else:
#             # This is a transaction - transaction function will handle . . . .
#             pass


# if __name__ == '__main__':

#     # If you were not the Alpha node
#     # t1 = threading.Thread(target=createBlockchainConnection, daemon=True)

#     t1 = threading.Thread(target=initialiseAlphaNode, daemon=True)
#     t2 = threading.Thread(target=awaiting_transaction_broadcast, daemon=True)
#     t3 = threading.Thread(target=awaiting_chain_broadcast, daemon=True)

#     t1.start()
#     t2.start()
#     t3.start()

#     app.run(host='0.0.0.0', port='8888', debug=True)
