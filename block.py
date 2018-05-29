import hashlib
import json
from binascii import hexlify, unhexlify

class Block:
	def __init__(self, previous_block, transactions, hash=None, nonce=0):
		self.previous_block = previous_block
		self.transactions = transactions
		self.hash = hash
		self.nonce = nonce
		
	def pow(self):
		data = '%s' % hexlify(self.previous_block).decode()
		
		for t in map(lambda t: hexlify(t).decode(), self.transactions):
			data += t
	
		nonce = 0
		
		while True:
			sha256 = hashlib.new('sha256')
			sha256.update(('%s%d' % (data, nonce)).encode())
			hash = sha256.digest()
			
			if (hash[0] & 0xFF) == 0x00 and (hash[1] & 0xF0) == 0x00:
				break
			
			nonce += 1
		
		self.hash = hash
		self.nonce = nonce
		
		return nonce, hash
		
	def checksum(self):
		assert self.hash != None, 'cannot return checksum, you need to compute the PoW'
		return self.hash
		
		
	def serialize(self):
		d = {
			'previous_block': hexlify(self.previous_block).decode(),
			'checksum': hexlify(self.hash).decode(),
			'nonce': self.nonce,
			'transactions': [hexlify(t).decode() for t in self.transactions]
		}

		return json.dumps(d, indent=4)
		