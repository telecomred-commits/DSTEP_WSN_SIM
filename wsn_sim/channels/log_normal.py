from .log_distance import LogDistanceChannel
class LogNormalChannel(LogDistanceChannel):
    name="log_normal"
    def shadowing_db(self,tx,rx):
        return self.rng.gauss(0.0,self.cfg.get("shadow_sigma_db",0.0))
