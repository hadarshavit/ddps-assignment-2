import socket
import threading
from argparse import ArgumentParser
from hyperparameter_optimization import HyperparameterOptimization
from dataclasses import dataclass
from multiprocessing import Queue
from utils import RunResults, Configuration, RunInstruction, MasterInitialMessage
from typing import List
import pickle
import logging
from argparse import ArgumentParser


class Client(threading.Thread):
    def __init__(self, socket, address, id, master):
        threading.Thread.__init__(self)
        self.socket: socket.socket = socket
        self.address = address
        self.id = id
        self.master: Master = master
        self.awaiting_configurations = []

        # self.socket.settimeout(1)

    def __str__(self):
        return str(self.id) + " " + str(self.address)

    def run(self):
        self.socket.sendall(MasterInitialMessage(self.id))
        while True:
            try:
                data = self.socket.recv(1024)
                self.master.finish_run(data)
            except:
                print("Client " + str(self.address) + " has disconnected")
                self.signal = False
                self.master.connections.remove(self)
                break
            # if data != "":
            #     print("ID " + str(self.id) + ": " + str(data.decode("utf-8")))
            #     for client in connections:
            #         if client.id != self.id:
            #             client.socket.sendall(data)

    def send(self, configuration: Configuration, process_id):
        run_instruction = RunInstruction(configuration, worker_id=self.id, process_id=process_id)
        try:
            data_string = pickle.dumps(run_instruction)
            self.socket.sendall(data_string)
        except:
            self.master.configs_queue.append(configuration)


class Master:

    def __init__(self, host, port):
        self.connections: List[Client] = []
        self.total_connections = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        self.hpo_manager = HyperparameterOptimization()

        self.configs_queue: List = []
        self.best_configuration = None
        self.best_loss = None
        self.results_queue = Queue()

    def start(self):
        threading.Thread(target=self.newConnections).start()
        self.start()

    def newConnections(self):
        while True:
            sock, address = self.socket.accept()
            self.connections.append(Client(sock, address, self.total_connections,  self))
            self.connections[len(self.connections) - 1].start()
            logging.info("New connection at ID " + str(self.connections[len(self.connections) - 1]))
            self.total_connections += 1

    def get_connection(self, id):
        for conn in self.connections:
            if conn.id == id:
                return conn
        return None

    def run(self):
        while True:
            result: RunResults = self.queue.get()
            if not result.first_configuration:
                self.history.append(result)

            if self.configs_queue.empty():
                next_configuration = self.hpo_manager.get_next_configuration(result)
            else:
                next_configuration = self.configs_queue.pop()

            conn = self.get_connection(result.worker_id)
            if conn:
                conn.send(next_configuration)
            else:
                logging.error(f'Connection {result.worker_id} not existing, adding config to queue')

    def finish_run(self, data):
        self.hpo_manager.queue.put(data)



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=int)
    args = parser.parse_args()

    Master(args.host, args.port).start()

