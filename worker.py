import argparse
import socket
import threading
from multiprocessing import Process, Queue, Event
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
import sklearn.datasets, sklearn.model_selection, sklearn.metrics
import sys
import pickle
from concurrent.futures import ProcessPoolExecutor
from utils import RunResults, Configuration, MasterInitialMessage, RunInstruction
import logging
from argparse import ArgumentParser
import random
import time


class Trainer(Process):
    def __init__(self, worker, process_id):
        super().__init__()
        self.worker: Worker = worker
        self.task = None
        self.process_id = process_id
        
        self.queue = Queue()
        self.stop = Event()

    def run(self):
        if self.worker.task == 'lfw_people':
            taskX, tasky = sklearn.datasets.fetch_lfw_people(data_home='~/scratch/data', return_X_y=True)
            self.X_train, self.X_test, self.y_train, self.y_test = \
                sklearn.model_selection.train_test_split(taskX, tasky, test_size=0.2)
        elif self.worker.task == 'digits':
            taskX, tasky = sklearn.datasets.load_digits(return_X_y=True)
            self.X_train, self.X_test, self.y_train, self.y_test = \
                sklearn.model_selection.train_test_split(taskX, tasky, test_size=0.2)
        else:
            raise ValueError(self.task)
        logging.info(f'Trainer {self.process_id} is ready')
        while not self.stop.is_set():

            try:
                configuration: Configuration = self.queue.get(timeout=10)
                logging.debug(f'Worker {self.worker.worker_id} Trainer {self.process_id} received configuration {configuration}')
            except:
                continue
            start = time.time()
            if configuration.algorithm == 'rf':
                model = RandomForestClassifier(n_estimators=configuration.rf_config.n_estimators,
                                               max_features=configuration.rf_config.max_features,
                                               max_depth=configuration.rf_config.max_depth,
                                               min_samples_split=configuration.rf_config.min_samples_split,
                                               min_samples_leaf=configuration.rf_config.min_samples_leaf,
                                               bootstrap=configuration.rf_config.bootstrap,
                                               n_jobs=-1)
                model.fit(self.X_train, self.y_train)
                pred_y = model.predict(self.X_test)
                acc = sklearn.metrics.accuracy_score(self.y_test, pred_y)
            else:
                raise ValueError(configuration.algorithm)
            runtime = time.time() - start

            result = RunResults(configuration=configuration, value=acc, worker_id=self.worker.worker_id,
                                process_id=self.process_id, first_configuration=False, running_time=runtime)
            self.worker.sock.sendall(pickle.dumps(result))


class Worker(threading.Thread):
    def __init__(self, host, port, num_processes):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.worker_id: int = -1
        self.task = None

        self.trainers = [Trainer(self, p_id) for p_id in range(num_processes)]

    def start_worker(self):
        self.sock.connect((self.host, self.port))
        data = self.sock.recv(1024)
        data: MasterInitialMessage = pickle.loads(data)

        assert isinstance(data, MasterInitialMessage)
        logging.info(f'Worker initial: {data}')
        self.worker_id = data.worker_id
        self.task = data.task_name

        for trainer in self.trainers:
            result: RunResults = RunResults(None, None, self.worker_id, trainer.process_id, True, None)
            trainer.start()
            logging.debug(f'Sending first configuration request worker: {self.worker_id} process: {trainer.process_id}')
            self.sock.sendall(pickle.dumps(result))

        self.start()

    def run(self):
        logging.info('Worker main thread is ready')
        while True:
            try:
                data = self.sock.recv(2048)
                data: RunInstruction = pickle.loads(data)
                # logging.debug('Worker {s')

                assert isinstance(data, RunInstruction)
                assert data.worker_id == self.worker_id

                for trainer in self.trainers:
                    if trainer.process_id == data.process_id:
                        trainer.queue.put(data.configuration)
            except:
                logging.error('Socket disconnected, attempting reconnection')
                self.sock.connect()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    parser = ArgumentParser()
    parser.add_argument('--master-hostname', type=str)
    parser.add_argument('--master-port', type=int)
    parser.add_argument('--num-processes', type=int)

    args = parser.parse_args()

    worker = Worker(args.master_hostname, args.master_port, args.num_processes)
    worker.start_worker()
