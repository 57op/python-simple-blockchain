import os
import json
from binascii import hexlify, unhexlify
from glob import glob
import transaction as t
import block as b

class BasicDAO:
	def __init__(self, fs_dir):
		self.root = fs_dir
		os.makedirs(fs_dir, exist_ok=True)
		
	def read(self, subpath):
		res = None
		
		with open(os.path.join(self.root, subpath), 'r') as fh:
			res = fh.read()
			
		return res
		
	def write(self, subpath, content):
		with open(os.path.join(self.root, subpath), 'w') as fh:
			fh.write(content)
	

class TransactionDAO(BasicDAO):
	def read_by_hash(self, hash):
		serialized_transaction = self.read(hash)
		return self.deserialize(serialized_transaction)
		
	def deserialize(self, serialized_transaction):
		deserialized_transaction = json.loads(serialized_transaction)
		transaction = t.Transaction()
		
		transaction.uuid = unhexlify(deserialized_transaction['uuid'])
		
		for input in deserialized_transaction['vin']:
			transaction.addInput(t.TransactionInput(unhexlify(input['tx']), input['vout'], unhexlify(input['signature']), unhexlify(input['pubkey'])))
			
		for output in deserialized_transaction['vout']:
			transaction.addOutput(t.TransactionOutput(output['value'], output['address'].encode()))
			
		return transaction
		
	def store(self, transaction):
		'''old_name = hexlify(transaction.checksum()).decode()
		name = old_name
		id = 1
		
		while os.path.isfile(os.path.join(self.root, name)):
			name = '%s_%d' % (old_name, id)
			id += 1
		
		self.write(name, transaction.serialize() )
		'''
		self.write(hexlify(transaction.checksum()).decode(), transaction.serialize() )
		
	def get_transactions_for(self, pubkey, address):
		transaction_names = glob(os.path.join(self.root, '*'))
		
		for n in transaction_names:
			t = self.read_by_hash(os.path.basename(n))
			keep = False
			
			for input in t.inputs:
				if input.pubkey == pubkey:
					keep = True
					break
			
			if keep:
				yield t
				continue
			
			keep = False
			
			for output in t.outputs:
				if output.address == address:
					keep = True
					break
					
			if keep:
				yield t
		
class BlockDAO(BasicDAO):
	# todo read_by_hash

	def store(self, block):
		self.write( hexlify(block.checksum()).decode(), block.serialize() )
		
	def get_last_hash(self):
		blocks = glob(os.path.join(self.root, '*'))
		blocks.sort(key=os.path.getmtime)
		
		return unhexlify(os.path.basename(blocks[-1]))
	
DB_DIR = 'db'
TRANSACTIONS_DIR = os.path.join(DB_DIR, 'transactions')
BLOCKS_DIR = os.path.join(DB_DIR, 'blocks')

TransactionDAO = TransactionDAO(TRANSACTIONS_DIR)
BlockDAO = BlockDAO(BLOCKS_DIR)

'''
import wallet

w = Wallet('test_wallets/alice')
# here create the genesis block
coinbase = t.Transaction()
coinbase.addOutput(t.TransactionOutput(25, w.address()))
coinbase.checksum()

genesis = b.Block(b'\x00' * 32, [coinbase.checksum()])
nonce, hash = genesis.pow()

print(nonce, hexlify(hash).decode())
TransactionDAO.store(coinbase)
BlockDAO.store(genesis)
'''