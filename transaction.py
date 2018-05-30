'''

// tx input = { pointer to UTX0, output index, unlocking script }
// tx output = { value, locking script / cryptographic puzzle }

// unlocking script contains a signature and the public key (not base58 encoded)
// <signature> <public key>

// locking script contains the receiver public key (again not base58 encoded)
// which will be compared with the one in unlocking script and at last will check if the signature is valid

'''

import math
import hashlib
import base58
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import dao
from util import sqrt

import binascii
import json
import uuid

class TransactionInput:
	# utxo is the hash
	def __init__(self, utxo, vout, signature, pubkey):
		self.utxo = utxo
		self.vout = vout
		# for unlocking
		self.signature = signature
		self.pubkey = pubkey
		
	def serialize(self):
		return {
			'tx': binascii.hexlify(self.utxo).decode(),
			'vout': self.vout,
			'signature': binascii.hexlify(self.signature).decode(),
			'pubkey': binascii.hexlify(self.pubkey).decode()
		}
		
class TransactionOutput:
	def __init__(self, value, address):
		self.value = value
		# for locking
		self.address = address
		
	def serialize(self):
		return {
			'value': self.value,
			'address': self.address.decode()
		}

class Transaction:
	def __init__(self):
		self.inputs = []
		self.outputs = []
		self._hash = None
		
	def addInput(self, input):
		self.inputs.append(input)
		
	def addOutput(self, output):
		self.outputs.append(output)
	
	def verify(self):
		hash = self.checksum()
		
		'''
		try:
			dao.TransactionDAO.read_by_hash(binascii.hexlify(hash).decode())
			# the transaction was already spent
			# this is not enough, we should also check if this transaction was already mined inside a block
			return False
		except:
			pass
		'''
		
		valid = False	
		# we need to scan the blockchain in order to understand
		# if this transaction was already included in a block
	
		# check if inputs can be spent!
		inputs_value = 0
		
		for input in self.inputs:
			# recover the utxo refered by the input
			# output = input.utxo.outputs[input.vout]
			utxo = dao.TransactionDAO.read_by_hash(binascii.hexlify(input.utxo).decode())
			output = utxo.outputs[input.vout]
			
			# how many time utxo was mined into a block?
			tx_utxo_count = len(list(dao.BlockDAO.tx_in_blocks(utxo.checksum())))
			tx_this_count = len(list(dao.BlockDAO.tx_in_blocks(hash)))
			
			# print('%s -> [count] %d, [unlock] %d' % (binascii.hexlify(utxo.checksum()).decode(), tx_utxo_count, tx_this_count))
			if (tx_utxo_count - tx_this_count) < 1:
				print('The UTXO [%s] cannot be spent anymore' % binascii.hexlify(utxo.checksum()).decode())
				break
			
			
			# input pubkey to address
			sha256 = hashlib.new('sha256')
			ripemd160 = hashlib.new('ripemd160')

			sha256.update(input.pubkey)
			ripemd160.update(sha256.digest())
			
			if output.address != base58.b58encode_check(b'\x00' + ripemd160.digest()):
				# print('You cannot unlock this output with this public key')
				break
			
			# the unlocking address is the same as the locking one				
			# now we have to check the signature
			# decompress the public key
			curve = SECP256k1.curve
			signY = input.pubkey[0] - 2
			x = int.from_bytes(input.pubkey[1:], byteorder='big')
			yy = (pow(x, 3, curve.p()) + curve.a() * x + curve.b()) % curve.p()
			
			try:
				y = sqrt(yy, curve.p())
			except:
				# invalid x probably
				break
			
			if y % 2 != signY:
				y = curve.p() - y
			
			key = x.to_bytes(32, byteorder='big') + y.to_bytes(32, byteorder='big')
			vk = VerifyingKey.from_string(key, SECP256k1)

			try:
				vk.verify(input.signature, utxo.checksum())
			except BadSignatureError:
				break
				
			inputs_value += output.value
		else:
			#print('Every input can be unlocked')
			valid = True
		
		# signature is valid
		if valid:
			outputs_value = 0
			
			for output in self.outputs:
				outputs_value += output.value
				
			# print(inputs_value, outputs_value)
			
			# ignore coinbase TXs for this check
			if len(self.inputs) > 0 and inputs_value < outputs_value:
				valid = False
		
		return valid
		
	def checksum(self):
		if not self._hash:
			sha256 = hashlib.new('sha256')
			sha256.update(self.serialize().encode())
			self._hash = sha256.digest()
			
		return self._hash
		
	def serialize(self):
		d = {
			'vin': [],
			'vout': []
		}
		
		for i in self.inputs:
			d['vin'].append(i.serialize())
			
		for i in self.outputs:
			d['vout'].append(i.serialize())
			
		return json.dumps(d, indent=4)