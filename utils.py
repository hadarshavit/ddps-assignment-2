from dataclasses import dataclass


@dataclass
class RFConfiguration:
    n_estimators: int
    # Number of features to consider at every split
    max_features: str
    # Maximum number of levels in tree
    max_depth: int
    # Minimum number of samples required to split a node
    min_samples_split: int
    # Minimum number of samples required at each leaf node
    min_samples_leaf: int
    # Method of selecting samples for training each tree
    bootstrap: bool


@dataclass
class Configuration:
    algorithm: str
    rf_config: RFConfiguration


@dataclass
class RunResults:
    configuration: Configuration
    value: float
    worker_id: int
    process_id: int
    first_configuration: bool


@dataclass
class RunInstruction:
    configuration: Configuration
    worker_id: int
    process_id: int


@dataclass
class MasterInitialMessage:
    worker_id: int
    task_name: str

