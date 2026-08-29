import json
from pathlib import Path
from wsn_sim.simulator import Simulator

def test_broadcast_counts_one_tx_frame():
    root = Path(__file__).resolve().parents[1]
    with open(root / "config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    sim = Simulator(cfg, 20, "event_driven", seed=12345)
    sender = sim.nodes[0]

    before_tx = sender.tx_count
    before_energy = sender.energy_tx
    power_before_tx = sender.tx_power_dbm
    expected = sim.radio.tx_energy_for_power(sender, cfg["energy_mj"]["tx_base"])
    sim.broadcast(sender, {"type": "test", "confidence": 1.0})

    assert sender.tx_count == before_tx + 1
    assert abs(sender.energy_tx - (before_energy + expected)) < 1e-12
    assert power_before_tx == 0.0
