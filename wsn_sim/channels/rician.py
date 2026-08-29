import math
from .log_distance import LogDistanceChannel
class RicianChannel(LogDistanceChannel):
    name="rician"
    def fading_db(self,tx,rx):
        k=10.0**(self.cfg.get("rician_k_db",6.0)/10.0)
        s=math.sqrt(k/(k+1.0)); sigma=math.sqrt(1.0/(2.0*(k+1.0)))
        x=self.rng.gauss(s,sigma); y=self.rng.gauss(0.0,sigma)
        return 20.0*math.log10(max(math.hypot(x,y),1e-12))
