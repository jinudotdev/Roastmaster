# infer_core.py

from typing import Tuple, Dict, Any
from scripts_utility.paths import CORE_MODEL_PATH
from catboost import CatBoostRegressor
import pandas as pd
import json
import os
from datetime import datetime

CATEGORICAL_COLS = ["supplier", "country", "region", "variety", "process_method"]

# -------------------------------------------------------------------
# Preprocess for inference
# -------------------------------------------------------------------
def preprocess(values: Dict[str, Any]) -> Dict[str, Any]:
    """Convert raw capture dict into engineered features expected by Core."""
    roast_date = values.get("roast_date")
    purchase_date = values.get("purchase_date")

    # Compute freshness
    if isinstance(roast_date, datetime) and isinstance(purchase_date, datetime):
        values["bean_age_days_at_roast"] = (roast_date - purchase_date).days

    # Overwrite roast_date with day-of-year
    if isinstance(roast_date, datetime):
        values["roast_date"] = roast_date.timetuple().tm_yday

    # Drop purchase_date (not used by the model)
    values.pop("purchase_date", None)

    return values

# -------------------------------------------------------------------
# Core inference
# -------------------------------------------------------------------
def infer_core(inputs: dict) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Run CatBoost models on already-flattened inputs.
    Fills in missing fields directly in `inputs`.
    Returns (ml_filled_fields, confidence).
    """
    # Preprocess first, just like training
    inputs = preprocess(inputs)

    meta_path = os.path.join(os.path.dirname(CORE_MODEL_PATH), "ml_catboost_meta.json")
    if not os.path.exists(meta_path):
        print("❌ No metadata found — have you trained models yet?")
        return {}, {}

    with open(meta_path) as f:
        meta = json.load(f)

    feature_order = meta.get("feature_order", [])
    model_paths = meta.get("models", {})
    trained_targets = meta.get("predictables", list(model_paths.keys()))
    metrics = meta.get("metrics", {})

    df = pd.DataFrame([inputs]).reindex(columns=feature_order)
    df = df.loc[:, ~df.columns.duplicated()]

    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("NaN")

    predictions: Dict[str, Any] = {}
    skipped_targets: list[str] = []

    for col in trained_targets:
        path = model_paths.get(col)
        if not path or not os.path.exists(path):
            skipped_targets.append(col)
            continue
        model = CatBoostRegressor()
        model.load_model(path)
        try:
            predictions[col] = model.predict(df)[0]
        except Exception as e:
            print(f"❌ Skipped {col}: {str(e).splitlines()[-1]}")
            skipped_targets.append(col)

    ml_filled_fields: Dict[str, Any] = {}
    confidence: Dict[str, float] = {}

    for key, val in predictions.items():
        if inputs.get(key) is None and val is not None:
            inputs[key] = val
            ml_filled_fields[key] = val

            mae = metrics.get(key)
            if mae is None:
                conf = 0.5  # default mid confidence if no metric
            else:
                # Scale confidence: lower MAE → higher confidence
                # Clamp between 0.1 and 1.0
                conf = max(0.1, min(1.0, 1.0 / (1.0 + mae)))
            confidence[key] = conf

    print(f"🔮 Ran inference with {len(trained_targets)} trained targets, filled {len(ml_filled_fields)} fields")
    if skipped_targets:
        print(f"⚠️ Skipped {len(skipped_targets)} targets with no model: {', '.join(skipped_targets)}")

    return ml_filled_fields, confidence
