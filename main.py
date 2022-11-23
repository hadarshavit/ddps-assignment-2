import openml
import socket
import os
from multiprocessing import Queue
from threading import Thread, Event


class ServerConnection(Thread):
    def __init__(self) -> None:
        super().__init__()
        self.queue = Queue()
        self.stop = Event()
        self.server_id = None

    def run(self, connection):
        connection.send(str.encode('Server is working:'))
        while True:
            data = connection.recv(2048)
            response = 'Server message: ' + data.decode('utf-8')
            if not data:
                break
            connection.sendall(str.encode(response))
        connection.close()

    
    


#https://realpython.com/python-sockets/#multi-connection-client-and-server

class DistributedHPO:
    def __init__(self, node_id, nodes_order,dataset_id) -> None:
        self.dataset = openml.datasets.get_dataset(dataset_id)
        self.node_id = node_id
        self.nodes_order = nodes_order
        self.server_threads = []
    
    def start_socket(self):
        self.server_socket = socket.socket()
        host = '127.0.0.1'
        port = 2004
        ThreadCount = 0
        try:
            self.server_socket.bind((host, port))
        except socket.error as e:
            print(str(e))
        self.server_socket.listen(5)
        while True:
            Client, address = self.server_socket.accept()
            print('Connected to: ' + address[0] + ':' + str(address[1]))
            start_new_thread(multi_threaded_client, (Client, self))
            ThreadCount += 1
            print('Thread Number: ' + str(ThreadCount))
        self.server_socket.close()

    

