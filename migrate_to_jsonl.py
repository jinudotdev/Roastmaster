# migrate_to_jsonl.py
import json
from pathlib import Path

SESSIONS_DIR = Path("data/sessions")
OUT_FILE = Path("data/roast_data.jsonl")

def migrate():
    with OUT_FILE.open("w", encoding="utf-8") as out:
        for file in sorted(SESSIONS_DIR.glob("*.json")):
            raw = json.loads(file.read_text())
            # keep original filename for traceability if you want
            raw["_source_file"] = file.name
            out.write(json.dumps(raw) + "\n")
    print(f"✅ Migrated {len(list(SESSIONS_DIR.glob('*.json')))} roasts into {OUT_FILE}")

if __name__ == "__main__":
    migrate()

