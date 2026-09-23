# Data dictionary and provenance

## TEST002

`02_hardware_TEST002/esp32_test002_runs.csv` contains one row per distance/run (15 rows).

Key fields:
- `distance_m`: fixed nominal TX–RX separation.
- `run`: repetition identifier (1–3).
- `split`: `calibration` for Runs 1–2; `validation` for Run 3.
- `tx_packets`: logical DATA packets started (1,000 per run).
- `data_received_rx`: unique DATA packets observed by RX.
- `data_pdr`: RX DATA delivery ratio.
- `ack_confirmed_tx`: application ACKs accepted on time at TX.
- `confirmed_ratio`: ACK-confirmed / logical DATA packets.
- `stale_acks`: ACKs received after the 80-ms application timeout.
- `ack_missing_after_data`: DATA observed at RX for which no accepted/stale ACK was observed by TX.
- `ack_on_time_given_data`: conditional on-time ACK ratio given DATA arrival.
- `rssi_data_*`: RSSI statistics among successfully received DATA packets only.
- `rtt_*`: application-level RTT measured on the TX clock.
- `tx_log_rows_parsed`, `tx_log_complete_rows`: raw-log integrity indicators.

**Censoring note:** RSSI is only observed for received frames; missing frames do not have RSSI values. The calibration therefore uses a censored likelihood rather than fitting path loss only to successful RSSI.

**10 m Run 2 integrity note:** the TX file has corrupted leading bytes. RX data and TX summary are intact. The normalized dataset marks the detailed TX log as incomplete.

## Final campaign

`05_final_campaign_6M/final_raw.csv` contains 2,160 simulation rows and 151 output fields.

Design factors:
- `event_model`: deterministic, physical_pulse, absent.
- `nodes`: 20, 50, 100.
- `policy`: periodic, event_driven, send_on_delta, teen_like, distributed_edge, voi_baseline, dstep, dstep_payoff.
- `run`: 0–29.
- `seed`: paired within each event/node/run combination.

Core manuscript metrics include confirmation/policy-decision F1, network awareness recall, DCR, false-alarm incidence, TX packets, collisions, PDR/loss decomposition, delay, and modeled energy.

For D-STEP-family policies, F1 reflects distributed confirmation; external baselines use their own local decision semantics. Cross-family F1 therefore must not be interpreted as a universally identical classifier metric.
