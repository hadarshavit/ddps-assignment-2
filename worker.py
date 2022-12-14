import argparse
import socket
import threading
from multiprocessing import Process, Queue, Event
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
import sys
import pickle
from concurrent.futures import ProcessPoolExecutor
from utils import RunResults, Configuration, MasterInitialMessage, RunInstruction
import logging
from argparse import ArgumentParser


class Trainer(Process):
    def __init__(self, worker, process_id):
        self.worker: Worker = worker
        self.process_id = process_id
        self.queue = Queue()
        self.stop = Event()

    def run(self):
        while not self.stop.is_set():
            try:
                configuration: Configuration = self.queue.get(timeout=10)
            except:
                continue

            if configuration['algorithm'] == 'rf':
                model = RandomForestClassifier(n_estimators=configuration['rf_n_estimators'],
                                               criterion=configuration['rf_criterion'],
                                               min_samples_split=configuration['rf_min_samples_split'],
                                               min_samples_leaf=configuration['rf_min_samples_leaf'],
                                               min_weight_fraction_leaf=configuration['rf_min_weight_fraction_leaf'],
                                               max_features=configuration['max_features'],
                                               bootstrap=configuration['bootstrap'],
                                               oob_score=configuration['oob_score'])
            result = RunResults(configuration=configuration, value=1, worker_id=self.worker_id,
                                process_id=self.process_id, first_configuration=False)


class Worker(threading.Thread):
    def __init__(self, host, port, num_processes):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.worker_id: int = -1

        self.trainers = [Trainer(self, p_id) for p_id in range(num_processes)]

    def start_worker(self):
        self.sock.connect((self.host, self.port))
        data = self.sock.recv(1024)
        data: MasterInitialMessage = pickle.loads(data)

        assert isinstance(data, MasterInitialMessage)
        self.worker_id = data.worker_id

        for trainer in self.trainers:
            result: RunResults = RunResults(None, None, self.worker_id, trainer.process_id, True)
            trainer.start()
            logging.debug(f'Sending first configuration request worker: {self.worker_id} process: {trainer.process_id}')
            self.sock.sendall(result)

        self.start()

    def run(self):
        while True:
            try:
                data = self.sock.recv(1024)
                data: RunInstruction = pickle.loads(data)

                assert isinstance(data, RunInstruction)
                assert data.worker_id == self.worker_id

                for trainer in self.trainers:
                    if trainer.process_id == data.process_id:
                        trainer.queue.put(data.configuration)
            except:
                logging.error('Socket disconnected, attempting reconnection')
                self.sock.connect()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--master-hostname', type=str)
    parser.add_argument('--master-port', type=int)
    parser.add_argument('--num-processes', type=int)

    args = parser.parse_args()

    worker = Worker(args.master_hostname, args.master_port, args.num_processes)
    worker.start_worker()
