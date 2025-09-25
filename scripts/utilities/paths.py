import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Running as a PyInstaller .exe
    # Use the folder where the executable lives
    ROOT_DIR = Path(sys.executable).resolve().parent
else:
    # Running from source
    ROOT_DIR = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = ROOT_DIR / "data"
ROAST_DATA = DATA_DIR / "roast_data.jsonl"

# Models
MODELS_DIR = ROOT_DIR / "models"
TRAINED_MODELS_DIR = MODELS_DIR / "trained_models"
TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Scripts/utilities
SCRIPTS_DIR = ROOT_DIR / "scripts"
UTILITIES_DIR = SCRIPTS_DIR / "utilities"

# Ensure base data dir exists
DATA_DIR.mkdir(parents=True, exist_ok=True)