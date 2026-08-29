import math

class ChannelModel:
    name = "base"
    def __init__(self, cfg, rng):
        self.cfg = cfg
        self.rng = rng
    def distance_m(self, tx, rx):
        return max(math.dist(tx.position, rx.position), 1e-9)
    def path_loss_db(self, tx, rx):
        raise NotImplementedError
    def shadowing_db(self, tx, rx):
        return 0.0
    def fading_db(self, tx, rx):
        return 0.0
    def mean_rssi_dbm(self, tx, rx):
        return self.cfg["tx_power_dbm"] - self.path_loss_db(tx, rx)
    def rssi_dbm(self, tx, rx):
        return self.cfg["tx_power_dbm"] - self.path_loss_db(tx, rx) + self.shadowing_db(tx, rx) + self.fading_db(tx, rx)
    def reception_probability(self, rssi_dbm):
        midpoint=self.cfg["rssi_midpoint_dbm"]; slope=self.cfg["rssi_slope"]
        return 1.0/(1.0+math.exp(-slope*(rssi_dbm-midpoint)))
    def propagation_delay_s(self, tx, rx):
        return self.distance_m(tx,rx)/3e8
