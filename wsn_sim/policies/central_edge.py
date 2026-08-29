from .base import Policy

class CentralEdgePolicy(Policy):
    uses_local_inference = False
    name = "central_edge"

    def on_sample(self, node, value, confidence):
        # Todos reportan al sink; el sink concentra la decisión.
        self.sim.send_to_sink(node, {
            "type": "feature",
            "confidence": confidence,
            "time": self.sim.engine.time
        })
