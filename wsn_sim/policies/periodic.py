from .base import Policy

class PeriodicPolicy(Policy):
    uses_local_inference = False
    name = "periodic"

    def on_sample(self, node, value, confidence):
        # En este baseline el nodo transmite cada muestra programada.
        self.sim.broadcast(node, {
            "type": "sample",
            "confidence": confidence,
            "time": self.sim.engine.time
        })
