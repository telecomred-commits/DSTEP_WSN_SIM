# Reproduction guide

## 1. Verify software

From the archive root:

```bash
pip install -r 01_simulator_source/requirements_reproducibility.txt
pip install -e 01_simulator_source
pytest 01_simulator_source/tests -q
```

Expected: 115 passed.

## 2. Reproduce TEST002 fit

The original fit script expects a sibling `raw/` directory. To reproduce without altering the archived source:

```bash
mkdir -p 03_channel_calibration/raw
cp 02_hardware_TEST002/raw_logs/* 03_channel_calibration/raw/
python 03_channel_calibration/fit_esp32_test002.py --write
```

Compare the generated `calibrated_parameters_refit.json` with `calibrated_parameters.json`. Small floating-point differences can occur across numerical-library versions.

The calibration split is Runs 1–2 at each distance. Run 3 at each distance is held out.

## 3. Hardware-validation evidence

`03_channel_calibration/heldout_validation_simulated.csv` contains the simulator predictive distribution evaluated against the held-out Run-3 measurements. The manuscript reports that all five held-out DATA-PDR observations and all five successful-packet RSSI means fall inside their corresponding 95% predictive intervals.

## 4. Final campaign rerun

Copy or run from the simulator source directory because the runner resolves `config.json` relative to itself:

```bash
cd 01_simulator_source
python run_v050_final_campaign_chunk.py --start 0 --stop 2 --workers 4
# Continue 2-run chunks through --start 28 --stop 30.
python analyze_v050_final_campaign.py
```

The published archive preserves the complete final result, so rerunning all chunks is optional. The final design contains 2,160 simulations using paired seeds in the 6,000,000-series.

## 5. Figure regeneration

```bash
cd ..
python 06_figures_and_tables/generate_manuscript_figures.py
```

The script regenerates the seven manuscript-facing plots from archived source CSVs. `final_figures/` contains the submission-version images used by the manuscript.
