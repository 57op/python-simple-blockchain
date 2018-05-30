from wallet import Wallet 
import binascii

alice = Wallet('test_wallets/alice')
bob = Wallet('test_wallets/bob')

print('#' * 50)
print('Alice')
print('Address: %s' % alice.address())
print('Public key: %s' % binascii.hexlify(alice.pubkey()))
print('Balance: %f' % alice.balance())
print('#' * 50)
print('Bob')
print('Address: %s' % bob.address())
print('Public key: %s' % binascii.hexlify(bob.pubkey()))
print('Balance: %f' % bob.balance())
print('#' * 50)

from transaction import Transaction, TransactionInput, TransactionOutput
from block import Block
from dao import TransactionDAO

coinbase = TransactionDAO.read_by_hash('2c3a24c14f3a2a017ee2591d4402b42443c96152a532713a11e1124dbabccc00')

'''
t = Transaction()
# alice has an output in coinbase transaction, at index 0,
# so she provides the signatures and public key to unlock that output
t.addInput(TransactionInput(coinbase.checksum(), 0, alice.sign(coinbase.checksum()), alice.pubkey()))
t.addOutput(TransactionOutput(10, bob.address()))
t.addOutput(TransactionOutput(15, alice.address()))

print(binascii.hexlify(t.checksum()))
print(t.verify())

'''

# the first coinbase transaction (from genesis block)
coinbase = TransactionDAO.read_by_hash('2c3a24c14f3a2a017ee2591d4402b42443c96152a532713a11e1124dbabccc00')

# let Alice send some value to Bob
t = Transaction()
# alice has an output in coinbase transaction, at index 0,
# so she provides the signatures and public key to unlock that output
t.addInput(TransactionInput(coinbase.checksum(), 0, alice.sign(coinbase.checksum()), alice.pubkey()))
t.addOutput(TransactionOutput(10, bob.address()))
t.addOutput(TransactionOutput(15, alice.address()))
#t = TransactionDAO.read_by_hash('985777eac46108b05259e54037efd996b6c052562f61ddc85acd9698763b499b')


# send the transaction to the daemon
import socket
import sys

HOST, PORT = 'localhost', 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	st = t.serialize().encode()
	
	sock.connect((HOST, PORT))
	sock.sendall(len(st).to_bytes(4, byteorder='big'))	
	sock.sendall(t.serialize().encode())
finally:
	sock.close()
#'''