import csv
import os
import time
from typing import Optional

# TODO: Live feedback of accuracy over training session
# TODO: Live graph of accumulated hits on the board surrounding target
# TODO: Live 2-D board heatmap and gaussian distribution of all throws during session
class TrainingClient:
    """Lightweight logger for training throws."""

    def __init__(self, log_path: str):
        base_dir = os.path.dirname(os.path.abspath(log_path))
        training_dir = os.path.join(base_dir, "training_logs")
        os.makedirs(training_dir, exist_ok=True)
        self.log_path = os.path.join(training_dir, os.path.basename(log_path))
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "turn_state"])

    def log_throw(self, turn_state: str) -> Optional[str]:
        """Append a training throw to the CSV."""
        try:
            with open(self.log_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), turn_state])
            return None
        except Exception as exc:
            return str(exc)
