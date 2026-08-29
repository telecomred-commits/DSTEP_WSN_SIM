from .base import RadioController

class RuleBasedAdaptivePowerController(RadioController):
    name = "rule_based_adaptive"

    def __init__(self, sim):
        super().__init__(sim)
        self.cooldown = {}

    def _next_level(self, current, direction):
        levels = sorted(float(x) for x in self.cfg["power_levels_dbm"])
        idx = min(range(len(levels)), key=lambda i: abs(levels[i] - current))
        if direction > 0:
            idx = min(len(levels)-1, idx+1)
        elif direction < 0:
            idx = max(0, idx-1)
        return levels[idx]

    def after_transmit(self, node, feedback):
        obs = int(feedback.get("observations", 0))
        if obs < int(self.cfg.get("min_feedback_samples", 1)):
            return

        mean_rssi = feedback.get("mean_rssi_dbm")
        success_rate = feedback.get("success_rate")
        node.last_feedback_rssi_dbm = mean_rssi
        node.last_feedback_success_rate = success_rate
        node.radio_tx_observations += 1

        remaining = self.cooldown.get(node.node_id, 0)
        if remaining > 0:
            self.cooldown[node.node_id] = remaining - 1
            return

        sensitivity = self.sim.radio.receiver_sensitivity_dbm()
        target_margin = float(self.cfg.get("target_link_margin_db", 8.0))
        high_margin = float(self.cfg.get("high_link_margin_db", 15.0))
        min_success = float(self.cfg.get("min_success_rate", 0.80))
        high_success = float(self.cfg.get("high_success_rate", 0.95))

        margin = None if mean_rssi is None else mean_rssi - sensitivity

        increase = (
            success_rate is not None and success_rate < min_success
        ) or (
            margin is not None and margin < target_margin
        )

        decrease = (
            success_rate is not None and success_rate >= high_success
            and margin is not None and margin > high_margin
        )

        if increase:
            self.set_power(node, self._next_level(node.tx_power_dbm, +1))
            self.cooldown[node.node_id] = int(self.cfg.get("cooldown_transmissions", 1))
        elif decrease:
            self.set_power(node, self._next_level(node.tx_power_dbm, -1))
            self.cooldown[node.node_id] = int(self.cfg.get("cooldown_transmissions", 1))
