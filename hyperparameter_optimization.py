from multiprocessing import Queue
import threading
from abc import abstractmethod
from dataclasses import dataclass
import logging
import numpy as np
import random
import time
from utils import Configuration, RFConfiguration


class HyperparameterOptimization:
    def __init__(self):
        self.history = []
        self.best_loss = None
        logging.debug(f'Best loss {self.best_loss}')

    @abstractmethod
    def _inner_get_next_configuration(self, result):
        pass

    def get_next_configuration(self, result):
        if not result.first_configuration:
            self.history.append((result, time.time()))
            if self.best_loss is not None and result.value < self.best_loss:
                self.best_loss = result.value
                self.best_configuration = result.configuration

        return self._inner_get_next_configuration(result)

    def register_result(self, result):
        self.history.append((result, time.time()))


class RandomSearch(HyperparameterOptimization):
    def __init__(self):
        super().__init__()

    def _inner_get_next_configuration(self, result):
        # Number of trees in random forest
        n_estimators = list(range(50, 2000))
        # Number of features to consider at every split
        max_features = ['sqrt', 'log2']
        # Maximum number of levels in tree
        max_depth = list(range(5, 200))
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = range(2, 50)
        # Minimum number of samples required at each leaf node
        min_samples_leaf = range(1, 20)
        # Method of selecting samples for training each tree
        bootstrap = [True, False]

        return Configuration('rf', RFConfiguration(n_estimators=random.choice(n_estimators), 
                                    max_features=random.choice(max_features),
                                    max_depth=random.choice(max_depth),
                                    min_samples_split=random.choice(min_samples_split),
                                    min_samples_leaf=random.choice(min_samples_leaf),
                                    bootstrap=random.choice(bootstrap)))

