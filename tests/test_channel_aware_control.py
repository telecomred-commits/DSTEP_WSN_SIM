import json
from pathlib import Path
from wsn_sim.simulator import Simulator

def make_sim():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/"config.json").read_text(encoding="utf-8"))
    cfg["radio_control"]["mode"]="channel_aware_adaptive"
    cfg["radio_control"]["initial_tx_power_dbm"]=0
    return Simulator(cfg,20,"dstep",12345)

def test_weak_link_increases_power():
    sim=make_sim()
    n=sim.nodes[0]
    n.tx_power_dbm=0
    sim.radio_controller.after_transmit(n,{
        "observations":4,"mean_rssi_dbm":-100,"success_rate":0.25,
        "collision_rate":0.0,"below_sensitivity_rate":0.75,"channel_loss_rate":0.0
    })
    assert n.tx_power_dbm > 0
    assert n.radio_coverage_events == 1

def test_collisions_do_not_force_power_increase():
    sim=make_sim()
    n=sim.nodes[0]
    n.tx_power_dbm=0
    sim.radio_controller.after_transmit(n,{
        "observations":4,"mean_rssi_dbm":-75,"success_rate":0.25,
        "collision_rate":0.75,"below_sensitivity_rate":0.0,"channel_loss_rate":0.0
    })
    assert n.tx_power_dbm <= 0
    assert n.radio_backoff_actions == 1
    assert n.radio_wait_actions == 1

def test_backoff_directive_is_consumed():
    sim=make_sim()
    n=sim.nodes[0]
    n.pending_radio_backoff_s=0.05
    d=sim.radio_controller.transmission_directive(n)
    assert d["delay_s"] == 0.05
    assert n.pending_radio_backoff_s == 0.0

def test_feedback_uses_nearest_relevant_receivers():
    sim=make_sim()
    sender=sim.nodes[0]
    candidates=sim.communication_candidates(sender)
    rel=sim.feedback_receivers(sender,candidates)
    assert len(rel) <= sim.cfg["radio_control"]["feedback_neighbor_count"]
    ds=[(r.position[0]-sender.position[0])**2+(r.position[1]-sender.position[1])**2 for r in rel]
    assert ds == sorted(ds)
