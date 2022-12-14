from dataclasses import dataclass


@dataclass
class Configuration:
    algorithm: str
    number_of_trees: str


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

