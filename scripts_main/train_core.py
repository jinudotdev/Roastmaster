"""
Long-Form Trainer — trains one CatBoost model per optional field with data
from roast logs in data/sessions/ and saves them into models/.
It uses more features than Scout, so it'll take more data to train effectively.
"""

import json
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Centralized paths
from scripts_utility.paths import DATA_FILE, CORE_MODEL_PATH
from scripts_utility.master_order import CORE_FEATURE_ORDER, CORE_PREDICTABLES 

# --- Schema introspection ---
from dataclasses import fields
from typing import get_origin, Optional
from scripts_utility.schema import RoastSession

# Dynamic thresholds
from scripts_main.train_core_config import get_thresholds

DATE_COLS = ["purchase_date", "roast_date"]
CATEGORICAL_COLS = ["supplier", "country", "region", "variety", "process_method"]  # agtron removed

# --- Load CSV data ---
def load_roast_data():
    csv_file = DATA_FILE.with_suffix(".csv")
    if not csv_file.exists():
        print(f"❌ {csv_file} not found.")
        return pd.DataFrame()
    return pd.read_csv(csv_file)

# --- Preprocess ---
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Parse dates as real datetimes first
    if "roast_date" in df.columns:
        df["roast_date"] = pd.to_datetime(df["roast_date"], errors="coerce")

    if "purchase_date" in df.columns:
        df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")

    if "purchase_date" in df.columns and "roast_date" in df.columns:
        roast_dt = pd.to_datetime(df["roast_date"], errors="coerce")
        purchase_dt = pd.to_datetime(df["purchase_date"], errors="coerce")
        df["bean_age_days_at_roast"] = (roast_dt - purchase_dt).dt.days

    if "roast_date" in df.columns:
        roast_dt = pd.to_datetime(df["roast_date"], errors="coerce")
        df["roast_date"] = roast_dt.dt.dayofyear

    # Handle categoricals
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("NaN").replace("nan", "NaN")

    return df


# --- ML builder ---
def train_core(df):
    
    # Ensure model directory exists (fresh machine safety)
    CORE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Ensure all expected features exist
    for col in CORE_FEATURE_ORDER:
        if col not in df.columns:
            df[col] = np.nan

    # Get dynamic thresholds based on dataset size
    rows = len(df)
    feature_thresh, target_thresh = get_thresholds(rows)
    print(f"📊 Using thresholds — features: {feature_thresh:.2f}, targets: {target_thresh:.2f}")

    # Apply feature coverage threshold
    valid_features, dropped_features = [], []
    for col in CORE_FEATURE_ORDER:
        coverage = df[col].notna().mean()
        if coverage >= feature_thresh:
            valid_features.append(col)
        else:
            dropped_features.append(col)

    if dropped_features:
        print(f"⚠️ Dropped {len(dropped_features)} low‑coverage features: {', '.join(dropped_features)}")

    models, metrics, trained_targets = {}, {}, []

    for col in CORE_PREDICTABLES:
        coverage = df[col].notna().mean()
        if coverage < target_thresh:
            print(f"⚠️ Skipping {col}: insufficient coverage ({coverage:.0%})")
            continue

        df_target = df[[col] + valid_features].dropna(subset=[col])
        y = df_target[col]
        if isinstance(y, pd.DataFrame):
            y = y.iloc[:, 0]
        X = df_target[valid_features]

        if y.nunique() <= 1:
            print(f"⚠️ Skipping {col}: target has no variance")
            continue

        # Reindex to ensure alignment
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Deduplicate columns
        X_train = X_train.loc[:, ~X_train.columns.duplicated()]
        X_test = X_test.loc[:, ~X_test.columns.duplicated()]

        # Drop NaNs in y_train
        non_nan_mask = ~y_train.isna()
        if non_nan_mask.sum() < len(y_train):
            print(f"⚠️ Dropped {len(y_train) - non_nan_mask.sum()} NaN rows from y_train for {col}")
        X_train = X_train.loc[non_nan_mask]
        y_train = y_train.loc[non_nan_mask]

        if y_train.nunique() <= 1:
            print(f"⚠️ Skipping {col}: target has no variance (train split)")
            continue

        try:
            # CatBoost expects categorical indices, not names
            cat_features = [i for i, c in enumerate(X_train.columns) if c in CATEGORICAL_COLS]

            model = CatBoostRegressor(
                iterations=500,
                depth=8,
                learning_rate=0.05,
                cat_features=cat_features,
                verbose=0
            )

            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            mae = mean_absolute_error(y_test, preds)
            metrics[col] = mae
            print(f"✅ {col}: MAE={mae:.3f}")

            model_path = CORE_MODEL_PATH.with_name(f"{col}_catboost.cbm")
            model.save_model(model_path)
            models[col] = str(model_path)
            trained_targets.append(col)

        except Exception as e:
            print(f"❌ Skipped {col}: {str(e).splitlines()[-1]}")
            continue

    # Save metadata with only valid features + trained targets
    meta = {
        "feature_order": valid_features,
        "categorical_cols": CATEGORICAL_COLS,
        "predictables": trained_targets,
        "models": models,
        "metrics": metrics,
        "thresholds": {
            "feature_threshold": feature_thresh,
            "target_threshold": target_thresh
        },
    }
    meta_path = CORE_MODEL_PATH.with_name("ml_catboost_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print("🧾 Final feature set:", valid_features)
    print("🎯 Trained targets:", trained_targets)
    print(f"💾 Metadata saved to {meta_path}")
    print(f"📊 Summary: trained {len(models)} models, skipped {len(CORE_PREDICTABLES) - len(models)}")

# --- Main ---
def main():
    print("📦 Loading roast data...")
    df = load_roast_data()
    if df.empty:
        print("❌ No roast logs found.")
        return
    print("🛠 Preprocessing...")
    df = preprocess(df)
    print("🤖 Training CatBoost models...")
    train_core(df)
    print("✅ Training complete.")

if __name__ == "__main__":
    main()
