from multiprocessing import Process, Queue, Value, Array
from socketserver import ThreadingTCPServer, BaseRequestHandler
import ctypes
import time

import wallet
import transaction as tx
import block as bk
import dao
import hashlib
from binascii import hexlify

def pow_process(q, block, stopped, nonce, hash):
	data = block.pow_data()
	sha256 = hashlib.new('sha256')
	
	while True:
		if not q.empty():
			stopped.value = 1
			break
	
		sha256.update(data + nonce.value.to_bytes(32, 'big'))
		hash[:] = sha256.digest()
		
		if block.is_hash_valid(hash[:]):
			break
			
		nonce.value += 1

def miner_process(q):
	print('[miner] working!')
	time.sleep(5)

	w = wallet.Wallet('test_wallets/alice')
	block_hash = dao.BlockDAO.get_last_hash()
	txs_to_keep = []

	while True:
		# always mine on a different address
		#w = wallet.Wallet.make_wallet()
		
		# store the private key, so that the value is not lost
		#w.save('test_wallets/%s' % w.address().decode())
		
		coinbase = tx.Transaction()
		coinbase.addOutput(tx.TransactionOutput(25, w.address()))
		# dao.TransactionDAO.store(coinbase)
		
		transactions = [coinbase]
		
		if len(txs_to_keep) > 0:
			print('Extending transactions with previous one')
			transactions.extend(txs_to_keep)
			txs_to_keep = []
		
		while not q.empty():			
			transactions.append(q.get_nowait())
		
		stopped = Value(ctypes.c_uint8, 0)
		hash = Array(ctypes.c_uint8, 32)
		nonce = Value(ctypes.c_uint32, 0)
		b = bk.Block(block_hash, [t.checksum() for t in transactions])
		
		pow = Process(target=pow_process, args=(q, b, stopped, nonce, hash))
		pow.start()
		pow.join()
		
		if stopped.value == 1:
			# store transactions except coinbase
			txs_to_keep = transactions[1:]
			
			print('[miner] stopped PoW because new transactions where found, restarting PoW on extended block')
		else:
			b.hash = bytes(hash[:])
			b.nonce = nonce.value
			
			print('[miner] block hash %s' % hexlify(b.checksum()).decode())
					
			for i, t in enumerate(b.transactions):
				print('[miner] [%s] %s' % ('coinbase' if i == 0 else '', hexlify(t).decode()))
				dao.TransactionDAO.store(transactions[i])
				
			dao.BlockDAO.store(b)
			block_hash = b.checksum()
			
		time.sleep(10)
			
		
class RequestHandler(BaseRequestHandler):
	def setup(self):
		# print(self.client_address)
		pass
		
	def handle(self):
		'''
		1. get 4 bytes, convert to int in bigendian
		2. get N bytes (the previous read), deserialize the transaction
		'''
		bytes_to_read = int.from_bytes(self.request.recv(4), byteorder='big')
		data = self.request.recv(bytes_to_read)
		
		assert len(data) == bytes_to_read, 'Expected %d bytes, got %d' % (bytes_to_read, len(data))
		
		t = dao.TransactionDAO.deserialize(data.decode())
		is_valid = t.verify()
		
		print('[node] received a new transaction %s, valid = %s' % (hexlify(t.checksum()).decode(), is_valid))
		
		if is_valid:		
			self.server.q.put_nowait(t)
			print(t.serialize())
		
if __name__ == '__main__':
	HOST, PORT = 'localhost', 9999

	q = Queue()
	
	# Create the server, binding to localhost on port 9999
	server = ThreadingTCPServer((HOST, PORT), RequestHandler)
	server.q = q
	miner = Process(target=miner_process, args=(q,))
	
	miner.start()
	
	print('[node] Server running on %s:%d' % server.server_address)
	
	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print('Stopping server')
		server.shutdown()
		server.server_close()		
		
		print('Stopping miner')
		miner.terminate()