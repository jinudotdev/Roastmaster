import sys
import subprocess
from scripts.utilities.paths import ROAST_DATA

def launch_visidata():
    if not ROAST_DATA.exists():
        print(f"❌ roast_data.jsonl not found at {ROAST_DATA}")
        return

    try:
        subprocess.run([sys.executable, "-m", "visidata", str(ROAST_DATA)])
    except Exception as e:
        print(f"❌ Failed to launch VisiData: {e}")
