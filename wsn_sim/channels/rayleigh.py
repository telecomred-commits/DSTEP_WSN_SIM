import math
from .log_distance import LogDistanceChannel
class RayleighChannel(LogDistanceChannel):
    name="rayleigh"
    def fading_db(self,tx,rx):
        u=max(self.rng.random(),1e-12)
        amp=math.sqrt(-math.log(u))
        return 20.0*math.log10(max(amp,1e-12))
