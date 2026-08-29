from .base import Policy

class EventDrivenPolicy(Policy):
    uses_local_inference = False
    name = "event_driven"

    def on_sample(self, node, value, confidence):
        if value >= self.sim.sensor_threshold:
            self.sim.broadcast(node, {
                "type": "event",
                "confidence": confidence,
                "time": self.sim.engine.time
            })
