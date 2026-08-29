import json
from pathlib import Path
from wsn_sim.simulator import Simulator

def links(sim):
    return sum(len(sim.neighbors(n)) for n in sim.nodes)

def test_tx_power_monotonic_nominal_connectivity():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/"config.json").read_text(encoding="utf-8"))
    cfg["radio"]["connectivity_mode"]="link_budget"
    cfg["radio"]["receiver_sensitivity_dbm"]=-90.0
    cfg["radio"]["tx_power_dbm"]=-10.0
    low=Simulator(cfg,20,"event_driven",12345)
    cfg["radio"]["tx_power_dbm"]=10.0
    high=Simulator(cfg,20,"event_driven",12345)
    assert links(high)>=links(low)

def test_receiver_sensitivity_monotonic_nominal_connectivity():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/"config.json").read_text(encoding="utf-8"))
    cfg["radio"]["connectivity_mode"]="link_budget"
    cfg["radio"]["tx_power_dbm"]=0.0
    cfg["radio"]["receiver_sensitivity_dbm"]=-80.0
    poor=Simulator(cfg,20,"event_driven",12345)
    cfg["radio"]["receiver_sensitivity_dbm"]=-100.0
    better=Simulator(cfg,20,"event_driven",12345)
    assert links(better)>=links(poor)
