import math
from .log_distance import LogDistanceChannel
class NakagamiChannel(LogDistanceChannel):
    name="nakagami"
    def fading_db(self,tx,rx):
        m=max(self.cfg.get("nakagami_m",1.5),0.5); omega=max(self.cfg.get("nakagami_omega",1.0),1e-9)
        power=self.rng.gammavariate(m,omega/m)
        return 20.0*math.log10(max(math.sqrt(power),1e-12))
