import math
from .base import ChannelModel
class TwoRayGroundChannel(ChannelModel):
    name="two_ray"
    def path_loss_db(self,tx,rx):
        d=max(self.distance_m(tx,rx),1.0); d0=max(self.cfg.get("d0_m",1.0),1e-9)
        ht=max(self.cfg.get("tx_height_m",1.5),0.01); hr=max(self.cfg.get("rx_height_m",1.5),0.01)
        wavelength=max(self.cfg.get("wavelength_m",0.125),1e-9)
        dc=max(4.0*math.pi*ht*hr/wavelength,d0)
        if d<=dc:
            return self.cfg["pl_d0_db"]+20.0*math.log10(d/d0)
        pl_dc=self.cfg["pl_d0_db"]+20.0*math.log10(dc/d0)
        return pl_dc+40.0*math.log10(d/dc)
