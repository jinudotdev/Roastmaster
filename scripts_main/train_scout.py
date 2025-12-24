# scripts_main/train_scout.py

import os
import pandas as pd
import joblib
from catboost import CatBoostRegressor

from scripts_utility.master_order import (
    SCOUT_FEATURE_ORDER,
    SCOUT_PREDICTABLES,
    SCOUT_CATEGORICAL_COLS,
)
from scripts_utility.paths import SCOUT_MODEL_PATH, DATA_FILE


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stub for any future Scout preprocessing.
    Right now we just return the dataframe as-is.
    """
    return df


def train_scout(X: pd.DataFrame, y: pd.DataFrame) -> dict:
    models: dict = {}
    X = X.reset_index(drop=True)

    for target in y.columns:
        y_target = pd.to_numeric(y[target], errors="coerce").reset_index(drop=True)
        mask = y_target.notna().to_numpy()
        X_train, y_train = X.loc[mask], y_target.loc[mask]

        unique_vals = y_train.unique()

        if len(y_train) >= 3 and len(unique_vals) > 1:
            cat_features = [
                i for i, col in enumerate(X_train.columns)
                if col in SCOUT_CATEGORICAL_COLS
            ]
            model = CatBoostRegressor(
                iterations=200,
                depth=6,
                learning_rate=0.1,
                loss_function="MAE",
                verbose=False,
            )
            model.fit(X_train, y_train, cat_features=cat_features)
            models[target] = ("catboost", model)
            print(f"✅ Trained CatBoost for {target} on {len(y_train)} samples")
        elif len(y_train) > 0:
            models[target] = ("mean", y_train.mean())
            print(f"⚠️ Fallback mean for {target} (n={len(y_train)})")
        else:
            print(f"❌ Skipped {target} (no data)")

    return models


def main():
    # 1. Load roast data from the canonical path
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Roast data CSV not found at: {DATA_FILE}")

    print(f"📄 Loading roast data from {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)

    # 2. Preprocess (if needed later)
    df = preprocess(df)

    # 3. Split into features and targets
    X = df[SCOUT_FEATURE_ORDER].copy()
    y = df[SCOUT_PREDICTABLES].copy()

    # 4. Train models
    models = train_scout(X, y)

    # 5. Ensure models/scout directory exists
    SCOUT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 6. Save payload
    payload = {
        "models": models,
        "feature_columns": list(X.columns),
    }
    joblib.dump(payload, SCOUT_MODEL_PATH)
    print(f"✅ Scout models trained and saved to {SCOUT_MODEL_PATH}")


if __name__ == "__main__":
    main()
