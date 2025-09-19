"""
Jarvis Trainer — trains a multi-output ML model from roast logs in data/sessions/
and saves it into models/ for use by ml.py at prediction time.
"""

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Centralized paths
from scripts.utilities.paths import DATA_DIR, TRAINED_MODELS_DIR


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


def load_roast_data():
    rows = []
    for file in DATA_DIR.glob("*.json"):
        with open(file, "r") as f:
            roast = json.load(f)

        sd = roast.get("session_data", {})

        row = {
            # Metadata
            "supplier": sd.get("supplier_name"),
            "origin_country": sd.get("origin_country"),
            "altitude_meters": sd.get("altitude_meters"),
            "variety": sd.get("variety"),
            "process_method": sd.get("process_method"),
            "purchase_date": sd.get("purchase_date"),
            "roast_date": sd.get("roast_date"),
            "room_temp_f": sd.get("room_temp_f"),
            "humidity_pct": sd.get("room_rh_pct"),
            "bean_temp_start_f": sd.get("bean_temp_pre_f"),
            "green_bean_moisture_pct": sd.get("green_bean_moisture_pct"),

            # Required inputs only
            "batch_weight_lbs": sd.get("batch_weight_lbs"),
            "end_temp": sd.get("end_temp"),

            # Post-roast metrics
            "moisture_post_pct": sd.get("moisture_post_pct"),
            "agtron_whole": sd.get("agtron_whole"),

            # Turning Point (flexible: feature + target)
            "turning_point_temp": sd.get("turning_point_temp"),
            "turning_point_time": sd.get("turning_point_time"),

            # Sensory (flexible: feature + target)
            "target_clarity": sd.get("sensory_scores", {}).get("clarity"),
            "target_acidity": sd.get("sensory_scores", {}).get("acidity"),
            "target_body": sd.get("sensory_scores", {}).get("body"),
            "target_sweetness": sd.get("sensory_scores", {}).get("sweetness"),
            "target_overall": sd.get("sensory_scores", {}).get("overall"),
        }

        # Stage temps + burner % + times
        stages = sd.get("stages", [])
        for stage_num in range(10):
            stage_data = next((s for s in stages if s.get("stage") == stage_num), None)
            if stage_data:
                row[f"stage_{stage_num}_temp"] = stage_data.get("bean_temp")
                row[f"stage_{stage_num}_burner"] = stage_data.get("burner_pct")
                row[f"stage_{stage_num}_time"] = stage_data.get("time_in_secs")
            else:
                row[f"stage_{stage_num}_temp"] = None
                row[f"stage_{stage_num}_burner"] = None
                row[f"stage_{stage_num}_time"] = None

        rows.append(row)

    return pd.DataFrame(rows)


def preprocess(df):
    df = df.copy()
    for date_col in ["purchase_date", "roast_date"]:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.dayofyear
    for col in ["supplier", "origin_country", "variety", "process_method"]:
        df[col] = df[col].astype("category").cat.codes.replace(-1, np.nan)
    return df.fillna(df.mean(numeric_only=True))


def train_models(df):
    # Ensure all features are numeric
    df[FEATURE_ORDER] = df[FEATURE_ORDER].apply(pd.to_numeric, errors="coerce").fillna(0)
    df[TARGET_COLUMNS] = df[TARGET_COLUMNS].apply(pd.to_numeric, errors="coerce")

    X = df[FEATURE_ORDER].values
    Y = df[TARGET_COLUMNS].values

    print(f"📊 Features table: {X.shape[0]} roasts × {X.shape[1]} features")
    print(f"🎯 Targets table: {Y.shape[0]} roasts × {Y.shape[1]} targets")

    # Drop rows with no targets at all
    mask = ~np.all(np.isnan(Y), axis=1)
    X, Y = X[mask], Y[mask]

    # Fill missing targets with column means (so model can still train)
    col_means = np.nanmean(Y, axis=0)
    inds = np.where(np.isnan(Y))
    Y[inds] = np.take(col_means, inds[1])

    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, random_state=42
    )

    base_model = GradientBoostingRegressor(random_state=42)
    model = MultiOutputRegressor(base_model)
    model.fit(X_train, Y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(Y_test, preds)
    print(f"✅ Multi-output model trained — MAE = {mae:.2f}")

    # Save trained model
    save_path = TRAINED_MODELS_DIR / "ml_multi_output.pkl"
    joblib.dump(model, save_path)
    print(f"✅ Model saved to {save_path}")



def main():
    print("📦 Loading roast data...")
    df = load_roast_data()
    if df.empty:
        print("❌ No roast logs found.")
        return
    print("🛠 Preprocessing...")
    df = preprocess(df)
    print("🤖 Training Jarvis multi-output model...")
    train_models(df)
    print("✅ Training complete.")

if __name__ == "__main__":
    main()
