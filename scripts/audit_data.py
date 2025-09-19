import json
import pandas as pd
import dtale
from scripts.utilities.paths import DATA_DIR

def audit_data():
    session_files = list(DATA_DIR.glob("*.json"))
    if not session_files:
        print(f"No session files found in {DATA_DIR}")
        return

    records = []
    file_map = []  # track which row came from which file

    for file in session_files:
        with open(file, "r") as f:
            raw = json.load(f)

        s = raw.get("session_data", {})
        ftrs = raw.get("features", {})

        record = {
            "roast_date": s.get("roast_date"),
            "bean_id": s.get("bean_id"),
            "origin_country": s.get("origin_country"),
            "altitude_meters": s.get("altitude_meters"),
            "variety": s.get("variety"),
            "process_method": s.get("process_method"),
            "batch_weight_kg": s.get("batch_weight_kg"),
            "post_roast_batch_weight_kg": s.get("post_roast_batch_weight_kg"),
            "end_temp": s.get("end_temp"),
            "agtron_whole": s.get("agtron_whole"),
            "moisture_post_pct": s.get("moisture_post_pct"),
            "weight_loss_pct": ftrs.get("weight_loss_pct"),
            "total_roast_time_s": ftrs.get("total_roast_time_s"),
        }
        records.append(record)
        file_map.append(file)

    if not records:
        print("No valid session data found.")
        return

    df = pd.DataFrame(records)

    # 🚀 Open Dtale in browser for editing
    d = dtale.show(df, editable=True)
    d.open_browser()

    input("\nPress Enter here after closing the Dtale browser tab...")

    # Grab the edited DataFrame
    edited_df = d.data.copy()

    # --- Dry run preview ---
    changes_detected = False
    for i, row in edited_df.iterrows():
        file = file_map[i]
        with open(file, "r") as f:
            raw = json.load(f)

        s = raw["session_data"]
        ftrs = raw["features"]

        updated = {
            "bean_id": row["bean_id"],
            "origin_country": row["origin_country"],
            "altitude_meters": row["altitude_meters"],
            "variety": row["variety"],
            "process_method": row["process_method"],
            "batch_weight_kg": row["batch_weight_kg"],
            "post_roast_batch_weight_kg": row["post_roast_batch_weight_kg"],
            "end_temp": row["end_temp"],
            "agtron_whole": row["agtron_whole"],
            "moisture_post_pct": row["moisture_post_pct"],
            "weight_loss_pct": row["weight_loss_pct"],
            "total_roast_time_s": row["total_roast_time_s"],
        }

        for k, v in updated.items():
            old_val = s.get(k) if k in s else ftrs.get(k)
            if old_val != v:
                if not changes_detected:
                    print("\n--- DRY RUN: Proposed changes ---")
                    changes_detected = True
                print(f"{file.name} | {k}: {old_val} → {v}")

    if not changes_detected:
        print("\nNo changes detected. Nothing to save.")
        return

    # --- Confirmation prompt ---
    confirm = input("\nSave these edits to JSON files? (y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Edits discarded. No files modified.")
        return

    # --- Commit changes ---
    for i, row in edited_df.iterrows():
        file = file_map[i]
        with open(file, "r") as f:
            raw = json.load(f)

        s = raw["session_data"]
        ftrs = raw["features"]

        for k in ["bean_id","origin_country","altitude_meters","variety",
                  "process_method","batch_weight_kg","post_roast_batch_weight_kg",
                  "end_temp","agtron_whole","moisture_post_pct"]:
            s[k] = row[k]

        ftrs["weight_loss_pct"] = row["weight_loss_pct"]
        ftrs["total_roast_time_s"] = row["total_roast_time_s"]

        with open(file, "w") as f:
            json.dump(raw, f, indent=2)

    print(f"\n✅ Saved edits back to {len(file_map)} JSON files")
