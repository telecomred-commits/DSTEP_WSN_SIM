import json
from pathlib import Path
from wsn_sim.simulator import Simulator
def test_same_seed_same_topology_across_policies():
 cfg=json.loads((Path(__file__).resolve().parents[1]/"config.json").read_text())
 a=Simulator(cfg,20,"event_driven",777); b=Simulator(cfg,20,"dstep",777)
 assert [n.position for n in a.nodes]==[n.position for n in b.nodes]
 assert a.sensor_bias==b.sensor_bias
