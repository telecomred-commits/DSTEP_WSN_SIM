# V0.50 FINAL FROZEN-POLICY CAMPAIGN

Fresh final-evaluation seeds: 6,000,000-series (not used for development or the 5,000,000-series hold-out).
Design: 3 event models × 3 node counts × 8 policies × 30 paired runs = 2,160 simulations.
Policies: Periodic, Event-driven, Send-on-Delta, TEEN-like, Distributed-edge, VoI baseline, original D-STEP, D-STEP Payoff-Aware.

All energy quantities below are modeled energy, not direct hardware energy measurements.

## deterministic

| N | Policy | Conf. F1 | Awareness | DCR | TX | Energy mJ | Collisions | Op. success |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 20 | periodic | 1.0000 | 1.0000 | 1.0000 | 600.0 | 2695.2 | 6269.7 | 1.000 |
| 20 | event_driven | 1.0000 | 1.0000 | 1.0000 | 345.3 | 1570.7 | 3672.9 | 1.000 |
| 20 | send_on_delta | 1.0000 | 1.0000 | 1.0000 | 154.2 | 727.2 | 1596.8 | 1.000 |
| 20 | teen_like | 1.0000 | 1.0000 | 1.0000 | 183.7 | 857.4 | 1910.7 | 1.000 |
| 20 | distributed_edge | 1.0000 | 1.0000 | 1.0000 | 345.3 | 1663.7 | 3672.9 | 1.000 |
| 20 | voi_baseline | 1.0000 | 1.0000 | 1.0000 | 113.0 | 638.4 | 1125.7 | 1.000 |
| 20 | dstep | 0.8900 | 0.9067 | 0.7500 | 35.0 | 389.7 | 317.1 | 0.133 |
| 20 | dstep_payoff | 1.0000 | 1.0000 | 0.9967 | 41.8 | 362.9 | 375.2 | 1.000 |
| 50 | periodic | 1.0000 | 1.0000 | 0.9993 | 1500.0 | 14805.8 | 48658.6 | 1.000 |
| 50 | event_driven | 1.0000 | 1.0000 | 0.9993 | 860.2 | 8541.1 | 28056.5 | 1.000 |
| 50 | send_on_delta | 1.0000 | 1.0000 | 0.9993 | 379.5 | 3833.5 | 12078.4 | 1.000 |
| 50 | teen_like | 1.0000 | 1.0000 | 0.9993 | 455.9 | 4582.0 | 14550.1 | 1.000 |
| 50 | distributed_edge | 1.0000 | 1.0000 | 0.9993 | 860.2 | 8773.6 | 28056.5 | 1.000 |
| 50 | voi_baseline | 1.0000 | 1.0000 | 0.9993 | 278.8 | 3080.5 | 8817.1 | 1.000 |
| 50 | dstep | 0.9956 | 0.9993 | 0.9860 | 100.6 | 1605.7 | 3034.9 | 0.933 |
| 50 | dstep_payoff | 1.0000 | 1.0000 | 1.0000 | 108.5 | 1538.4 | 3278.2 | 1.000 |
| 100 | periodic | 1.0000 | 1.0000 | 0.9977 | 3000.0 | 56349.9 | 234013.4 | 1.000 |
| 100 | event_driven | 1.0000 | 1.0000 | 0.9977 | 1730.2 | 32600.7 | 133483.6 | 1.000 |
| 100 | send_on_delta | 1.0000 | 1.0000 | 0.9977 | 763.4 | 14525.0 | 56868.8 | 1.000 |
| 100 | teen_like | 1.0000 | 1.0000 | 0.9977 | 911.6 | 17296.5 | 68028.2 | 1.000 |
| 100 | distributed_edge | 1.0000 | 1.0000 | 0.9977 | 1730.2 | 33065.7 | 133483.6 | 1.000 |
| 100 | voi_baseline | 1.0000 | 1.0000 | 0.9977 | 554.6 | 11085.1 | 40571.5 | 1.000 |
| 100 | dstep | 0.9998 | 1.0000 | 1.0000 | 201.8 | 5083.6 | 14631.1 | 1.000 |
| 100 | dstep_payoff | 1.0000 | 1.0000 | 1.0000 | 212.6 | 4994.1 | 15619.8 | 1.000 |

## physical_pulse

| N | Policy | Conf. F1 | Awareness | DCR | TX | Energy mJ | Collisions | Op. success |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 20 | periodic | 0.9923 | 0.9850 | 0.9817 | 600.0 | 2696.2 | 6320.1 | 0.967 |
| 20 | event_driven | 0.9923 | 0.9850 | 0.9817 | 51.2 | 272.5 | 496.1 | 0.967 |
| 20 | send_on_delta | 0.9923 | 0.9850 | 0.9817 | 39.7 | 221.7 | 376.0 | 0.967 |
| 20 | teen_like | 0.9923 | 0.9850 | 0.9817 | 42.9 | 235.9 | 403.3 | 0.967 |
| 20 | distributed_edge | 0.9923 | 0.9850 | 0.9817 | 51.2 | 365.5 | 496.1 | 0.967 |
| 20 | voi_baseline | 0.9923 | 0.9850 | 0.9817 | 39.5 | 313.7 | 381.4 | 0.967 |
| 20 | dstep | 0.5746 | 0.7100 | 0.6483 | 29.3 | 362.5 | 248.7 | 0.000 |
| 20 | dstep_payoff | 0.7851 | 0.9350 | 0.9183 | 37.1 | 339.3 | 296.7 | 0.000 |
| 50 | periodic | 0.9932 | 0.9867 | 0.9813 | 1500.0 | 14797.4 | 48586.8 | 0.967 |
| 50 | event_driven | 0.9932 | 0.9867 | 0.9813 | 128.3 | 1373.9 | 3876.3 | 0.967 |
| 50 | send_on_delta | 0.9932 | 0.9867 | 0.9813 | 101.5 | 1110.8 | 2987.0 | 0.967 |
| 50 | teen_like | 0.9932 | 0.9867 | 0.9813 | 108.8 | 1183.0 | 3248.6 | 0.967 |
| 50 | distributed_edge | 0.9932 | 0.9867 | 0.9813 | 128.3 | 1606.4 | 3876.3 | 0.967 |
| 50 | voi_baseline | 0.9932 | 0.9867 | 0.9813 | 100.8 | 1336.9 | 2964.6 | 0.967 |
| 50 | dstep | 0.9090 | 0.9847 | 0.9793 | 92.1 | 1521.1 | 2589.2 | 0.167 |
| 50 | dstep_payoff | 0.8502 | 0.9987 | 0.9980 | 98.4 | 1436.4 | 2764.3 | 0.033 |
| 100 | periodic | 0.9919 | 0.9840 | 0.9767 | 3000.0 | 56356.9 | 234703.2 | 1.000 |
| 100 | event_driven | 0.9919 | 0.9840 | 0.9767 | 257.8 | 5067.7 | 18686.0 | 1.000 |
| 100 | send_on_delta | 0.9919 | 0.9840 | 0.9767 | 202.3 | 4028.6 | 14167.4 | 1.000 |
| 100 | teen_like | 0.9919 | 0.9840 | 0.9767 | 218.6 | 4335.0 | 15497.0 | 1.000 |
| 100 | distributed_edge | 0.9919 | 0.9840 | 0.9767 | 257.8 | 5532.7 | 18686.0 | 1.000 |
| 100 | voi_baseline | 0.9919 | 0.9840 | 0.9767 | 199.5 | 4441.2 | 13808.0 | 1.000 |
| 100 | dstep | 0.9666 | 0.9997 | 0.9997 | 196.0 | 4979.7 | 13590.5 | 0.900 |
| 100 | dstep_payoff | 0.8958 | 0.9997 | 0.9997 | 199.4 | 4745.0 | 13641.7 | 0.033 |

## absent

| N | Policy | Network false-alarm incidence | False-alarm-free runs | TX | Energy mJ |
|---:|---|---:|---:|---:|---:|
| 20 | periodic | 1.0000 | 0.000 | 600.0 | 2696.2 |
| 20 | event_driven | 1.0000 | 0.000 | 10.2 | 91.6 |
| 20 | send_on_delta | 1.0000 | 0.000 | 9.7 | 89.3 |
| 20 | teen_like | 1.0000 | 0.000 | 9.8 | 89.8 |
| 20 | distributed_edge | 1.0000 | 0.000 | 10.2 | 184.6 |
| 20 | voi_baseline | 1.0000 | 0.000 | 9.9 | 183.1 |
| 20 | dstep | 0.2333 | 0.767 | 8.5 | 264.6 |
| 20 | dstep_payoff | 0.0667 | 0.933 | 10.1 | 212.3 |
| 50 | periodic | 1.0000 | 0.000 | 1500.0 | 14798.5 |
| 50 | event_driven | 1.0000 | 0.000 | 22.1 | 333.2 |
| 50 | send_on_delta | 1.0000 | 0.000 | 21.1 | 323.0 |
| 50 | teen_like | 1.0000 | 0.000 | 21.3 | 325.3 |
| 50 | distributed_edge | 1.0000 | 0.000 | 22.1 | 565.7 |
| 50 | voi_baseline | 1.0000 | 0.000 | 21.3 | 557.2 |
| 50 | dstep | 0.8000 | 0.200 | 18.2 | 754.1 |
| 50 | dstep_payoff | 0.0000 | 1.000 | 22.4 | 642.6 |
| 100 | periodic | 1.0000 | 0.000 | 3000.0 | 56357.5 |
| 100 | event_driven | 1.0000 | 0.000 | 44.8 | 1075.1 |
| 100 | send_on_delta | 1.0000 | 0.000 | 43.3 | 1046.3 |
| 100 | teen_like | 1.0000 | 0.000 | 43.8 | 1055.1 |
| 100 | distributed_edge | 1.0000 | 0.000 | 44.8 | 1540.1 |
| 100 | voi_baseline | 1.0000 | 0.000 | 43.1 | 1507.0 |
| 100 | dstep | 0.9667 | 0.033 | 45.0 | 2036.4 |
| 100 | dstep_payoff | 0.0000 | 1.000 | 45.8 | 1720.9 |

## Payoff-Aware versus original D-STEP (paired)

| Event | N | ΔConf.F1 | ΔAwareness | ΔDCR | ΔTX | ΔEnergy mJ | Holm p(E) |
|---|---:|---:|---:|---:|---:|---:|---:|
| deterministic | 20 | +0.1100 | +0.0933 | +0.2467 | +6.83 | -26.86 | 1.419e-06 |
| deterministic | 50 | +0.0044 | +0.0007 | +0.0140 | +7.87 | -67.33 | 1.304e-08 |
| deterministic | 100 | +0.0002 | +0.0000 | +0.0000 | +10.80 | -89.50 | 3.453e-05 |
| physical_pulse | 20 | +0.2105 | +0.2250 | +0.2700 | +7.77 | -23.24 | 1.382e-06 |
| physical_pulse | 50 | -0.0588 | +0.0140 | +0.0187 | +6.27 | -84.72 | 2.08e-05 |
| physical_pulse | 100 | -0.0708 | +0.0000 | +0.0000 | +3.47 | -234.72 | 1.304e-08 |
| absent | 20 | +0.0000 | +0.0000 | +0.0000 | +1.60 | -52.25 | 1.304e-08 |
| absent | 50 | +0.0000 | +0.0000 | +0.0000 | +4.20 | -111.52 | 1.304e-08 |
| absent | 100 | +0.0000 | +0.0000 | +0.0000 | +0.73 | -315.49 | 1.304e-08 |

## Integrity notes

- v0.50 policy parameters remained frozen; no tuning was performed using these 6,000,000-series results.
- Event-absent runs are interpreted through false-alarm metrics, not F1/DCR.
- Confirmation F1 and network awareness/DCR remain separate because the 5M hold-out exposed a real confirmation-versus-awareness trade-off.
- Hardware TEST002 calibrates/validates the measured ESP32 link profile; the final large-scale campaign remains simulation-based.
- Modeled energy must not be described as hardware-measured energy until direct current/time measurements are performed.