import json,random,math
from pathlib import Path
from wsn_sim.channels.factory import create_channel
class N:
 def __init__(self,x,y): self.position=(x,y)
def test_all_channel_models_finite():
 cfg=json.loads((Path(__file__).resolve().parents[1]/"config.json").read_text())["radio"]
 for name in ["free_space","log_distance","log_normal","two_ray","rayleigh","rician","nakagami"]:
  c=create_channel(name,cfg,random.Random(1)); r=c.rssi_dbm(N(0,0),N(10,0)); assert math.isfinite(r); assert 0<=c.reception_probability(r)<=1
