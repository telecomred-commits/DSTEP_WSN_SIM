from abc import ABC, abstractmethod

class Policy(ABC):
    name = "base"
    uses_local_inference = False

    def __init__(self, sim):
        self.sim = sim

    @abstractmethod
    def on_sample(self, node, value, confidence):
        ...

    def on_receive(self, node, message):
        pass
