# gui/gui_paths.py

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROAST_FILE = os.path.join(BASE_DIR, "data", "roast_data.csv")
INV_FILE = os.path.join(BASE_DIR, "data", "coffee_inventory.csv")
