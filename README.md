# PA-DSTEP v0.50 reproducibility package

This archive supports the manuscript:

**When Does Distributed Intelligence Pay Off? A Payoff-Aware D-STEP Policy for Communication-Efficient Wireless Sensor Networks**

Authors: Carlos René Suárez Suárez and Oscar Fernando Penagos Espinel.

## What this package contains

1. **Frozen simulator source (v0.50)** and the automated test suite.
2. **TEST002 ESP32/ESP-NOW firmware and raw logs** for the five fixed-distance experiments (1, 10, 20, 25, and 30 m; three runs; 1,000 logical DATA packets per run; 15,000 transmissions total).
3. **Normalized TEST002 run-level dataset**, calibration script, fitted channel parameters, and held-out Run-3 validation outputs.
4. **Independent 5,000,000-series hold-out outputs** used before the final campaign.
5. **Final frozen 6,000,000-series campaign**: 3 event models × 3 node counts × 8 policies × 30 paired runs = 2,160 simulations, including raw rows, processed summaries, paired statistics, and reports.
6. **Manuscript figure source data, final figure images, and a regeneration script**.
7. Documentation, manifest, citation metadata, and SHA-256 checksums.

## Scientific scope

PA-DSTEP is the algorithm proposed in the associated manuscript. D-STEP is retained as the integrated architectural baseline. The v0.50 policy parameters were frozen before independent hold-out and final-campaign seed families were inspected.

The TEST002 hardware campaign calibrates **static two-node DATA RSSI/PDR**. It does **not** claim protocol-faithful experimental validation of native ESP-NOW contention, CCA timing, internal Wi-Fi retransmissions, or MAC ACK timing. Network energy reported in the final campaign is **modeled energy**, not direct current/energy measurement from the ESP32 boards.

## Quick start

Requires Python 3.10 or later.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r 01_simulator_source/requirements_reproducibility.txt
pip install -e 01_simulator_source
pytest 01_simulator_source/tests -q
```

Expected frozen-suite result: **115 tests passed**.

### Refit TEST002 calibration

```bash
python 03_channel_calibration/fit_esp32_test002.py
```

The raw files required by the calibration script are also available in `02_hardware_TEST002/raw_logs/`. The calibration copy is intentionally separated from the raw archive for clarity; see `REPRODUCE.md` for the exact working-directory procedure.

### Regenerate manuscript figures

```bash
python 06_figures_and_tables/generate_manuscript_figures.py
```

### Final campaign

The final campaign used fresh 6,000,000-series seeds. The preserved raw campaign is in `05_final_campaign_6M/results/final_raw.csv` (2,160 rows). The chunk runner and analysis script used to generate it are included.

## Important raw-data note

The original TX log for **10 m, Run 2** contains corrupted leading bytes. Its acquisition summary remains intact, and the RX log for the run is complete; the detailed TX parser recovers the later clean rows. The raw file is preserved unchanged. The normalized run-level dataset records this explicitly through `tx_log_rows_parsed` and `tx_log_complete_rows`.

## Version lineage

An earlier D-STEP simulator release is available at Zenodo DOI **10.5281/zenodo.22151638**. This v0.50 archive should preferably be published as a **new version** of that Zenodo record so that the conceptual lineage remains linked. After Zenodo mints the v0.50 DOI, cite the version-specific DOI in the manuscript.

## License

No reuse license is asserted by this generated archive because the authors have not selected one in this workflow. Select the intended license in Zenodo metadata before publication and, if desired, add the corresponding LICENSE file to the deposit.
