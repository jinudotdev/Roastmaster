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


def flatten_data(session_data: dict) -> dict:
    flat = {}

    # Metadata
    flat["supplier"] = session_data.get("supplier_name")
    flat["origin_country"] = session_data.get("origin_country")
    flat["altitude_meters"] = session_data.get("altitude_meters")
    flat["variety"] = session_data.get("variety")
    flat["process_method"] = session_data.get("process_method")
    flat["purchase_date"] = session_data.get("purchase_date")
    flat["roast_date"] = session_data.get("roast_date")
    flat["room_temp_f"] = session_data.get("room_temp_f")
    flat["humidity_pct"] = session_data.get("room_rh_pct")
    flat["bean_temp_start_f"] = session_data.get("bean_temp_pre_f")
    flat["green_bean_moisture_pct"] = session_data.get("green_bean_moisture_pct")

    flat["batch_weight_lbs"] = session_data.get("batch_weight_lbs")
    flat["end_temp"] = session_data.get("end_temp")

    # Stages
    for i in range(10):
        flat[f"stage_{i}_temp"] = None
        flat[f"stage_{i}_time"] = None
        flat[f"stage_{i}_burner"] = None

    for stage in session_data.get("stages", []):
        i = stage.get("stage")
        if isinstance(i, int) and 0 <= i < 10:
            flat[f"stage_{i}_temp"] = stage.get("bean_temp")
            flat[f"stage_{i}_time"] = stage.get("time_in_secs")
            flat[f"stage_{i}_burner"] = stage.get("burner_pct")

    # Turning Point (only temp + time)
    flat["turning_point_temp"] = session_data.get("turning_point_temp")
    flat["turning_point_time"] = session_data.get("turning_point_time")

    # Sensory
    sensory = session_data.get("sensory_scores", {}) or {}
    flat["target_clarity"] = sensory.get("clarity")
    flat["target_acidity"] = sensory.get("acidity")
    flat["target_body"] = sensory.get("body")
    flat["target_sweetness"] = sensory.get("sweetness")
    flat["target_overall"] = sensory.get("overall")

    # Strictly return only the 50 features
    return {k: flat.get(k) for k in FEATURE_ORDER}

def predict_with_ml(inputs: dict) -> Tuple[str, Dict[str, Any]]:
    """
    Run Jarvis multi-output model on flattened inputs.
    Returns (confidence_string, predictions_dict).
    """
    # Build feature vector
    features = [inputs.get(f) for f in FEATURE_ORDER]
    features = pd.to_numeric(pd.Series(features), errors="coerce").fillna(0).to_numpy().reshape(1, -1)

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
