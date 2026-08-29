import json
from pathlib import Path

def test_critical_radius_sweep_config():
    root = Path(__file__).resolve().parents[1]
    cfg = json.loads((root/"config.json").read_text(encoding="utf-8"))
    sw = cfg["critical_radius_sweep"]
    assert len(sw["neighbor_radius_m_values"]) >= 3
    assert sw["operational_thresholds"]["largest_component_fraction_min"] > 0
    assert sw["operational_thresholds"]["f1_min"] > 0
    assert sw["operational_thresholds"]["dcr_min"] > 0
