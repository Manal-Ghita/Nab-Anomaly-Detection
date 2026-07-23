# NAB Anomaly Detection

Anomaly detection on real-world AWS CloudWatch time series, built from scratch as a learning
project. Two approaches — **Isolation Forest** and an **LSTM Autoencoder** — are trained and
compared on the [NAB (Numenta Anomaly Benchmark)](https://github.com/numenta/NAB)
`realAWSCloudwatch` dataset, evaluated with the official NAB scoring method.

## Table of Contents

- [Objective](#objective)
- [Dataset](#dataset)
- [Repository Structure](#repository-structure)
- [Setup](#setup)
- [Notebooks](#notebooks)
- [NAB Scoring Setup](#nab-scoring-setup)
- [Results](#results)
- [Key Takeaways](#key-takeaways)
- [License](#license)

## Objective

- Detect anomalies in real AWS server metrics (CPU utilization, network, disk, RDS) in an
  unsupervised setting — no anomaly labels are used to train either model.
- Compare a classical ML baseline (Isolation Forest, hand-engineered features) against a deep
  learning approach (LSTM Autoencoder, learned temporal representation) on the same data.
- Evaluate both with the **official NAB score** — not just standard classification metrics —
  to get results directly comparable to the published NAB benchmark methodology, including its
  windowed, sigmoid-weighted scoring and per-profile threshold optimization.

## Dataset

[`realAWSCloudwatch`](https://github.com/numenta/NAB/tree/master/data/realAWSCloudwatch): 17
CSV files of real AWS CloudWatch metrics collected from production-like AWS server instances —
EC2 CPU utilization, EC2 disk write bytes, EC2 network in, RDS CPU utilization, ELB request
count. Each file has labeled anomaly windows in `labels/combined_windows.json`, provided by the
NAB project.

## Repository Structure

```
Nab-Anomaly-Detection/
├── data/
│   ├── raw/                    # NAB CSV files (realAWSCloudwatch)
│   ├── processed/              # cleaned / interpolated series
│   └── labels/
│       └── combined_windows.json
├── nab_integration/            # custom NAB detectors (source of truth, versioned here)
│   └── isolation_forest_detector.py
├── notebooks/
│   ├── 01_eda_ec2_cpu_825cc2.ipynb
│   ├── 02_isolation_forest_baseline.ipynb
│   ├── 03_lstm_autoencoder.ipynb
│   └── 04_final_comparison.ipynb
├── results/                    # NAB scores, comparison tables / plots
├── scripts/
│   └── setup_nab.py            # integrates our custom detectors into a cloned NAB repo
├── src/
│   └── data_loading.py         # load_series, load_anomaly_windows, clean_series
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone https://github.com/Manal-Ghita/Nab-Anomaly-Detection.git
cd Nab-Anomaly-Detection
pip install -r requirements.txt
```

## Notebooks

Run in order — each builds on the previous one.

| Notebook | Description |
|---|---|
| `01_eda_ec2_cpu_825cc2.ipynb` | Exploratory data analysis on a single file, then a cross-file comparison across `realAWSCloudwatch` to map out the diversity of normal/anomalous patterns in the dataset. |
| `02_isolation_forest_baseline.ipynb` | Feature engineering (rolling mean/std, point-to-point diff) and an Isolation Forest baseline — evaluated with standard metrics first, then with the official NAB scorer on one file, then generalized to all 17 files. |
| `03_lstm_autoencoder.ipynb` | LSTM Autoencoder built from scratch in PyTorch, trained on normal segments, evaluated the same way: sanity check with a threshold on reconstruction error, then official NAB scoring on one file and on all 17 files. |
| `04_final_comparison.ipynb` | Side-by-side comparison of both models' official NAB scores, with conclusions. |

## NAB Scoring Setup

This project uses the official NAB benchmark for scoring rather than a custom re-implementation,
so results are directly comparable to the published NAB methodology.

`NAB/` itself is **not** part of this repository (external dependency, excluded via
`.gitignore`) — the setup script below re-integrates the custom detectors from
`nab_integration/` into a fresh clone, so the whole pipeline is reproducible from scratch.

1. Clone NAB alongside this repo:
   ```bash
   git clone https://github.com/numenta/NAB.git ../NAB
   ```
2. Install its dependencies:
   ```bash
   pip install -r ../NAB/requirements.txt
   ```
3. Run the setup script (copies the custom detectors into the NAB clone, patches `run.py` and
   a known pandas-compatibility issue in `labeler.py`):
   ```bash
   python scripts/setup_nab.py --nab-path ../NAB
   ```
4. Run scoring, e.g. for the Isolation Forest detector on the full `realAWSCloudwatch` category:
   ```bash
   cd ../NAB
   python run.py -d isolationForest --detect --optimize --score --normalize \
       --dataDir data_test --windowsFile labels/combined_windows_realAWS.json \
       --skipConfirmation
   ```
   Swap `-d isolationForest` for `-d lstmAutoencoder` to score the other detector.

## Results

Official NAB score across all 17 `realAWSCloudwatch` files:

| Profile | Isolation Forest | LSTM Autoencoder |
|---|---:|---:|
| Standard | **80.35** | 72.34 |
| Reward low FP | **76.29** | 72.04 |
| Reward low FN | **85.65** | 77.72 |

*Scores are computed on the `realAWSCloudwatch` category only (17 files), not the full 58-file
NAB corpus — they are not directly comparable to the published NAB leaderboard.*

## Key Takeaways

- **Isolation Forest outperforms the LSTM Autoencoder** on all three NAB profiles under the
  official evaluation protocol.
- The main driver: the NAB protocol restricts LSTM training to each file's probationary period
  (~15% of the data), while Isolation Forest — using hand-engineered features like rolling std
  and point-to-point diff — stays robust even with limited or no anomaly-free training data.
- On a single file where the LSTM Autoencoder was trained with more representative data (see the
  exploratory notebook, which trains on all non-anomalous points instead of just the
  probationary period), it actually **beat** Isolation Forest on point-level F1 (0.501 vs 0.274)
  — suggesting the approach has genuine potential given more training data per file.
- The `realAWSCloudwatch` category contains highly diverse "normal" behaviors (stable high-CPU,
  near-zero sparse spikes, noisy stable signals, bursty duty-cycle patterns), which no single
  fixed threshold or architecture handles equally well — see `01_eda_ec2_cpu_825cc2.ipynb` for
  the full breakdown.

Full analysis and per-file diagnostics in `04_final_comparison.ipynb`.

## License

See [`LICENSE`](./LICENSE).
