from typing import Tuple, Dict, Any
import joblib
import numpy as np
import pandas as pd

# Centralized paths
from scripts.utilities.paths import TRAINED_MODELS_DIR

FEATURE_ORDER = (
    [
        # Metadata
        "supplier", "origin_country", "altitude_meters", "variety",
        "process_method", "purchase_date", "roast_date",
        "room_temp_f", "humidity_pct", "bean_temp_start_f",
        "green_bean_moisture_pct", "batch_weight_lbs",

        # End metrics
        "end_temp", "moisture_post_pct", "agtron_whole",
    ]
    # Roast curve
    + [f"stage_{i}_temp" for i in range(10)]
    + [f"stage_{i}_time" for i in range(10)]
    + [f"stage_{i}_burner" for i in range(10)]

    # Turning point
    + ["turning_point_temp", "turning_point_time"]

    # Sensory profile
    + ["target_clarity", "target_acidity", "target_body",
       "target_sweetness", "target_overall"]
)

# In bi-directional mode, targets = the same full schema
TARGET_COLUMNS = FEATURE_ORDER


def predict_with_ml(inputs: dict) -> Tuple[str, Dict[str, Any]]:
    """
    Run Jarvis multi-output model on already-flattened inputs.
    Returns (confidence_string, predictions_dict).
    """
    # Build feature vector in the same order as training
    features = [inputs.get(f) for f in FEATURE_ORDER]
    features = (
        pd.to_numeric(pd.Series(features), errors="coerce")
        .fillna(0)
        .to_numpy()
        .reshape(1, -1)
    )

    model_path = TRAINED_MODELS_DIR / "ml_multi_output.pkl"
    print("Expecting model at:", model_path)
    print("Exists?", model_path.exists())

    if not model_path.exists():
        return "Low — no trained multi-output model found", {}

    model = joblib.load(model_path)
    preds = model.predict(features)[0]

    # Map predictions back to target names
    predictions = dict(zip(TARGET_COLUMNS, preds))

    # Merge in provided burner percents (don’t overwrite user-supplied values)
    provided_burners = inputs.get("burner_percents", {})
    burner_preds = {}
    for stage in range(10):
        if stage in provided_burners:
            burner_preds[stage] = provided_burners[stage]
        else:
            burner_preds[stage] = predictions.get(f"stage_{stage}_burner")
    predictions["burner_pct"] = burner_preds

    # Confidence: count how many fields we actually filled
    ml_filled_fields = [k for k, v in predictions.items() if v is not None]
    total_slots = len(ml_filled_fields)
    if total_slots >= 10:
        confidence = f"High — predicted {total_slots} fields from trained model"
    elif total_slots >= 5:
        confidence = f"Medium — predicted {total_slots} fields from trained model"
    else:
        confidence = f"Low — predicted {total_slots} fields from trained model"

    return confidence, predictions
