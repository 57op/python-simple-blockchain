'''
this is a server listening for transactions.
when someon broadcast a transactions here, the daemon will verify it
if it's valid it will store it in its transaction pool.
and it will keep mining of course!
'''

from socketserver import TCPServer, BaseRequestHandler
from dao import TransactionDAO, BlockDAO
import threading
import queue
import block as b
import transaction
import wallet
import time
from binascii import hexlify

tx_pool = queue.Queue()

def miner(tx_pool, block_hash):
	time.sleep(8)
	
	# let Alice win the rewards
	w = wallet.Wallet('test_wallets/alice')

	while True:
		# this coinbase transaction will have always the same hash
		# it's not a big deal, but we have to keep track how many they are
		# otherwise we will only able to spend it once
		coinbase = transaction.Transaction()
		coinbase.addOutput(transaction.TransactionOutput(25, w.address()))
		TransactionDAO.store(coinbase)
		
		transactions = [coinbase.checksum()]
	
		while not tx_pool.empty():
			t = tx_pool.get()
			
			if t.verify():
				transactions.append(t.checksum())
				TransactionDAO.store(t)
			else:
				print('Ignoring non valid transaction: %s' % hexlify(t.checksum()).decode())
				
		# build the block
		block = b.Block(block_hash, transactions)
		block.pow()
		BlockDAO.store(block)
		
		block_hash = block.checksum()
		
		print('Mined a new block, including the following transactions')
		
		for i, t in enumerate(block.transactions):
			print('[%s] %s' % ('coinbase' if i == 0 else '', hexlify(t).decode()))
		
		time.sleep(8)

class RequestHandler(BaseRequestHandler):
	def handle(self):
		bytes_to_read = int.from_bytes(self.request.recv(4), byteorder='big')
		data = self.request.recv(bytes_to_read)
		
		assert len(data) == bytes_to_read, 'Expected %d bytes' % bytes_to_read
		
		t = TransactionDAO.deserialize(data.decode())
		#print(t.serialize())
		#print(t.verify())
		
		print('Received a new transaction %s' % hexlify(t.checksum()).decode())
		
		tx_pool.put(t)
		
		'''
		# self.request is the TCP socket connected to the client
		self.data = self.request.recv(1024).strip()
		print("{} wrote:".format(self.client_address[0]))
		print(self.data)
		# just send back the same data, but upper-cased
		self.request.sendall(self.data.upper())
		'''
		
if __name__ == '__main__':
	HOST, PORT = 'localhost', 9999

	block_hash = BlockDAO.get_last_hash()
	
	# Create the server, binding to localhost on port 9999
	server = TCPServer((HOST, PORT), RequestHandler)
	
	threading.Thread(target=miner, args=(tx_pool, block_hash)).start()
	
	# start another thread that keeps mining!

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()