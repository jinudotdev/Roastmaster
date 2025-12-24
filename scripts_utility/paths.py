# scripts_utility/paths.py
import sys
from pathlib import Path

# Detect root directory (works for frozen executables and normal scripts)
if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
else:
    ROOT_DIR = Path(__file__).resolve().parents[1]

# Data
DATA_FILE: Path = ROOT_DIR / "data" / "roast_data.csv"

# Base models directory
MODELS_DIR: Path = ROOT_DIR / "models"

# Subdirectories for Core and Scout
CORE_MODELS_DIR: Path = MODELS_DIR / "core"
SCOUT_MODELS_DIR: Path = MODELS_DIR / "scout"

# Canonical model file paths
CORE_MODEL_PATH: Path = CORE_MODELS_DIR / "core_model.pkl"
SCOUT_MODEL_PATH: Path = SCOUT_MODELS_DIR / "scout_model.pkl"
