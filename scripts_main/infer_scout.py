# scripts_main/infer_scout.py
"""
Inference with the Scout model: lightweight predictions using minimal inputs.
"""

import joblib
import pandas as pd
from pathlib import Path
from typing import Tuple

from scripts_utility.master_order import SCOUT_FEATURE_ORDER, SCOUT_PREDICTABLES
from scripts_utility.paths import SCOUT_MODEL_PATH


def load_payload(path: Path) -> Tuple[dict, list[str]]:
    """Load trained Scout models + feature schema from disk."""
    payload = joblib.load(path)
    return payload["models"], payload["feature_columns"]


def preprocess(flat_inputs: dict, feature_columns: list[str]) -> pd.DataFrame:
    """
    Convert flat input dict into a DataFrame aligned with training schema.
    Handles one-hot encoding of process_method and column reindexing.
    """
    df = pd.DataFrame([flat_inputs])

    # Ensure all expected base features exist
    for col in SCOUT_FEATURE_ORDER:
        if col not in df.columns:
            df[col] = pd.NA

    # One-hot encode process_method
    if "process_method" in df.columns:
        dummies = pd.get_dummies(df["process_method"], prefix="proc", dummy_na=True)
        df = pd.concat([df.drop(columns=["process_method"]), dummies], axis=1)

    # Align to training feature columns
    df = df.reindex(columns=feature_columns, fill_value=0)

    # Coerce numeric
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def raw_infer(models: dict, X_new: pd.DataFrame, flat_inputs: dict) -> tuple[dict[str, float], dict[str, float]]:
    """
    Low-level inference: apply trained models directly to a prepared DataFrame.
    Only predict fields that the user did not provide.
    """
    ml_filled_fields: dict[str, float] = {}
    confidence: dict[str, float] = {}

    for target, model_info in models.items():
        # Skip if user already provided this field
        if flat_inputs.get(target) not in (None, "", "NaN"):
            continue

        kind, model = model_info
        if kind == "catboost":
            pred = model.predict(X_new)[0]
            confidence[target] = 1.0
        elif kind == "mean":
            pred = model
            confidence[target] = 0.2
        else:
            continue

        ml_filled_fields[target] = float(pred)

    return ml_filled_fields, confidence


def infer_scout(flat_inputs: dict) -> tuple[dict[str, float], dict[str, float]]:
    models, feature_columns = load_payload(SCOUT_MODEL_PATH)
    X_new = preprocess(flat_inputs, feature_columns)
    return raw_infer(models, X_new, flat_inputs)

