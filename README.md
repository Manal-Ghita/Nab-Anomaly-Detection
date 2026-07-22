# Nab-Anomaly-Detection


## NAB Scoring Setup

This project uses the official NAB benchmark for scoring. To reproduce:

1. Clone NAB alongside this repo: `git clone https://github.com/numenta/NAB.git ../NAB`
2. Install its dependencies: `pip install -r ../NAB/requirements.txt`
3. Run the setup script: `python scripts/setup_nab.py --nab-path ../NAB`
4. Run scoring: `cd ../NAB && python run.py -d isolationForest --detect --optimize --score --normalize --dataDir data_test --windowsFile labels/combined_windows_test.json --skipConfirmation`