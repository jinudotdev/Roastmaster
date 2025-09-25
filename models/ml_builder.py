"""
Jarvis Trainer — trains a multi-output ML model from roast logs in data/sessions/
and saves it into models/ for use by ml.py at prediction time.
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Centralized paths
from scripts.utilities.paths import DATA_DIR, TRAINED_MODELS_DIR
from models.ml_config import ML_CONFIG

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
    roast_file = DATA_DIR / "roast_data.jsonl"
    if not roast_file.exists():
        print(f"❌ {roast_file} not found.")
        return pd.DataFrame()

    df = pd.read_json(roast_file, lines=True)
    return df



def preprocess(df):
    df = df.copy()
    for date_col in ["purchase_date", "roast_date"]:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.dayofyear
    for col in ["supplier", "origin_country", "variety", "process_method"]:
        df[col] = df[col].astype("category").cat.codes.replace(-1, np.nan)
    return df.fillna(df.mean(numeric_only=True))


def train_models(df):
    # --- Schema safety: ensure all expected columns exist ---
    for col in FEATURE_ORDER:
        if col not in df.columns:
            df[col] = np.nan
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # --- Coerce to numeric ---
    df[FEATURE_ORDER] = df[FEATURE_ORDER].apply(pd.to_numeric, errors="coerce")
    df[TARGET_COLUMNS] = df[TARGET_COLUMNS].apply(pd.to_numeric, errors="coerce")

    # --- Apply coverage threshold for features ---
    feature_threshold = ML_CONFIG["feature_coverage_threshold"]
    feature_coverage = df[FEATURE_ORDER].notna().mean()
    valid_features = feature_coverage[feature_coverage >= feature_threshold].index.tolist()
    X = df[valid_features].values

    # --- Impute missing features with column means ---
    col_means_X = np.nanmean(X, axis=0)
    inds_X = np.where(np.isnan(X))
    X[inds_X] = np.take(col_means_X, inds_X[1])

    # --- Apply coverage threshold for targets ---
    target_threshold = ML_CONFIG["target_coverage_threshold"]
    n_rows = df.shape[0]
    valid_targets = []
    for j, col in enumerate(TARGET_COLUMNS):
        non_nan_count = df[col].notna().sum()
        if n_rows > 0 and (non_nan_count / n_rows) >= target_threshold:
            valid_targets.append(True)
        else:
            valid_targets.append(False)

    valid_targets = np.array(valid_targets)
    Y = df[TARGET_COLUMNS].values[:, valid_targets]
    target_cols = [col for col, keep in zip(TARGET_COLUMNS, valid_targets) if keep]

    # --- Impute missing targets with column means ---
    col_means = np.nanmean(Y, axis=0)
    inds = np.where(np.isnan(Y))
    Y[inds] = np.take(col_means, inds[1])

    # --- Train/test split ---
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, random_state=42
    )

    # --- Model ---
    base_model = GradientBoostingRegressor(random_state=42)
    model = MultiOutputRegressor(base_model)
    model.fit(X_train, Y_train)

    # --- Evaluation ---
    preds = model.predict(X_test)
    mae = mean_absolute_error(Y_test, preds)
    print(f"✅ Multi-output model trained — overall MAE = {mae:.2f}")

    # Per-target MAE
    errors = np.abs(Y_test - preds)
    per_target_mae = errors.mean(axis=0)
    print("📉 Per-target MAE:")
    for col, err in zip(target_cols, per_target_mae):
        print(f"  {col:<25} {err:.2f}")

    # --- Save trained model ---
    save_path = TRAINED_MODELS_DIR / "ml_multi_output.pkl"
    joblib.dump(model, save_path)
    print(f"💾 Model saved to {save_path}")


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
