from typing import List
import requests
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastecdsa import curve, ecdsa, keys, point
from fastecdsa.keys import export_key, import_key, gen_keypair
import json
import os
import time
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import models, schemas, blockchain, wallet

from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
session = requests.Session()
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

url = "http://127.0.0.1:8000"

# Dependency
chain = blockchain.Blockchain()
account = wallet.Wallet()
account.generate_key_pair()

# Construct a transaction


def send_transaction():
    receiver_priv_key = account.generate_private_key()
    receiver_pub_key = account.generate_public_key(receiver_priv_key)

    data = "Buy me a coffee"
    priv_key, pub_key = import_key(
        os.path.join("blockchain/keys/secp256k1.key"))

    transaction = account.create_transaction(data)
    trans_result = transaction

    string_transaction = json.dumps(transaction, sort_keys=True).encode()
    signature = ecdsa.sign(string_transaction, priv_key,
                           curve=curve.secp256k1, hashfunc=ecdsa.sha256)
    transaction['signature'] = json.dumps(signature)
    to_send = json.dumps(transaction, sort_keys=True)

    verified = account.validate_transaction(to_send)

    if verified:

        trx = requests.post(
            f"{url}/new-transaction", trans_result)
        print('Just received transaction broadcast {}: and added it to transaction pool'.format(
            trx))
    else:
        print("You have sent an inbalid transaction")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return account.generate_key_pair()


@app.post("/create-genesis-block", response_model=schemas.Block)
async def create_genesis_block(db: Session = Depends(get_db)):
    genesis_block = chain.create_genesis_block(db)

    return genesis_block

# endpoint to submit a new transaction. This will be used by
# our application to add new data  to the blockchain
@app.post('/new-transaction', response_model=schemas.Transaction)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = chain.get_transaction_by_id(
        db, transaction_id=transaction.transaction_id)
    if db_transaction:
        raise HTTPException(
            status_code=400, detail="Transaction already exists")

    trx = chain.create_transaction(db=db, transaction=transaction)

    return trx


@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = chain.get_transaction_by_id(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction


@app.get("/check-transactions", response_model=schemas.Transaction)
def get_valid_transactions(db: Session = Depends(get_db)):
    valid_transactions = blockchain.check_valid_transactions(db=db)

    return valid_transactions

def initialiseAlphaNode():
    # Start by Creating the Genesis Block
    session.post(f"{url}/create-genesis-block")
 
    while True:
        send_transaction()
        # wait for 1 minute before checking again
        time.sleep(60)


t1 = threading.Thread(target=initialiseAlphaNode, daemon=True)

t1.start()
