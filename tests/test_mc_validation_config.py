import json
from pathlib import Path

def test_mc_validation_has_repeated_runs_and_primary_metrics():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/"config.json").read_text(encoding="utf-8"))
    sw=cfg["mc_intelligence_validation"]
    assert sw["runs_per_point"] >= 20
    assert "dstep_full" in sw["intelligent_profiles"]
    assert "event_driven" in sw["classical_baselines"]
    for m in ["f1","dcr","tx_packets","energy_mj","collisions"]:
        assert m in sw["primary_metrics"]
