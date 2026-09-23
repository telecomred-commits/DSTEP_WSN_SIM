# Zenodo upload instructions

Recommended action: open the existing Zenodo D-STEP record associated with DOI `10.5281/zenodo.22151638` and choose **New version** rather than creating an unrelated record. Upload the ZIP produced from this directory.

Suggested metadata:

- **Title:** PA-DSTEP v0.50: Simulator, ESP32 Calibration Dataset, and Reproducibility Package for Payoff-Aware Distributed Intelligence in Wireless Sensor Networks
- **Resource type:** Software (the archive also contains datasets)
- **Version:** v0.50
- **Creators:** Carlos René Suárez Suárez; Oscar Fernando Penagos Espinel
- **Affiliation:** Fundación Universitaria Los Libertadores, Bogotá, Colombia
- **Related manuscript:** *When Does Distributed Intelligence Pay Off? A Payoff-Aware D-STEP Policy for Communication-Efficient Wireless Sensor Networks*
- **Keywords:** Wireless Sensor Networks; PA-DSTEP; D-STEP; Edge AI; distributed intelligence; computation-communication trade-off; ESP32; ESP-NOW; Value of Information; reproducibility
- **Related identifier:** 10.5281/zenodo.22151638 (earlier version / lineage)

Suggested description:

> Reproducibility package for PA-DSTEP v0.50 and the manuscript “When Does Distributed Intelligence Pay Off? A Payoff-Aware D-STEP Policy for Communication-Efficient Wireless Sensor Networks.” The archive contains the frozen v0.50 simulator and automated tests, ESP32/ESP-NOW TEST002 firmware and raw measurements, normalized calibration data, channel-calibration and held-out validation scripts/results, the independent 5M-series hold-out, final 6M-series Monte Carlo outputs (2,160 simulations), processed paired statistics, and manuscript figure source data and generation scripts. TEST002 calibrates static two-node DATA RSSI/PDR; the large-scale network experiments remain simulation-based, and energy quantities are modeled rather than direct hardware energy measurements.

## Before pressing Publish

1. Choose the intended reuse **license** in Zenodo.
2. Confirm the creator names/order and affiliation.
3. Confirm `v0.50` as the version.
4. If available, add ORCID identifiers manually.
5. Publish and copy the **version-specific DOI** minted for v0.50.
6. Replace the manuscript's old v0.16 Zenodo reference with the v0.50 DOI.
7. Change the manuscript's Code and Data Availability statement from future-tense deposit language to the final public DOI.
