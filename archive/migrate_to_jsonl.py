"""
ARCHIVED SCRIPT — migrate_to_jsonl.py

Purpose:
One-time migration tool to convert legacy roast data into JSONL format.
legacy roasts were in json format, 1 file per roast inside /data/sessions. 
Relies on paths.py for canonical file locations.

Status:
Archived for reference. No longer used in active workflows.
Safe to run from any location as long as paths.py is intact.

Preserved for:
- Data format reference
- Potential reuse in future import/export utilities
"""

import json
from pathlib import Path

SESSIONS_DIR = Path("data/sessions")
OUT_FILE = Path("data/roast_data.jsonl")

def migrate():
    with OUT_FILE.open("w", encoding="utf-8") as out:
        for file in sorted(SESSIONS_DIR.glob("*.json")):
            raw = json.loads(file.read_text())
            raw["_source_file"] = file.name
            out.write(json.dumps(raw) + "\n")
    print(f"✅ Migrated {len(list(SESSIONS_DIR.glob('*.json')))} roasts into {OUT_FILE}")

if __name__ == "__main__":
    migrate()

