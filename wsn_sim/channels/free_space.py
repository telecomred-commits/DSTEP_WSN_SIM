import math
from .base import ChannelModel
class FreeSpaceChannel(ChannelModel):
    name="free_space"
    def path_loss_db(self,tx,rx):
        d0=max(self.cfg.get("d0_m",1.0),1e-9); d=max(self.distance_m(tx,rx),d0)
        return self.cfg["pl_d0_db"] + 20.0*math.log10(d/d0)
