#Module 2- Creating Cryptocurrency

#requests==2.18.4:

import datetime
import hashlib 
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse 


# Part-1 Building the Blockchain
class BlockChain:
    def __init__(self):
        self.chain = []
        self.transactions = []  #mempool
        self.create_block(proof = 1, previous_hash = '0' )
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain)+1, 'timestamp': str(datetime.datetime.now()), 'proof': proof, 'previous_hash': previous_hash, 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self,previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()      

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index<len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()    
            if hash_operation[:4]!='0000':
                return False
            previous_block = block    
            block_index +=1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender, 'receiver':receiver, 'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address_of_node):
        parsed_url = urlparse(address_of_node)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get-chain')
            if response.status_code == 200:
                new_length = response.json()['length']
                chain = response.json()['chain']
                if new_length > max_length and self.is_chain_valid(chain):
                    max_length = new_length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False                

# Part-2 Mining our Blockchain

#creating a web app
app=Flask(__name__)

#Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-','')

#creating a blockchain
blockchain = BlockChain()

#mining a new block
@app.route('/mine-block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver= 'Sangeeta', amount=1)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Congratulations, you just mined a block on my customized blockchain!',
        'index' : block['index'],
        'timestamp' : block['timestamp'],
        'proof' : block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200

#get the full blockchain
@app.route('/get-chain',methods=['GET'])
def get_chain():
    response = {
        'chain' : blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

#check if the chain is valid
@app.route('/is-valid',methods=['GET'])
def is_valid_blockchain():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {
            'message' : 'Blockchain is valid. Good to go! '
        }
    else :
        response = {
            'message': 'Invalid Blockchain. Alert !!!'
        }    
    return jsonify(response), 200

#add new transaction to blockchain
@app.route('/add-transaction',methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of transaction are missing!', 400
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {'message': f'This Transaction will be added to Block {index}'}
    return jsonify(response), 201

#part-3 Decentralizing the blockchain

#connecting new nodes
@app.route('/connect-node',methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': "All nodes are connected. The MOMO Blockchain now contains the following nodes:" ,'total_nodes': list(blockchain.nodes) }
    return jsonify(response),201

#replacing chain by longest chain if needed
@app.route('/replace-chain',methods=['GET'])
def replacing_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message' : 'The nodes had different chains so the chain was replaced by the longest one.',
            'new_chain': blockchain.chain
        }
    else :
        response = {
            'message': 'All good. The exisiting chain is the largest one',
            'actual_chain' : blockchain.chain
        }    
    return jsonify(response), 200

#run the app
app.run(host = '0.0.0.0', port = 5002)