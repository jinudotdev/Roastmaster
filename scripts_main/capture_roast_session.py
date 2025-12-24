# scripts_utility/capture_roast_session.py

import csv
import uuid
from datetime import date, datetime
from typing import Any, Callable, Dict, Optional

from scripts_utility.paths import DATA_FILE
from scripts_utility.master_order import MASTER_ORDER


def capture_roast_session(
    session_data: Dict[str, Any],
    recapture_callback: Optional[Callable[[], Dict[str, Any]]] = None
) -> None:
    """
    Validates, reviews, and saves a roast session to a CSV file.
    Always writes columns in MASTER_ORDER.
    Missing values are written as 'NaN' so pandas can parse them as np.nan.
    Adds a line_number and id automatically if present in MASTER_ORDER.
    """

    csv_file = DATA_FILE.with_suffix(".csv")

    while True:
        confirm = input("Save this session? (y/n): ").strip().lower()
        if confirm != "y":
            print("❌ Session NOT saved.")
            if recapture_callback:
                print("🔄 Let's try entering the roast again...")
                session_data = recapture_callback()
                continue
            return

        # How many existing data rows (excluding header)?
        if csv_file.exists():
            with csv_file.open("r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f) - 1  # subtract header
        else:
            line_count = 0

        # Inject line_number if schema has it
        if "line_number" in MASTER_ORDER and not session_data.get("line_number"):
            session_data["line_number"] = line_count + 1

        # Inject id if schema has it
        if "id" in MASTER_ORDER and not session_data.get("id"):
            session_data["id"] = str(uuid.uuid4())

        # Flatten in MASTER_ORDER, forcing NaN for missing/blank
        safe_record: Dict[str, str] = {}
        for field in MASTER_ORDER:
            val = session_data.get(field, "NaN")
            if val in (None, ""):
                safe_record[field] = "NaN"
            else:
                safe_record[field] = str(val)

        if len(safe_record) != len(MASTER_ORDER):
            print(f"⚠️ Record has {len(safe_record)} fields, expected {len(MASTER_ORDER)}. Aborting write.")
            return

        # Write row
        file_exists = csv_file.exists()
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        with csv_file.open("a", newline="\n", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=MASTER_ORDER, delimiter=",")
            if not file_exists:
                writer.writeheader()
            writer.writerow(safe_record)

        print(f"💾 Session appended to {csv_file} as line {line_count + 1}")
        return
