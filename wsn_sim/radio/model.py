import math
from wsn_sim.channels.factory import create_channel

class RadioModel:
    def __init__(self, cfg, rng):
        self.cfg = cfg
        self.rng = rng
        self.last_rx_time = {}
        self.channel = create_channel(cfg.get("channel_model","log_normal"), cfg, rng)

    def rssi(self, distance_m):
        class P:
            def __init__(self, x):
                self.position = (x,0.0)
        return self.channel.rssi_dbm(P(0.0), P(max(distance_m,1e-9)))

    def tx_power_dbm(self, sender):
        return float(getattr(sender, "tx_power_dbm", self.cfg.get("tx_power_dbm", 0.0)))

    def mean_rssi(self, a, b):
        return (
            self.tx_power_dbm(a)
            - self.channel.path_loss_db(a,b)
        )

    def instantaneous_rssi(self, a, b):
        return (
            self.tx_power_dbm(a)
            - self.channel.path_loss_db(a,b)
            + self.channel.shadowing_db(a,b)
            + self.channel.fading_db(a,b)
        )

    def receiver_sensitivity_dbm(self):
        return self.cfg.get("receiver_sensitivity_dbm", self.cfg.get("rssi_midpoint_dbm",-82.0))

    def link_margin_db(self, a, b):
        return self.mean_rssi(a,b) - self.receiver_sensitivity_dbm()

    def nominal_link_available(self, a, b):
        d = math.dist(a.position,b.position)
        mode = self.cfg.get("connectivity_mode","geometric")
        if mode == "geometric":
            return d <= self.cfg.get("neighbor_radius_m", float("inf"))
        cap = self.cfg.get("max_geometric_range_m")
        if cap is not None and d > float(cap):
            return False
        return self.link_margin_db(a,b) >= 0.0

    def candidate_receiver(self, a, b):
        d = math.dist(a.position,b.position)
        if self.cfg.get("connectivity_mode","geometric") == "geometric":
            return d <= self.cfg.get("neighbor_radius_m", float("inf"))
        cap = self.cfg.get("max_geometric_range_m")
        return cap is None or d <= float(cap)

    def success_probability(self, rssi_dbm):
        midpoint = self.receiver_sensitivity_dbm()
        slope = self.cfg.get("sensitivity_slope", self.cfg.get("rssi_slope",0.18))
        return 1.0/(1.0 + math.exp(-slope*(rssi_dbm-midpoint)))

    def packet_delay_s(self, distance_m, payload_bytes, access_s, tx_base_s):
        return access_s + tx_base_s + payload_bytes*8/self.cfg["bitrate_bps"] + distance_m/3e8

    def within_range(self, a, b):
        return self.nominal_link_available(a,b)

    def tx_energy_for_power(self, sender, default_tx_energy):
        table = self.cfg.get("tx_energy_by_power_mj", {})
        if not table:
            return default_tx_energy
        p = self.tx_power_dbm(sender)
        # JSON object keys are strings; use nearest calibrated power point.
        pts = [(float(k), float(v)) for k,v in table.items()]
        _, energy = min(pts, key=lambda kv: abs(kv[0]-p))
        return energy

    def charge_tx_frame(self, sender, tx_energy):
        sender.tx_count += 1
        sender.bytes_tx += self.cfg["payload_bytes"]
        sender.energy_tx += self.tx_energy_for_power(sender, tx_energy)

    def attempt_receive(self, sender, receiver, payload, access_s, tx_base_s, rx_energy, now):
        if not self.candidate_receiver(sender,receiver):
            return False,0.0,-200.0,"out_of_range"

        d = math.dist(sender.position,receiver.position)
        rssi = self.instantaneous_rssi(sender,receiver)
        sensitivity = self.receiver_sensitivity_dbm()
        delay = self.packet_delay_s(d,self.cfg["payload_bytes"],access_s,tx_base_s)

        if self.cfg.get("use_hard_sensitivity_cutoff",True) and rssi < sensitivity:
            return False,delay,rssi,"below_sensitivity"

        p = self.success_probability(rssi)
        collision_window = self.cfg.get("collision_window_ms",0.0)/1000.0
        last = self.last_rx_time.get(receiver.node_id)
        if last is not None and abs(now-last) <= collision_window:
            return False,0.0,rssi,"collision"

        success = self.rng.random() < p
        if success:
            self.last_rx_time[receiver.node_id] = now
            receiver.rx_count += 1
            receiver.energy_rx += rx_energy
            receiver.messages_received.append(payload)

        return success,delay,rssi,"ok" if success else "channel_loss"
