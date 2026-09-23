# ESP32 TEST002 real-hardware calibration report

## Experimental basis
The dataset contains 15 fixed-distance runs (1000 transmitted DATA packets each) at 1, 10, 20, 25 and 30 m. Each distance has three runs. TEST002 used a 48-byte DATA payload, Wi-Fi channel 6, application `MAX_RETRIES=0`, and an 80 ms application-ACK timeout. The transmitter logs report `tx_power_qdbm=80`; Espressif documents that the Wi-Fi API uses 0.25 dBm units and maps 80 to a commanded maximum of 20 dBm. Espressif also documents 1 Mbps as the default ESP-NOW PHY rate.

Raw logs are bundled under `calibration/esp32_test002/raw/`. `esp32_test002_runs.csv` is the normalized run-level registry.

## Calibration/validation split
- Calibration: Run 1 + Run 2 at each distance (10 runs; 10,000 DATA transmissions).
- Validation: Run 3 at each distance (5 runs; 5,000 DATA transmissions).

This avoids using the same run both to fit and to claim validation.

## Censored DATA/RSSI model
For run `i`, latent packet RSSI is modeled as

`R_ij = mu_i + epsilon_ij`, with `epsilon_ij ~ Normal(0, sigma_fast^2)`.

DATA decoding probability is

`P(success | R) = 1 / (1 + exp[-k (R - T)])`.

Successful packets contribute their observed RSSI to the likelihood. Failed packets contribute only a censored failure probability because their RSSI is not observed. A common `sigma_fast`, decoder midpoint `T`, and slope `k` are fitted jointly with one latent mean `mu_i` per calibration run.

The fitted calibration-run latent means are then regressed against log-distance:

`mu(d) = P_TX - PL(d0) - 10 n log10(d/d0)`.

Residual between-run spread is represented by a persistent link-shadow variable drawn once per directed link for each simulation realization.

## Fitted parameters
See `calibrated_parameters.json` for machine-readable values.

- `P_TX_reference = 20 dBm`
- `d0 = 1 m`
- `PL(d0) = 80.0333396 dB`
- `n = 2.2395445`
- `sigma_link = 5.4107865 dB`
- `sigma_fast = 3.4081073 dB`
- `T = -92.0968287 dBm`
- `k = 1.1242559 / dB`

The large effective `PL(d0)` is an empirical system-level intercept that includes the tested boards, antennas, orientation and environment. It is not free-space path loss.

## Why the model uses persistent shadowing
The raw repetitions show large changes at the same nominal distance. For example, 20 m DATA PDR was 99.5%, 55.5% and 31.2% across the three runs. At 25 m, mean PDR was lower than at 30 m. Encoding those five points as a deterministic distance lookup table would overfit the specific physical locations. v0.41 instead uses monotonic mean path loss plus a persistent per-link random term and packet-level variation.

## Held-out validation
`heldout_run3_validation.csv` contains a parameter-level predictive check, and `run_esp32_test002_validation.py` exercises the implemented simulator channel. In the generated 500-realization acceptance run, all five held-out PDR values and all five held-out successful-RSSI means were inside the corresponding 95% predictive intervals.

The intervals are intentionally broad because the real runs show strong between-run variability. Coverage is therefore evidence that the stochastic model can represent the observed variability, not proof of unique parameter identification.

## ACK evidence retained but not overclaimed
The hardware campaign also demonstrates that DATA arrival and application-ACK confirmation are not identical. Those columns are retained in `esp32_test002_runs.csv`, including `stale_acks` and the 80 ms timeout results. However, the firmware ACK was an application-level ESP-NOW message, while the simulator's ACK engine is a compact reliability abstraction. v0.41 therefore does not force those timing values into the native MAC model or claim protocol equivalence.

## Known data-quality note
`TX_10m_R2.txt` contains a truncated/corrupted early packet section in the supplied text capture; its final TX summary is intact and the corresponding RX run is complete. DATA PDR/RSSI for that run therefore come from the RX log, and RTT mean/min/max come from the TX summary. Per-packet RTT quantiles for that one TX file should not be reconstructed from the incomplete row section.
