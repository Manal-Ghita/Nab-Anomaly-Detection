# Nab-Anomaly-Detection

Anomaly detection on real-world AWS CloudWatch time series, built from scratch as a learning 
project. Two approaches — **Isolation Forest** and an **LSTM Autoencoder** — are compared on 
the [NAB (Numenta Anomaly Benchmark)](https://github.com/numenta/NAB) `realAWSCloudwatch` 
dataset, evaluated with the official NAB scoring method.

## Objective

- Detect anomalies in real AWS server metrics (CPU utilization, network, disk, RDS) without 
  relying on labels during model training.
- Compare a classical ML baseline (Isolation Forest) against a deep learning approach (LSTM 
  Autoencoder) on the same data.
- Evaluate both with the **official NAB score**, not just standard classification metrics, to 
  get a result comparable to the published NAB benchmark methodology.

## Dataset

[`realAWSCloudwatch`](https://github.com/numenta/NAB/tree/master/data/realAWSCloudwatch) — 17 
CSV files of real AWS CloudWatch metrics (EC2 CPU utilization, disk write bytes, network in, 
RDS CPU utilization, ELB request count), each with labeled anomaly windows from 
`labels/combined_windows.json`.

## Repository Structure
Nab-Anomaly-Detection/
├── data/
│ ├── raw/ # NAB CSV files (realAWSCloudwatch)
│ ├── processed/ # cleaned/interpolated series
│ └── labels/
│ └── combined_windows.json
├── nab_integration/ # custom NAB detectors (source of truth, versioned here)
│ └── isolation_forest_detector.py
├── notebooks/
│ ├── 01_eda_ec2_cpu_825cc2.ipynb
│ ├── 02_isolation_forest_baseline.ipynb
│ ├── 03_lstm_autoencoder.ipynb
│ └── 04_final_comparison.ipynb
├── results/ # NAB scores, comparison tables/plots
├── scripts/
│ └── setup_nab.py # patches the external NAB repo with our custom detectors
├── src/
│ └── data_loading.py # load_series, load_anomaly_windows, clean_series
├── requirements.txt
└── README.md

## Setup

```bash
pip install -r requirements.txt
```

## Notebooks

Run in order — each builds on the previous one:

1. **`01_eda_ec2_cpu_825cc2.ipynb`** — Exploratory data analysis on a single file, then a 
   cross-file comparison across the `realAWSCloudwatch` category to identify the diversity of 
   normal/anomalous patterns in the dataset.
2. **`02_isolation_forest_baseline.ipynb`** — Feature engineering (rolling stats, diff) and 
   Isolation Forest baseline, evaluated first with standard metrics, then with the official NAB 
   scorer on 1 file, then generalized to all 17 files.
3. **`03_lstm_autoencoder.ipynb`** — LSTM Autoencoder built from scratch in PyTorch, trained on 
   normal segments, evaluated the same way (sanity check, then official NAB scoring on 1 file 
   and on all 17 files).
4. **`04_final_comparison.ipynb`** — Side-by-side comparison of both models' official NAB scores 
   and final conclusions.

## NAB Scoring Setup

This project uses the official NAB benchmark for scoring. To reproduce:

1. Clone NAB alongside this repo: `git clone https://github.com/numenta/NAB.git ../NAB`
2. Install its dependencies: `pip install -r ../NAB/requirements.txt`
3. Run the setup script: `python scripts/setup_nab.py --nab-path ../NAB`
4. Run scoring: `cd ../NAB && python run.py -d isolationForest --detect --optimize --score --normalize --dataDir data_test --windowsFile labels/combined_windows_test.json --skipConfirmation`

> Note: `NAB/` is an external dependency, not committed to this repo (see `.gitignore`). The 
> setup script re-integrates our custom detectors (`nab_integration/`) into a fresh clone.

## Results

Official NAB score on all 17 `realAWSCloudwatch` files:

| Profile | Isolation Forest | LSTM Autoencoder |
|---|---|---|
| Standard | 80.35 | 72.34 |
| Reward low FP | 76.29 | 72.04 |
| Reward low FN | 85.65 | 77.72 |

**Isolation Forest outperforms the LSTM Autoencoder** on all three NAB profiles in this setup. 
The main factor: the official NAB protocol restricts LSTM training to each file's probationary 
period (~15% of the data), while Isolation Forest generalizes more robustly with less data 
thanks to hand-engineered features (rolling std, diff). On a single file where the LSTM was 
trained with more representative data (exploratory notebook), it actually beat Isolation Forest 
on point-level F1 (0.501 vs 0.274) — suggesting the approach has genuine potential given more 
training data per file. Full analysis in `04_final_comparison.ipynb`.

