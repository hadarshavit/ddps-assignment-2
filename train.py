from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.neural_network import MLPClassifier
from multiprocessing import Process, Queue, Event
from utils import Configuration


class Trainer(Process):
    def __init__(self) -> None:
        self.queue = Queue()
        self.stop = Event()

    def run(self):
        while not self.stop.is_set():
            try:
                configuration:Configuration = self.queue.get(timeout=10)
            except:
                continue
            
            if configuration.algorithm == 'rf':
                # model = RandomForestClassifier(n_estimators=configuration['rf_n_estimators'],
                #                                 criterion=configuration['rf_criterion'],
                #                                 min_samples_split=configuration['rf_min_samples_split'],
                #                                 min_samples_leaf=configuration['rf_min_samples_leaf'],
                #                                 min_weight_fraction_leaf=configuration['rf_min_weight_fraction_leaf'],
                #                                 max_features=configuration['max_features'],
                #                                 bootstrap=configuration['bootstrap'],
                #                                 oob_score=configuration['oob_score'])
                


                