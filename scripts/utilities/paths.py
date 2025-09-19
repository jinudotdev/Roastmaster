# scripts/utilities/paths.py
from pathlib import Path

# Project root (two levels up from this file)
ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data" / "sessions"
MODELS_DIR = ROOT_DIR / "models"
TRAINED_MODELS_DIR = MODELS_DIR / "trained_models"
TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_DIR = ROOT_DIR / "scripts"
UTILITIES_DIR = SCRIPTS_DIR / "utilities"
