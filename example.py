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


print(alice.balance())

exit()

from transaction import Transaction, TransactionInput, TransactionOutput
from block import Block
from dao import TransactionDAO

# the first coinbase transaction (from genesis block)
coinbase = TransactionDAO.read_by_hash('093c101a53e43e25893f04631e70ea86a64628ba982e85bf59d8ebe3be38fd0f')

# let Alice send some value to Bob
#t = Transaction()
#t.addInput(TransactionInput(coinbase.checksum(), 0, alice.sign(coinbase.checksum()), alice.pubkey()))
#t.addOutput(TransactionOutput(10, bob.address()))
#t.addOutput(TransactionOutput(15, alice.address()))
t = TransactionDAO.read_by_hash('985777eac46108b05259e54037efd996b6c052562f61ddc85acd9698763b499b')


# send the transaction to the daemon
import socket
import sys

HOST, PORT = 'localhost', 9999

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	st = t.serialize().encode()
	
	sock.connect((HOST, PORT))
	sock.send(len(st).to_bytes(4, byteorder='big'))	
	sock.sendall(t.serialize().encode())
finally:
	sock.close()
