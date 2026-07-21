import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
LABELS_PATH = Path(__file__).parent.parent / "data" / "labels" / "combined_windows.json"


def load_series(filename: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / filename, parse_dates=["timestamp"])
    return df.set_index("timestamp").sort_index()


def load_anomaly_windows(filename: str) -> list:
    with open(LABELS_PATH) as f:
        all_windows = json.load(f)
    key = f"realAWSCloudwatch/{filename}"
    return [(pd.Timestamp(s), pd.Timestamp(e)) for s, e in all_windows.get(key, [])]


if __name__ == "__main__":
    fname = "ec2_cpu_utilization_825cc2.csv"
    df = load_series(fname)
    windows = load_anomaly_windows(fname)

    print(f"Fichier: {fname}")
    print(f"Shape: {df.shape}")
    print(f"Période: {df.index.min()} → {df.index.max()}")
    print(f"Colonnes: {list(df.columns)}")
    print(f"Nombre de fenêtres d'anomalies: {len(windows)}")
    print(windows)