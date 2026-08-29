from dataclasses import dataclass, field
from typing import Tuple, List, Set

@dataclass
class Node:
    node_id: int
    position: Tuple[float, float]
    battery_mj: float = 100000.0

    # Per-node adaptive radio state
    tx_power_dbm: float = 0.0
    last_tx_power_dbm: float = 0.0
    last_feedback_rssi_dbm: float | None = None
    last_feedback_success_rate: float | None = None
    radio_power_changes: int = 0
    radio_power_increases: int = 0
    radio_power_decreases: int = 0
    radio_tx_observations: int = 0
    radio_backoff_actions: int = 0
    radio_wait_actions: int = 0
    radio_congestion_events: int = 0
    radio_coverage_events: int = 0
    radio_channel_loss_events: int = 0
    radio_backoff_stage: int = 0
    pending_radio_backoff_s: float = 0.0
    tx_power_history: List[float] = field(default_factory=list)

    local_confidence: float = 0.0
    global_belief: float = 0.0
    state: str = "NORMAL"

    detected: bool = False
    confirmed: bool = False

    first_detection_time: float | None = None
    first_confirmation_time: float | None = None
    first_alert_time: float | None = None

    # D-STEP estimates available to THIS node only
    est_origin: Tuple[float, float] | None = None
    est_t0: float | None = None
    est_speed: float | None = None
    est_direction: Tuple[float, float] | None = None
    est_eta: float | None = None
    estimate_points: int = 0

    tx_count: int = 0
    rx_count: int = 0
    bytes_tx: int = 0

    energy_sense: float = 0.0
    energy_preprocess: float = 0.0
    energy_infer: float = 0.0
    energy_consensus: float = 0.0
    energy_estimate: float = 0.0
    energy_prediction: float = 0.0
    energy_tx: float = 0.0
    energy_rx: float = 0.0
    energy_idle: float = 0.0

    messages_received: List[dict] = field(default_factory=list)
    seen_messages: Set[str] = field(default_factory=set)
    suppression_memory: List[dict] = field(default_factory=list)
    pending_forward_token: int = 0
    suppressed_tx_count: int = 0

    @property
    def total_energy(self):
        return (
            self.energy_sense
            + self.energy_preprocess
            + self.energy_infer
            + self.energy_consensus
            + self.energy_estimate
            + self.energy_prediction
            + self.energy_tx
            + self.energy_rx
            + self.energy_idle
        )
