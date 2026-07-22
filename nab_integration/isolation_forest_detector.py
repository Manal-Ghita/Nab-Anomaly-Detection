import numpy as np
from sklearn.ensemble import IsolationForest

from nab.detectors.base import AnomalyDetector


class IsolationForestDetector(AnomalyDetector):
    """
    Isolation Forest baseline for the NAB benchmark.

    Isolation Forest is a batch algorithm, not a streaming one. So the
    model is trained once on the full file inside initialize(), and the
    precomputed anomaly scores are simply replayed row by row through
    handleRecord(), as required by the NAB detector interface.
    """

    def __init__(self, *args, **kwargs):
        super(IsolationForestDetector, self).__init__(*args, **kwargs)
        self.scores = None
        self.rowIndex = 0

    def initialize(self):
        data = self.dataSet.data.copy()

        # Features identified during EDA: raw value, rolling stats, diff
        window = 12  # 1 hour at 5-min frequency
        data["rolling_mean"] = data["value"].rolling(window).mean()
        data["rolling_std"] = data["value"].rolling(window).std()
        data["diff"] = data["value"].diff()

        # NAB requires one score per input row, so NaNs (from rolling/diff
        # at the start of the series) are filled rather than dropped
        data = data.bfill()

        features = data[["value", "rolling_mean", "rolling_std", "diff"]]

        model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
        model.fit(features)

        # decision_function: higher = more normal -> invert so higher = more anomalous
        raw_scores = -model.decision_function(features)

        # NAB requires scores in [0, 1] -> min-max normalize
        min_score, max_score = raw_scores.min(), raw_scores.max()
        self.scores = (raw_scores - min_score) / (max_score - min_score)

    def handleRecord(self, inputData):
        score = float(self.scores[self.rowIndex])
        self.rowIndex += 1
        return [score]