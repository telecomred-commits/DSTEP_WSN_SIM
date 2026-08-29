from .base import Policy

class DistributedEdgePolicy(Policy):
    uses_local_inference = True
    name = "distributed_edge"

    def __init__(self, sim):
        super().__init__(sim)
        self.cfg = sim.cfg["distributed_edge"]
        self.last_sent_conf = {}

    def _voi(self, node, confidence):
        prev = self.last_sent_conf.get(node.node_id, 0.0)
        novelty = abs(confidence - prev)

        eta = self.sim.world.arrival_time(node.position) - self.sim.engine.time
        urgency = 1.0 if eta <= 0 else max(0.0, 1.0 - eta / max(self.sim.deadline_s, 1e-9))

        voi = (
            self.cfg["novelty_weight"] * novelty
            + self.cfg["confidence_weight"] * confidence
            + self.cfg["urgency_weight"] * urgency
        )
        return voi

    def _neighbor_confirmations(self, node):
        confirmations = 0
        for msg in node.messages_received[-20:]:
            if (
                msg.get("type") == "edge_evidence"
                and msg.get("confidence", 0.0) >= self.cfg["neighbor_threshold"]
            ):
                confirmations += 1
        return confirmations

    def on_sample(self, node, value, confidence):
        node.local_confidence = confidence

        local_candidate = confidence >= self.cfg["local_threshold"]
        confirmations = self._neighbor_confirmations(node)
        voi = self._voi(node, confidence)

        if local_candidate and (
            confirmations >= self.cfg["min_confirmations"]
            or voi >= self.cfg["voi_threshold"]
        ):
            self.last_sent_conf[node.node_id] = confidence
            self.sim.broadcast(node, {
                "type": "edge_evidence",
                "confidence": confidence,
                "time": self.sim.engine.time,
                "voi": voi
            })
