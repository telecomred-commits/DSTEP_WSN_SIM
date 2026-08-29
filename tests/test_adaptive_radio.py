import json
from pathlib import Path
from wsn_sim.simulator import Simulator

def make_sim(mode="rule_based_adaptive"):
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/"config.json").read_text(encoding="utf-8"))
    cfg["radio_control"]["mode"]=mode
    cfg["radio_control"]["initial_tx_power_dbm"]=0
    return Simulator(cfg,20,"dstep",12345)

def test_power_is_per_node_and_bounded():
    sim=make_sim()
    n=sim.nodes[0]
    sim.set_node_tx_power(n,100)
    assert n.tx_power_dbm == max(sim.cfg["radio_control"]["power_levels_dbm"])
    sim.set_node_tx_power(n,-100)
    assert n.tx_power_dbm == min(sim.cfg["radio_control"]["power_levels_dbm"])

def test_bad_feedback_increases_power():
    sim=make_sim()
    n=sim.nodes[0]
    n.tx_power_dbm=0
    sim.radio_controller.after_transmit(n,{"observations":2,"mean_rssi_dbm":-100,"success_rate":0.2})
    assert n.tx_power_dbm > 0

def test_good_feedback_can_decrease_power():
    sim=make_sim()
    n=sim.nodes[0]
    n.tx_power_dbm=10
    sim.radio_controller.after_transmit(n,{"observations":2,"mean_rssi_dbm":-60,"success_rate":1.0})
    assert n.tx_power_dbm < 10

def test_fixed_controller_does_not_change_power():
    sim=make_sim("fixed")
    n=sim.nodes[0]
    before=n.tx_power_dbm
    sim.radio_controller.after_transmit(n,{"observations":2,"mean_rssi_dbm":-100,"success_rate":0.0})
    assert n.tx_power_dbm == before
