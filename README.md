# D-STEP WSN Simulator v0.16 — Compute Break-Even Release

This repository contains the Python discrete-event simulation framework used to evaluate **D-STEP (Distributed Spatio-Temporal Event Propagation)** for communication-efficient wireless sensor networks (WSNs).

The release supports the experiments reported in the manuscript **“When Does Distributed Intelligence Pay Off? D-STEP for Communication-Efficient Wireless Sensor Networks”** by Carlos René Suárez Suárez and Oscar Fernando Penagos Espinel.

## Scope of this release

The simulator is designed for rapid algorithm-centric WSN research. It models the network variables required by D-STEP—topology, sensing, event propagation, RSSI, receiver sensitivity, packet reception, collisions, energy, latency, and adaptive communication—without implementing a complete PHY/MAC/network protocol stack.

D-STEP operates only on information available locally to each node. Ground-truth event origin, propagation speed, future state, and true ETA are retained exclusively by the environment/evaluator for performance assessment.

## Main experimental configurations

The configuration file `config.json` contains several experiment blocks. The experiments associated with the final manuscript are:

### 1. Main Monte Carlo validation

Block: `mc_intelligence_validation`

- Node counts: 20, 50, 100
- Deployment areas: 100 × 100 m and 500 × 500 m
- Channels: Log-normal and Rician
- Runs per scenario: 20
- Policies: 3 classical baselines + 6 progressive D-STEP profiles
- Total simulations: 2160

Run:

```bash
python run_mc_intelligence_validation.py
```

Primary outputs:

```text
results_mc_intelligence/mc_intelligence_raw.csv
results_mc_intelligence/mc_intelligence_summary.csv
results_mc_intelligence/full_vs_baselines_statistics.csv
results_mc_intelligence/intelligence_layer_statistics.csv
```

### 2. Power-dependent TX-energy validation

Block: `energy_calibration_sweep`

- Same node counts, areas, and final channel models as the main validation
- Runs per point: 20
- Compares calibrated power-dependent TX energy against the constant-TX reference under matched scenario seeds

Run:

```bash
python run_calibrated_energy_validation.py
```

Primary outputs:

```text
results_calibrated_energy/calibrated_energy_raw.csv
results_calibrated_energy/calibrated_energy_summary.csv
results_calibrated_energy/dstep_full_calibration_impact.csv
results_calibrated_energy/full_vs_baselines_calibrated_statistics.csv
```

### 3. Computational break-even analysis

Block: `compute_break_even`

- Node counts: 20, 50, 100
- Deployment areas: 100 × 100 m and 500 × 500 m
- Channels: Log-normal and Rician
- Runs per point: 10
- D-STEP profile: `dstep_full`
- AI-compute scale values: 0.10, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00, 3.00, 4.00
- Scaled energy terms: inference, consensus, estimation, and prediction

Run:

```bash
python run_compute_break_even.py
```

Primary outputs:

```text
results_compute_break_even/compute_break_even_raw.csv
results_compute_break_even/compute_break_even_paired.csv
results_compute_break_even/compute_break_even_summary.csv
results_compute_break_even/compute_break_even_frontier.csv
```

The reported critical frontier is the largest tested/interpolated AI-compute scale for which DSTEP_FULL satisfies the energy comparison while maintaining the configured F1 and deadline-compliance thresholds.

## Progressive D-STEP intelligence stack

The release includes the following nested profiles:

1. `dstep_0_local` — local inference + basic evidence dissemination
2. `dstep_1_consensus` — adds decentralized spatio-temporal consensus
3. `dstep_2_voi` — adds Value of Information (VoI)
4. `dstep_3_prediction` — adds robust event estimation and ETA prediction
5. `dstep_4_network_adaptive` — adds density-aware forwarding, suppression, and backoff
6. `dstep_full` — adds channel-aware adaptive radio control

The classical baselines are periodic, event-driven/threshold, and distributed-edge.

## Repository structure

```text
.
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── config.json
├── simulation_parameters.csv
├── tx_energy_calibration.csv
├── compute_energy_baseline.csv
├── wsn_sim/                         # simulator and D-STEP implementation
├── tests/                           # automated tests
├── run_mc_intelligence_validation.py
├── run_calibrated_energy_validation.py
├── run_compute_break_even.py
├── run_intelligence_benchmark.py
├── run_ablation.py
├── run_parameter_sweep.py
├── run_channel_sweep.py
├── run_channel_aware_sweep.py
├── run_link_budget_sweep.py
├── run_adaptive_power_sweep.py
├── run_critical_radius_sweep.py
├── run_experiment.py
└── results_*/                       # archived raw and processed outputs
```

## Requirements

The simulator runtime uses the Python standard library. `pytest` is required only for the automated test suite.

Recommended environment:

- Python 3.11 or newer
- `pytest >= 8.0`

Install test dependency:

```bash
python -m pip install -r requirements.txt
```

## Verification

Run the automated tests with:

```bash
python -m pytest -q
```

The archived release was checked with this command before packaging.

## Reproducibility notes

Randomness is separated into independent streams for topology, sensing, channel realization, and radio-control stochasticity. Paired policy comparisons reuse the same scenario seed so that topology, event evolution, and sensing conditions remain aligned across policies. Channel draws are not fully counterfactual when different policies generate different transmission patterns.

A physical broadcast is accounted for as one sender TX frame, independent of the number of candidate receivers; reception outcomes are then evaluated individually.

The release includes raw and processed outputs so that manuscript values can be checked directly or regenerated using the corresponding execution scripts.

## Energy-model references

- `simulation_parameters.csv` documents the principal simulation parameters.
- `tx_energy_calibration.csv` contains the power-dependent TX-energy calibration used in the final energy validation.
- `compute_energy_baseline.csv` documents the nominal computation-energy terms used by the break-even analysis.

These values are model parameters used for algorithm-level evaluation; they are not presented as direct physical measurements of a complete ESP32-S3/ESP-NOW implementation.

## Citation

Please cite this software release using the Zenodo DOI assigned to the deposited version. A machine-readable citation record is provided in `CITATION.cff`.

## Authors

- Carlos René Suárez Suárez — Fundación Universitaria Los Libertadores — ORCID: 0000-0002-7558-1503
- Oscar Fernando Penagos Espinel — Fundación Universitaria Los Libertadores — ORCID: 0000-0002-3458-1240

## License

Released under the MIT License. See `LICENSE`.
