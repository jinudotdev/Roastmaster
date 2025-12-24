# scripts_main/train_core_config.py

"""
Central config for ML training.
Keeps thresholds and knobs in one place so you can tune without touching core code.
"""

import math

def dynamic_threshold(num_rows: int, floor: float = 0.05, ceiling: float = 0.40) -> float:
    """
    Logarithmic decay threshold:
    - Starts stricter with small datasets
    - Relaxes gradually as dataset grows
    - Never drops below 'floor'
    - Never rises above 'ceiling'
    """
    if num_rows <= 1:
        return ceiling  # with 1 row, max strictness
    raw = 1.0 / math.log(num_rows + 1)
    return min(ceiling, max(floor, raw))

def get_thresholds(num_rows: int) -> tuple[float, float]:
    """
    Returns (feature_threshold, target_threshold).
    Both use the same log-based formula for simplicity.
    """
    feature_thresh = dynamic_threshold(num_rows)
    target_thresh = dynamic_threshold(num_rows)
    return feature_thresh, target_thresh
