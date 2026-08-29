import json
from pathlib import Path
from wsn_sim.simulator import Simulator

def load_cfg():
    root=Path(__file__).resolve().parents[1]
    return json.loads((root/"config.json").read_text(encoding="utf-8"))

def test_calibration_values_match_supplied_table():
    cfg=load_cfg();t=cfg["radio_control"]["tx_energy_by_power_mj"]
    assert abs(t["-10"]-0.31185)<1e-6
    assert abs(t["0"]-0.4158)<1e-6
    assert abs(t["10"]-0.58212)<1e-6
    assert abs(t["20"]-0.99792)<1e-6

def test_higher_power_costs_more_energy():
    cfg=load_cfg();cfg["radio_control"]["mode"]="fixed"
    sim=Simulator(cfg,20,"event_driven",12345);n=sim.nodes[0]
    vals=[]
    for p in [-10,0,10,20]:
        n.tx_power_dbm=p;vals.append(sim.radio.tx_energy_for_power(n,0.35))
    assert vals==sorted(vals)
