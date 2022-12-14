import socket
import threading
from argparse import ArgumentParser
from hyperparameter_optimization import HyperparameterOptimization, RandomSearch
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
        self.socket.sendall(pickle.dumps(MasterInitialMessage(self.id)))
        while True:
            try:
                data = self.socket.recv(1024)
                self.master.finish_run(pickle.loads(data))
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


class Master(threading.Thread):

    def __init__(self, host, port):
        super().__init__()
        self.connections: List[Client] = []
        self.total_connections = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        self.hpo_manager = RandomSearch()

        self.configs_queue: List = []
        self.best_configuration = None
        self.best_loss = None
        self.results_queue = Queue()

    def start(self):
        threading.Thread(target=self.newConnections).start()
        super().start()

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
        logging.info('Master is ready')
        while True:
            result: RunResults = self.results_queue.get()
            logging.debug(f'Master received results {result}')

            if len(self.configs_queue) == 0:
                logging.debug('Generating new configuration')
                next_configuration = self.hpo_manager.get_next_configuration(result)
            else:
                logging.debug('Taking configuration from queue')
                self.hpo_manager.register_result(result)
                next_configuration = self.configs_queue.pop()

            logging.debug(f'Master sends configuration {next_configuration}')
            conn = self.get_connection(result.worker_id)
            if conn:
                conn.send(next_configuration, result.process_id)
            else:
                logging.error(f'Connection {result.worker_id} not existing, adding config to queue')

    def finish_run(self, data):
        self.results_queue.put(data)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = ArgumentParser()
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=int)
    args = parser.parse_args()

    Master(args.host, args.port).start()

