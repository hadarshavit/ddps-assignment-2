from multiprocessing import Queue
import threading
from abc import abstractmethod
from dataclasses import dataclass
from utils import Configuration


class HyperparameterOptimization:
    def __init__(self):
        self.history = []

    @abstractmethod
    def _inner_get_next_configuration(self, result):
        pass

    def get_next_configuration(self, result):
        if not result.first_configuration:
            self.history.append(result)
            if self.best_loss is not None and result.value < self.best_loss:
                self.best_loss = result.value
                self.best_configuration = result.configuration

        return self._inner_get_next_configuration(result)

    def register_result(self, result):
        pass


class RandomSearch(HyperparameterOptimization):
    def _inner_get_next_configuration(self, result):
        return Configuration('rf', 100)

