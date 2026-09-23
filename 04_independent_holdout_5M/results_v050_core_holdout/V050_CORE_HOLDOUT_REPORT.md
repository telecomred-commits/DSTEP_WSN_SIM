# V0.50 CORE HOLD-OUT REPORT

Independent hold-out seeds: 5,000,000-series; 30 paired runs per event model, node count and policy.
Policies: original D-STEP vs D-STEP Payoff-Aware. Event models: deterministic, physical_pulse, absent.

## Mean results

### deterministic

| N | Policy | Confirmation F1 | Awareness recall | DCR | Energy (mJ) | TX | Net false alarm |
|---:|---|---:|---:|---:|---:|---:|---:|
| 20 | dstep | 0.8995 | 0.9033 | 0.7700 | 390.5 | 35.2 | 0.000 |
| 20 | dstep_payoff | 1.0000 | 1.0000 | 0.9967 | 364.0 | 42.3 | 0.000 |
| 50 | dstep | 0.9959 | 0.9973 | 0.9940 | 1579.3 | 98.0 | 0.000 |
| 50 | dstep_payoff | 1.0000 | 1.0000 | 0.9987 | 1516.2 | 106.1 | 0.000 |
| 100 | dstep | 0.9998 | 0.9997 | 0.9997 | 5077.9 | 201.3 | 0.000 |
| 100 | dstep_payoff | 1.0000 | 1.0000 | 1.0000 | 4995.6 | 212.6 | 0.000 |

### physical_pulse

| N | Policy | Confirmation F1 | Awareness recall | DCR | Energy (mJ) | TX | Net false alarm |
|---:|---|---:|---:|---:|---:|---:|---:|
| 20 | dstep | 0.6133 | 0.7400 | 0.6850 | 364.2 | 29.6 | 0.000 |
| 20 | dstep_payoff | 0.7852 | 0.9700 | 0.9633 | 339.1 | 36.9 | 0.000 |
| 50 | dstep | 0.8981 | 0.9873 | 0.9740 | 1500.7 | 90.3 | 0.000 |
| 50 | dstep_payoff | 0.8599 | 0.9987 | 0.9973 | 1440.6 | 98.9 | 0.000 |
| 100 | dstep | 0.9660 | 1.0000 | 1.0000 | 4993.3 | 196.5 | 0.000 |
| 100 | dstep_payoff | 0.8929 | 1.0000 | 1.0000 | 4723.8 | 198.2 | 0.000 |

### absent

| N | Policy | Confirmation F1 | Awareness recall | DCR | Energy (mJ) | TX | Net false alarm |
|---:|---|---:|---:|---:|---:|---:|---:|
| 20 | dstep | 0.0000 | 0.0000 | 0.0000 | 265.5 | 8.7 | 0.200 |
| 20 | dstep_payoff | 0.0000 | 0.0000 | 0.0000 | 213.2 | 10.3 | 0.133 |
| 50 | dstep | 0.0000 | 0.0000 | 0.0000 | 765.7 | 19.3 | 0.800 |
| 50 | dstep_payoff | 0.0000 | 0.0000 | 0.0000 | 659.9 | 24.1 | 0.000 |
| 100 | dstep | 0.0000 | 0.0000 | 0.0000 | 2012.6 | 44.0 | 0.967 |
| 100 | dstep_payoff | 0.0000 | 0.0000 | 0.0000 | 1709.9 | 45.2 | 0.000 |

## Interpretation

Deterministic event: payoff-aware D-STEP improved or preserved confirmation F1, awareness and DCR at all N while reducing modeled energy; it used slightly more TX packets.

Physical pulse: payoff-aware D-STEP strongly improved awareness and DCR, especially at N=20, while reducing modeled energy. Confirmation F1 was higher at N=20 but lower than original D-STEP at N=50 and N=100. This is not hidden: it indicates that faster/wider awareness trades against stricter confirmation precision/recall semantics under dense physical-pulse scenarios.

Event absent: payoff-aware D-STEP eliminated network-level false alarms in the 30-run hold-out for N=50 and N=100 and reduced them at N=20, while also reducing energy. Original D-STEP showed increasing false-alarm incidence with density.

## Scientific status

This hold-out supports the payoff-aware policy as a substantially different and testable decision policy, but it also exposes a confirmation-quality trade-off in dense physical-pulse scenarios. The manuscript should report both confirmation F1 and awareness/DCR rather than collapsing them into a single reliability statement.

Full publication-scale comparisons against all external baselines should be run after freezing this research-candidate policy; do not tune on these hold-out seeds.