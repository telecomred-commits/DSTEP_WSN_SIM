from .base import RadioController

class ChannelAwareAdaptiveRadioController(RadioController):
    """
    Separates:
      - coverage/weak-link problem -> increase TX power
      - congestion/collisions      -> backoff/wait; optionally reduce power
      - good excess margin         -> reduce TX power

    RSSI is feedback, never a directly controlled quantity.
    """
    name = "channel_aware_adaptive"

    def __init__(self, sim):
        super().__init__(sim)

    def _next_level(self, current, direction):
        levels = sorted(float(x) for x in self.cfg["power_levels_dbm"])
        idx = min(range(len(levels)), key=lambda i: abs(levels[i] - current))
        if direction > 0:
            idx = min(len(levels)-1, idx+1)
        elif direction < 0:
            idx = max(0, idx-1)
        return levels[idx]

    def _set_backoff(self, node, severe=False):
        stage = min(
            int(self.cfg.get("max_backoff_stage", 4)),
            node.radio_backoff_stage + 1
        )
        node.radio_backoff_stage = stage
        lo = float(self.cfg.get("backoff_min_s", 0.01))
        hi = float(self.cfg.get("backoff_max_s", 0.12))
        growth = float(self.cfg.get("backoff_growth", 1.7))
        stage_hi = min(hi, lo * (growth ** stage))
        node.pending_radio_backoff_s = self.sim.control_rng.uniform(lo, max(lo, stage_hi))
        node.radio_backoff_actions += 1
        if severe:
            node.radio_wait_actions += 1

    def transmission_directive(self, node):
        delay = max(0.0, float(node.pending_radio_backoff_s))
        node.pending_radio_backoff_s = 0.0
        if delay > 0.0:
            return {"transmit": True, "delay_s": delay, "reason": "adaptive_backoff"}
        return {"transmit": True, "delay_s": 0.0, "reason": "immediate"}

    def after_transmit(self, node, feedback):
        obs = int(feedback.get("observations", 0))
        if obs < int(self.cfg.get("min_feedback_samples", 1)):
            return

        mean_rssi = feedback.get("mean_rssi_dbm")
        success_rate = float(feedback.get("success_rate", 0.0))
        collision_rate = float(feedback.get("collision_rate", 0.0))
        below_rate = float(feedback.get("below_sensitivity_rate", 0.0))
        channel_loss_rate = float(feedback.get("channel_loss_rate", 0.0))

        node.last_feedback_rssi_dbm = mean_rssi
        node.last_feedback_success_rate = success_rate
        node.radio_tx_observations += 1

        sensitivity = self.sim.radio.receiver_sensitivity_dbm()
        margin = None if mean_rssi is None else mean_rssi - sensitivity

        target_margin = float(self.cfg.get("target_link_margin_db", 8.0))
        high_margin = float(self.cfg.get("high_link_margin_db", 15.0))
        min_success = float(self.cfg.get("min_success_rate", 0.80))
        high_success = float(self.cfg.get("high_success_rate", 0.95))
        collision_thr = float(self.cfg.get("collision_rate_threshold", 0.20))
        severe_collision_thr = float(self.cfg.get("severe_collision_rate_threshold", 0.45))
        below_thr = float(self.cfg.get("below_sensitivity_rate_threshold", 0.25))
        channel_loss_thr = float(self.cfg.get("channel_loss_rate_threshold", 0.30))

        congestion = collision_rate >= collision_thr
        severe_congestion = collision_rate >= severe_collision_thr
        weak_link = (
            (margin is not None and margin < target_margin)
            or below_rate >= below_thr
        )
        stochastic_channel_problem = (
            channel_loss_rate >= channel_loss_thr
            and not congestion
        )

        if congestion:
            node.radio_congestion_events += 1
            self._set_backoff(
                node,
                severe=severe_congestion and bool(self.cfg.get("wait_on_severe_congestion", True))
            )
            # Do not interpret collision losses as evidence to increase power.
            if (
                self.cfg.get("congestion_power_reduction_enabled", True)
                and margin is not None
                and margin > high_margin
            ):
                self.set_power(node, self._next_level(node.tx_power_dbm, -1))
            return

        if weak_link:
            node.radio_coverage_events += 1
            self.set_power(node, self._next_level(node.tx_power_dbm, +1))
            node.radio_backoff_stage = max(0, node.radio_backoff_stage - 1)
            return

        if stochastic_channel_problem:
            node.radio_channel_loss_events += 1
            # Fading/loss with acceptable RSSI: first use a small randomized wait,
            # rather than blindly escalating power.
            self._set_backoff(node, severe=False)
            if margin is not None and margin < high_margin and success_rate < min_success:
                self.set_power(node, self._next_level(node.tx_power_dbm, +1))
            return

        if success_rate >= high_success and margin is not None and margin > high_margin:
            self.set_power(node, self._next_level(node.tx_power_dbm, -1))
            node.radio_backoff_stage = max(0, node.radio_backoff_stage - 1)
        elif success_rate >= min_success:
            node.radio_backoff_stage = max(0, node.radio_backoff_stage - 1)
