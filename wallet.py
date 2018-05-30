import hashlib
import base58
from ecdsa import SigningKey, SECP256k1
import dao
from binascii import hexlify

class Wallet:
	@staticmethod
	def make_wallet(seed=None):
		# signing key is the private key
		sk = SigningKey.generate(curve=SECP256k1)
		wif_compressed = base58.b58encode_check(b'\x80' + sk.to_string() + b'\x01')
		
		return Wallet(wif_compressed)
		
	def __init__(self, pathOrBytes):
		if isinstance(pathOrBytes, str):
			with open(pathOrBytes, 'rb') as fh:
				pathOrBytes = fh.read()
		
		# throws ValueError if invalid checksum
		wif = base58.b58decode_check(pathOrBytes)
		
		# we will only use compressed public keys
		if wif[0] != 0x80 or wif[-1] != 0x01:
			raise Exception('Wrong import format. Only WIF-compressed is allowed')
			
		self.private_key = SigningKey.from_string(wif[1:-1], curve=SECP256k1)
		self.public_key = self.private_key.get_verifying_key()
		
	def address(self, b58=True):
		# public address calculation: ripemd160(sha256(vk))
		sha256 = hashlib.new('sha256')
		ripemd160 = hashlib.new('ripemd160')

		sha256.update(self.pubkey())
		ripemd160.update(sha256.digest())
		
		addr = ripemd160.digest()
		
		if b58:
			addr = base58.b58encode_check(b'\x00' + addr)
			
		return addr
		
	def pubkey(self):
		# compressed public key
		key = self.public_key.to_string()
		#return (4).to_bytes(1, byteorder='big') + key
		
		x = key[:32]
		y = key[32:]

		sign = (2 + (y[-1] & 1)).to_bytes(1, byteorder='big')
		return sign + x
		
	def save(self, path):
		with open(path, 'wb') as fh:
			wif = base58.b58encode_check(b'\x80' + self.private_key.to_string() + b'\x01')
			fh.write(wif)
			
	def sign(self, message):
		return self.private_key.sign_deterministic(message)
		
	def verify(self, signature):
		return self.public_key.verify(signature)
		
	def balance(self):
		pubkey = self.pubkey()
		addr = self.address()
	
		balance = 0
		
		for t in dao.TransactionDAO.get_transactions_for(pubkey, addr):
			tx_count = len(list(dao.BlockDAO.tx_in_blocks(t.checksum())))
			
			print(hexlify(t.checksum()).decode(), tx_count)
		
			for _ in range(tx_count):
				for input in t.inputs:
					if input.pubkey == pubkey:
						i_tx = dao.TransactionDAO.read_by_hash(hexlify(input.utxo).decode())
						balance -= i_tx.outputs[input.vout].value
						#print('[input] -%d' % i_tx.outputs[input.vout].value)
				
				for output in t.outputs:
					if output.address == addr:
						balance += output.value
						#print('[output] +%d' % output.value)
		
		return balance
		
if __name__ == '__main__':
	import sys
	
	if len(sys.argv) < 2:
		print('Missing wallet name')
		exit(-1)
	
	wallet = Wallet.make_wallet()
	
	print('Wallet address is %s' % wallet.address())
	
	wallet.save(sys.argv[1])
