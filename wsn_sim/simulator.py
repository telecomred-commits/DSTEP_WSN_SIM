import random
from .core.event_engine import EventEngine
from .nodes.node import Node
from .radio.model import RadioModel
from .radio_control.factory import create_radio_controller
from .environments.profiles import apply_profile
from .topology.metrics import topology_metrics
from .world.radial_event import RadialEvent
from .policies.periodic import PeriodicPolicy
from .policies.event_driven import EventDrivenPolicy
from .policies.central_edge import CentralEdgePolicy
from .policies.distributed_edge import DistributedEdgePolicy
from .policies.dstep import DStepPolicy

POLICIES = {
    "periodic": PeriodicPolicy,
    "event_driven": EventDrivenPolicy,
    "central_edge": CentralEdgePolicy,
    "distributed_edge": DistributedEdgePolicy,
    "dstep": DStepPolicy,
}

class Simulator:
    def __init__(self, cfg, node_count, policy_name, seed, ablation_mode="full"):
        self.cfg = cfg
        self.duration = cfg["simulation_time_s"]
        self.deadline_s = cfg["deadline_s"]
        self.period_s = cfg["period_s"]
        self.sensor_threshold = cfg["sensor"]["threshold"]

        self.engine = EventEngine()
        # Independent random streams: topology/sensing/channel cannot perturb each other.
        self.seed = seed
        self.topology_rng = random.Random(seed + 100003)
        self.sensor_rng = random.Random(seed + 200003)
        self.channel_rng = random.Random(seed + 300007)
        self.control_rng = random.Random(seed + 400009)
        self.rng = self.sensor_rng  # backwards-compatible alias; D-STEP does not use it.
        self.radio_cfg = apply_profile(cfg["radio"], cfg.get("environment", {"profile":"custom"}))
        self.radio = RadioModel(self.radio_cfg, self.channel_rng)
        self.policy_name = policy_name
        self.ablation_mode = ablation_mode
        self.intelligence_profile = cfg.get("_active_intelligence_profile")
        if self.intelligence_profile:
            profile = cfg.get("intelligence_profiles", {}).get(self.intelligence_profile)
            if profile is None:
                raise ValueError(f"Unknown intelligence profile: {self.intelligence_profile}")
            # Expose the profile through the existing D-STEP ablation interface.
            self.ablation_mode = self.intelligence_profile
            cfg.setdefault("ablation", {})[self.intelligence_profile] = {
                "use_consensus": profile.get("use_consensus", True),
                "use_voi": profile.get("use_voi", True),
                "use_estimation": profile.get("use_estimation", True),
                "use_prediction": profile.get("use_prediction", True),
                "use_density": profile.get("use_density", True),
                "use_suppression": profile.get("use_suppression", True),
                "use_backoff": profile.get("use_backoff", True),
            }

        self.world = RadialEvent(
            origin=cfg["event"]["origin"],
            start_time_s=cfg["event"]["start_time_s"],
            speed_m_s=cfg["event"]["speed_m_s"],
            radius_max_m=cfg["event"]["radius_max_m"],
        )

        w, h = cfg["area_m"]
        placement = cfg.get("topology", {}).get("placement", "uniform_random")
        manual = cfg.get("topology", {}).get("manual_positions", [])
        if placement == "manual":
            if len(manual) != node_count:
                raise ValueError(f"manual_positions must contain exactly {node_count} positions")
            self.nodes = [Node(i, tuple(map(float, manual[i]))) for i in range(node_count)]
        else:
            self.nodes = [Node(i, (self.topology_rng.uniform(0, w), self.topology_rng.uniform(0, h))) for i in range(node_count)]
        self.sink = Node(-1, tuple(cfg["sink_position"]))
        controller_name = cfg.get("radio_control", {}).get("mode", "fixed")
        self.radio_controller = create_radio_controller(controller_name, self)
        for node in self.nodes:
            self.radio_controller.initialize_node(node)
        self.radio_controller.initialize_node(self.sink)
        self.radio_cfg["tx_energy_by_power_mj"] = cfg.get("radio_control", {}).get("tx_energy_by_power_mj", {})
        self.policy = POLICIES[policy_name](self)

        self.collisions = 0
        self.channel_losses = 0
        self.out_of_range = 0
        self.below_sensitivity = 0

        # Node-specific sensor bias
        self.sensor_bias = {
            n.node_id: self.sensor_rng.gauss(0.0, self.cfg["sensor"].get("bias_std", 0.0))
            for n in self.nodes
        }

    def confidence_from_sample(self, x):
        return max(0.0, min(1.0, x))

    def sensor_value(self, node):
        signal = self.world.intensity(node.position, self.engine.time)
        noise = self.sensor_rng.gauss(0.0, self.cfg["sensor"]["noise_std"])
        x = signal + noise + self.sensor_bias[node.node_id]

        # Imperfecciones sintéticas controladas
        if signal > 0.55 and self.sensor_rng.random() < self.cfg["sensor"].get("false_negative_prob", 0.0):
            x *= 0.35
        elif signal < 0.2 and self.sensor_rng.random() < self.cfg["sensor"].get("false_positive_prob", 0.0):
            x = max(x, self.sensor_rng.uniform(0.58, 0.85))

        return max(0.0, min(1.0, x))

    def schedule_samples(self):
        t = 0.0
        while t <= self.duration:
            for node in self.nodes:
                self.engine.schedule(t, self.sample_node, node)
            t += self.period_s

    def sample_node(self, node):
        tm = self.cfg["timing_ms"]
        en = self.cfg["energy_mj"]

        node.energy_sense += en["sense"]
        node.energy_preprocess += en["preprocess"]

        value = self.sensor_value(node)

        if self.policy.uses_local_inference:
            node.energy_infer += en["infer"]
            confidence = self.confidence_from_sample(value)
            infer_ms = tm["infer"]
        else:
            # Baselines without Edge AI use the sensor/threshold value directly.
            confidence = value
            infer_ms = 0.0

        processing_delay = (tm["sense"] + tm["preprocess"] + infer_ms + tm["decision"]) / 1000.0
        decision_time = self.engine.time + processing_delay

        if confidence >= self.sensor_threshold and node.first_detection_time is None:
            node.first_detection_time = decision_time

        self.engine.schedule(decision_time, self.process_policy, node, value, confidence)

    def process_policy(self, node, value, confidence):
        self.policy.on_sample(node, value, confidence)

        # For baselines, detection is local classifier output.
        # For D-STEP, confirmed state is the network-level decision.
        if self.policy_name == "dstep":
            node.detected = node.confirmed
        else:
            if confidence >= self.sensor_threshold:
                node.detected = True
                if self.policy_name in ("periodic", "event_driven", "distributed_edge") and node.first_alert_time is None:
                    # these baselines act on their own local decision
                    node.first_alert_time = self.engine.time

    def neighbors(self, sender):
        return [
            n for n in self.nodes
            if n.node_id != sender.node_id and self.radio.nominal_link_available(sender, n)
        ]

    def communication_candidates(self, sender):
        return [
            n for n in self.nodes
            if n.node_id != sender.node_id and self.radio.candidate_receiver(sender, n)
        ]

    def feedback_receivers(self, sender, candidates=None):
        """
        Feedback is based on the nearest relevant receivers, not the entire network.
        This avoids distant irrelevant nodes forcing TX-power escalation.
        """
        if candidates is None:
            candidates = self.communication_candidates(sender)
        k = int(self.cfg.get("radio_control", {}).get("feedback_neighbor_count", 4))
        ranked = sorted(
            candidates,
            key=lambda n: ((n.position[0]-sender.position[0])**2 + (n.position[1]-sender.position[1])**2)
        )
        return ranked[:max(1, k)]

    def set_node_tx_power(self, node, power_dbm):
        """Optional algorithm-level radio control hook."""
        if not self.cfg.get("radio_control", {}).get("allow_policy_override", True):
            return node.tx_power_dbm
        return self.radio_controller.set_power(node, power_dbm)

    def _radio_params(self):
        tm = self.cfg["timing_ms"]
        en = self.cfg["energy_mj"]
        return (
            tm["access"]/1000.0,
            tm["tx_base"]/1000.0,
            en["tx_base"],
            en["rx_base"],
        )

    def _count_failure(self, reason):
        if reason == "collision":
            self.collisions += 1
        elif reason == "channel_loss":
            self.channel_losses += 1
        elif reason == "out_of_range":
            self.out_of_range += 1
        elif reason == "below_sensitivity":
            self.below_sensitivity += 1

    def broadcast(self, sender, payload):
        directive = self.radio_controller.transmission_directive(sender)
        delay_s = max(0.0, float(directive.get("delay_s", 0.0)))
        if delay_s > 0.0:
            self.engine.schedule(self.engine.time + delay_s, self._execute_broadcast, sender, payload)
            return
        self._execute_broadcast(sender, payload)

    def _execute_broadcast(self, sender, payload):
        """
        Physical broadcast. All candidates may receive the frame, but adaptive
        control feedback is computed only from nearest relevant receivers.
        """
        access_s, tx_base_s, tx_e, rx_e = self._radio_params()
        self.radio_controller.before_transmit(sender)
        receivers = self.communication_candidates(sender)
        relevant = self.feedback_receivers(sender, receivers)
        relevant_ids = {n.node_id for n in relevant}

        self.radio.charge_tx_frame(sender, tx_e)

        obs = []
        successes = collisions = below = channel_loss = 0

        for receiver in receivers:
            success, delay, rssi, reason = self.radio.attempt_receive(
                sender, receiver, payload, access_s, tx_base_s, rx_e, self.engine.time
            )
            if success:
                self.engine.schedule(self.engine.time + delay, self.receive, receiver, payload)
            else:
                self._count_failure(reason)

            if receiver.node_id in relevant_ids and rssi > -199:
                obs.append(rssi)
                if success:
                    successes += 1
                elif reason == "collision":
                    collisions += 1
                elif reason == "below_sensitivity":
                    below += 1
                elif reason == "channel_loss":
                    channel_loss += 1

        nobs = len(obs)
        denom = max(nobs, 1)
        feedback = {
            "observations": nobs,
            "relevant_receivers": len(relevant),
            "mean_rssi_dbm": (sum(obs)/nobs) if nobs else None,
            "success_rate": successes/denom if nobs else 0.0,
            "collision_rate": collisions/denom if nobs else 0.0,
            "below_sensitivity_rate": below/denom if nobs else 0.0,
            "channel_loss_rate": channel_loss/denom if nobs else 0.0,
            "successes": successes,
            "collisions": collisions,
            "below_sensitivity": below,
            "channel_losses": channel_loss,
        }
        self.radio_controller.after_transmit(sender, feedback)

    def send_to_sink(self, sender, payload):
        directive = self.radio_controller.transmission_directive(sender)
        delay_s = max(0.0, float(directive.get("delay_s", 0.0)))
        if delay_s > 0.0:
            self.engine.schedule(self.engine.time + delay_s, self._execute_send_to_sink, sender, payload)
            return
        self._execute_send_to_sink(sender, payload)

    def _execute_send_to_sink(self, sender, payload):
        access_s, tx_base_s, tx_e, rx_e = self._radio_params()
        self.radio_controller.before_transmit(sender)
        self.radio.charge_tx_frame(sender, tx_e)

        success, delay, rssi, reason = self.radio.attempt_receive(
            sender, self.sink, payload, access_s, tx_base_s, rx_e, self.engine.time
        )
        if success:
            self.engine.schedule(self.engine.time + delay, self.sink_receive, sender, payload)
        else:
            self._count_failure(reason)

        feedback = {
            "observations": 1 if rssi > -199 else 0,
            "relevant_receivers": 1,
            "mean_rssi_dbm": rssi if rssi > -199 else None,
            "success_rate": 1.0 if success else 0.0,
            "collision_rate": 1.0 if reason == "collision" else 0.0,
            "below_sensitivity_rate": 1.0 if reason == "below_sensitivity" else 0.0,
            "channel_loss_rate": 1.0 if reason == "channel_loss" else 0.0,
            "successes": 1 if success else 0,
            "collisions": 1 if reason == "collision" else 0,
            "below_sensitivity": 1 if reason == "below_sensitivity" else 0,
            "channel_losses": 1 if reason == "channel_loss" else 0,
        }
        self.radio_controller.after_transmit(sender, feedback)

    def sink_receive(self, sender, payload):
        if payload["confidence"] >= self.sensor_threshold and sender.first_alert_time is None:
            sender.first_alert_time = self.engine.time

    def receive(self, receiver, payload):
        self.policy.on_receive(receiver, payload)

    def topology_snapshot(self):
        return topology_metrics(
            self.nodes,
            self.cfg["area_m"],
            self.cfg.get("sensing", {}).get("sensing_radius_m"),
            link_predicate=self.radio.nominal_link_available,
            link_margin_fn=self.radio.link_margin_db
        )

    def run(self):
        self.schedule_samples()
        self.engine.run(self.duration)
        idle_e = self.cfg["energy_mj"]["idle_per_s"] * self.duration
        for n in self.nodes:
            n.energy_idle += idle_e
        return self
