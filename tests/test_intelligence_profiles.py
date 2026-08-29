import copy, json
from pathlib import Path
from wsn_sim.simulator import Simulator

def load_cfg():
    root=Path(__file__).resolve().parents[1]
    return json.loads((root/"config.json").read_text(encoding="utf-8"))

def test_profiles_are_progressive_and_full_has_radio_intelligence():
    cfg=load_cfg()
    p=cfg["intelligence_profiles"]
    assert p["dstep_0_local"]["use_consensus"] is False
    assert p["dstep_1_consensus"]["use_consensus"] is True
    assert p["dstep_2_voi"]["use_voi"] is True
    assert p["dstep_3_prediction"]["use_prediction"] is True
    assert p["dstep_4_network_adaptive"]["use_density"] is True
    assert p["dstep_full"]["radio_control_mode"] == "channel_aware_adaptive"

def test_prediction_disabled_profile_does_not_charge_prediction_energy():
    cfg=load_cfg()
    cfg["_active_intelligence_profile"]="dstep_2_voi"
    cfg["radio_control"]["mode"]="fixed"
    sim=Simulator(cfg,20,"dstep",12345)
    sim.run()
    assert sum(n.energy_prediction for n in sim.nodes) == 0.0

def test_full_profile_activates_channel_aware_controller():
    cfg=load_cfg()
    cfg["_active_intelligence_profile"]="dstep_full"
    cfg["radio_control"]["mode"]=cfg["intelligence_profiles"]["dstep_full"]["radio_control_mode"]
    sim=Simulator(cfg,20,"dstep",12345)
    assert sim.radio_controller.name == "channel_aware_adaptive"

def test_dstep_still_cannot_reference_world_ground_truth():
    root=Path(__file__).resolve().parents[1]
    text=(root/"wsn_sim/policies/dstep.py").read_text(encoding="utf-8")
    assert "self.sim.world" not in text
