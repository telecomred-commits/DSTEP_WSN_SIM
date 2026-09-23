# v0.50 final campaign audit

## Completion and independence

- Frozen policy: v0.50 Research Candidate.
- Final-evaluation seed family: 6,000,000-series.
- Development/tuning seeds: below 4,000,000.
- Prior independent hold-out seeds: 5,000,000-series.
- No v0.50 parameter was changed after the final 6M-series campaign was inspected.
- Design: 3 event models × 3 node counts × 8 policies × 30 paired runs = **2,160 simulations**.
- Policies: periodic, event-driven, Send-on-Delta, TEEN-like, distributed-edge, VoI baseline, original D-STEP, and D-STEP Payoff-Aware.
- Event models: deterministic, physical_pulse, event absent.
- Node counts: 20, 50, 100.
- Raw-row integrity check: 2,160 unique event/N/policy/run combinations.
- Test suite after campaign scripts/results were added: **115/115 passed** using `python -m pytest -q`.

## Main findings

### Deterministic event

Payoff-Aware D-STEP preserved or improved the strict D-STEP decision quality relative to original D-STEP at all three node counts while reducing modeled energy. The largest reliability gain occurred at N=20: DCR increased from 0.7500 to 0.9967 and D-STEP decision F1 from 0.8900 to 1.0000, while modeled energy decreased by 26.86 mJ on average. At N=50 and N=100 the reliability difference narrowed, while modeled energy remained lower.

### Physical pulse

The final campaign confirms the trade-off already exposed by the 5M hold-out. Payoff-Aware D-STEP improves network awareness and deadline compliance over original D-STEP, especially at N=20, and reduces modeled energy at all N. However, its strict D-STEP decision/confirmation F1 is lower than original D-STEP at N=50 and N=100. This must be reported rather than collapsed into a single reliability metric.

Against the external baselines, Payoff-Aware D-STEP is **not uniformly dominant**. The simpler local-decision baselines achieve very high local-decision F1 in the current physical-pulse sensor model, while some (Send-on-Delta, TEEN-like, VoI) also consume less modeled energy in parts of the operating space. This is compatible with the manuscript question "when does distributed intelligence pay off?" but rules out a universal-superiority claim.

### Event absent

Payoff-Aware D-STEP markedly suppresses network-level false alarms relative to original D-STEP. Final 6M results show network false-alarm incidence of 0.0667, 0, and 0 at N=20, 50, and 100 respectively, versus 0.2333, 0.8000, and 0.9667 for original D-STEP. Modeled energy is also lower for Payoff-Aware D-STEP at all N.

The external baselines show network false-alarm incidence 1.0 under the present evaluator definition because any local baseline alert at any negative node makes the run a network false alarm. This result is mathematically consistent with the current metric but should be explained carefully in the manuscript rather than presented as a simplistic claim that every baseline "fails".

## Metric-semantics warning

The evaluator uses each policy's own final decision semantics:

- for original D-STEP and Payoff-Aware D-STEP, `detected` corresponds to distributed confirmation;
- for the external baselines, `detected` corresponds to their local classifier/threshold decision.

Therefore the generic `f1`/`confirmation_f1` column should be called **policy-decision F1** when comparing all policy families. The term **confirmation F1** should be reserved for D-STEP-family discussion. Network awareness and DCR are separate metrics and should remain separate.

This is a reporting/interpretation issue, not a missing-run issue; no final simulations need to be rerun merely to rename the metric.

## Energy warning

All energy results in the final campaign are **modeled energy**. TEST002 provides real ESP32 packet-level RSSI/PDR/latency evidence for channel calibration/validation, but direct hardware measurements of TX/RX/idle/inference current and duration have not yet been performed. The manuscript must not label final energy values as hardware-measured energy.

## Statistical outputs

`final_summary.csv` contains means, standard deviations, and 95% bootstrap confidence intervals. `final_paired_comparisons.csv` contains paired mean differences, paired bootstrap confidence intervals, Cohen's dz, Wilcoxon signed-rank tests, and Holm-adjusted p-values for Payoff-Aware D-STEP against each comparator within each event/N family.

## Freeze rule after this campaign

The 6M-series data are final evaluation data for frozen v0.50. If algorithm parameters are now changed in response to these results, the modified algorithm must receive a new version and must be evaluated on a new, untouched seed family; the current 6M results cannot then be described as independent final validation of the modified policy.
