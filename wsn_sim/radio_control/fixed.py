from .base import RadioController

class FixedPowerController(RadioController):
    name = "fixed"

    def after_transmit(self, node, feedback):
        if feedback.get("observations", 0) > 0:
            node.last_feedback_rssi_dbm = feedback.get("mean_rssi_dbm")
            node.last_feedback_success_rate = feedback.get("success_rate")
            node.radio_tx_observations += 1
