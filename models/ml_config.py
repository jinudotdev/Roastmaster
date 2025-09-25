# models/ml_config.py

"""
Central config for ML training.
Keeps thresholds and knobs in one place so you can tune without touching core code.
"""

ML_CONFIG = {
    # Minimum non-null coverage required for a column to be included
    "feature_coverage_threshold": 0.33,   # 33% for features
    "target_coverage_threshold": 0.33,    # 33% for targets


}
