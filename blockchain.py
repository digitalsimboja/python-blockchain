from datetime import datetime
import hashlib
import json
import threading
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from fastecdsa import curve, ecdsa, keys
from fastecdsa.keys import export_key, import_key, gen_keypair
import requests
from uuid import uuid4
import zmq


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce


class Blockchain:

    def create_genesis_block(self, mysql):
        genesis_time = datetime.now()

        block = {}
        block['index'] = 1
        block['prev_hash'] = '0000000000'
        block['nonce'] = 123
        block['data'] = 'This is the genesis block of skolo-online python blockchain'
        block['timestamp'] = genesis_time.strftime('%Y-%m-%d %H:%M:%S.%f')

        encode_block = json.dumps(block, sort_keys=True).encode()
        new_hash = hashlib.sha256(encode_block).hexdigest()
        block['hash'] = new_hash

        # Persist the genesis block to the blockchain
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO blockchain_chain(block, nonce, hash, prev_hash, timestamp, data) VALUES(%s, %s, %s, %s, %s, %s)",
                    (block['index'], block['nonce'], block['hash'], block['prev_hash'], block['timestamp'], block['data']))

        mysql.connection.commit()

        cur.close()

        return block

    def add_transaction(self, pub_key, new_transaction, signature, transaction_id, mysql):
        # Confirm the transaction does not exist in the transaction pool before adding the new transaction
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM blockchain_transactions")
        transactions = cur.fetchall()

        if result > 0:
            for trx in transactions:
                trxn = json.loads(trx['transaction'])
                if trxn['transaction_id'] == new_transaction['transaction_id']:
                    print('transaction {} already exits in the pool'.format(trxn))
                    return

        # Transaction does not exist so add to Database
        transaction_string = json.dumps(
            new_transaction, sort_keys=True).encode()
        transaction_signature = json.dumps(signature)
        cur.execute("INSERT INTO blockchain_transactions(pub_key, signature, transaction_id, transaction) VALUES(%s, %s, %s, %s)",
                    (pub_key, transaction_signature, transaction_id, transaction_string))
        mysql.connection.commit()

        cur.execute("SELECT * FROM blockchain_chain")
        chain = cur.fetchall()

        cur.close()

        return len(chain) + 1

    def mine(self, transactions, mysql):
        """
        Mines a new block and adds to the blockchain
        """

        t_time = datetime.now()
        previous_hash = ""
        cur = mysql.connection.cursor()

        block = {}
        block['nonce'] = 123
        block['data'] = transactions
        block['timestamp'] = t_time.strftime('%Y-%m-%d %H:%M:%S.%f')

        result = cur.execute("SELECT * FROM blockchain_chain")
        chain = cur.fetchall
        current_index = len(chain) + 1
        if result > 0:
            chain_length = len(chain)
            cur.execute(
                'SELECT * FROM blockchain_chain WHERE block=%s', [chain_length])
            last_block = cur.fetchone()
            previous_hash = last_block['hash']

        block['index'] = current_index
        block['prev_hash'] = previous_hash

        mining = False
        while mining is False:
            encode_block = json.dumps(block, sort_keys=True).encode()
            new_hash = hashlib.sha256(encode_block).hexdigest()

            if new_hash[:5] == '00009':
                mining = True
            else:
                block['nonce'] += 1

                encoded_block = json.dumps(block, sort_keys=True).encode()
                new_hash = hashlib.sha256(encoded_block).hexdigest()

        block['hash'] = new_hash

        # New block is mined, persist it to the chain
        cur.execute("INSERT INTO blockchain_chain(block, nonce, hash, prev_hash, timestamp, data) VALUES(%s, %s, %s, %s, %s, %s)",
                    (block['index'], block['nonce'], block['hash'], block['prev_hash'], block['timestamp'], json.dumps(block['data'])))

        mysql.connection.commit()

        cur.close()

        return block

    def check_valid_transactions(self, mysql):
        """
        A function that check is all transactions are valid
        """
        verified_transactions = []

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM blockchain_transactions")
        transactions = cur.fetchall()

        if result > 0:
            for trx in transactions:
                trx_id = trx['id']
                data = json.loads(trx['transaction'])
                sig = trx['signature']
                string_transaction = json.dumps(data, sort_keys=True).encode()

                signature = eval(sig)

                pub, key2 = keys.get_public_keys_from_sig(signature, string_transaction, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

                is_valid = ecdsa.verify(signature, string_transaction, pub, curve.secp256k1, ecdsa.sha256)

                if is_valid:
                    verified_transactions.append(data)
        
        cur.close()
        return verified_transactions