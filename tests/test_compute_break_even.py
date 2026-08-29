import json
from pathlib import Path

def load_cfg():
    root=Path(__file__).resolve().parents[1]
    return json.loads((root/"config.json").read_text(encoding="utf-8"))

def test_compute_break_even_grid_contains_nominal_scale():
    cfg=load_cfg()
    vals=cfg["compute_break_even"]["ai_compute_scale_values"]
    assert 1.0 in vals
    assert min(vals) < 1.0
    assert max(vals) > 1.0

def test_only_intelligence_compute_components_are_scaled():
    cfg=load_cfg()
    comps=cfg["compute_break_even"]["scaled_energy_components"]
    assert comps == ["infer","consensus","estimate","prediction"]
    assert "tx_base" not in comps
    assert "rx_base" not in comps
    assert "sense" not in comps

def test_calibrated_tx_energy_is_preserved():
    cfg=load_cfg()
    table=cfg["radio_control"]["tx_energy_by_power_mj"]
    assert abs(table["-10"]-0.31185) < 1e-6
    assert abs(table["20"]-0.99792) < 1e-6
