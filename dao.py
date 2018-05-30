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
		
		# transaction.uuid = unhexlify(deserialized_transaction['uuid'])
		
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
		for n in glob(os.path.join(self.root, '*')):
			tx = self.read_by_hash(os.path.basename(n))
			keep = False
			
			for input in tx.inputs:
				if input.pubkey == pubkey:
					keep = True
					break
			
			if keep:
				yield tx
				continue
			
			keep = False
			
			for output in tx.outputs:
				if output.address == address:
					keep = True
					break
					
			if keep:
				yield tx
				
	def get_transactions_unlocks(self, tx_hash):
		u = 0
	
		for h in glob(os.path.join(self.root, '*')):
			h = os.path.basename(h)
			tx = self.read_by_hash(h)
			
			for input in tx.inputs:
				if input.utxo == tx_hash:
					u += 1
		
		return u
		
class BlockDAO(BasicDAO):
	def read_by_hash(self, hash):
		serialized_block = self.read(hash)
		return self.deserialize(serialized_block)
		
	def deserialize(self, serialized_block):
		deserialized_block = json.loads(serialized_block)
		
		return b.Block(
			unhexlify(deserialized_block['previous_block']),
			[unhexlify(tx) for tx in deserialized_block['transactions']],
			unhexlify(deserialized_block['checksum']),
			deserialized_block['nonce'])
	

	def store(self, block):
		self.write( hexlify(block.checksum()).decode(), block.serialize() )
		
	def get_last_hash(self):
		blocks = glob(os.path.join(self.root, '*'))
		blocks.sort(key=os.path.getmtime)
		
		return unhexlify(os.path.basename(blocks[-1]))
		
	def tx_in_blocks(self, tx_hash):
		for block_hash in glob(os.path.join(self.root, '*')):
			block_hash = os.path.basename(block_hash)
			block = self.read_by_hash(block_hash)
			
			for tx in block.transactions:
				if tx == tx_hash:
					yield block.checksum()
					break
	
DB_DIR = 'db'
TRANSACTIONS_DIR = os.path.join(DB_DIR, 'transactions')
BLOCKS_DIR = os.path.join(DB_DIR, 'blocks')

TransactionDAO = TransactionDAO(TRANSACTIONS_DIR)
BlockDAO = BlockDAO(BLOCKS_DIR)

'''
import wallet

w = wallet.Wallet('test_wallets/alice')
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