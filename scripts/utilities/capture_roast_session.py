import json
from pathlib import Path
from datetime import date, datetime

OUT_FILE = Path("data/roast_data.jsonl")

def capture_roast_session(session_data, recapture_callback=None):
    """
    Validates, reviews, and saves a roast session.
    If the user rejects the data and recapture_callback is provided,
    it will call that function to re-enter the session.
    """

    while True:
        # --- Validation ---
        stages = session_data.get("stages", [])
        if len(stages) != 10:  # Stage 0 + Stages 1–9
            print(f"❌ ERROR: Expected 10 entries (Stage 0 + Stages 1–9), got {len(stages)}. Session NOT saved.")
            if recapture_callback:
                print("🔄 Let's try entering the roast again...")
                session_data = recapture_callback()
                continue
            return

        for s in stages:
            if "stage" not in s or "bean_temp" not in s or "burner_pct" not in s:
                print(f"❌ ERROR: Missing required data in stage {s.get('stage', '?')}. Session NOT saved.")
                if recapture_callback:
                    print("🔄 Let's try entering the roast again...")
                    session_data = recapture_callback()
                    continue
                return
            if s["stage"] != 0 and not isinstance(s["stage"], str) and s.get("time_in_secs") is None:
                print(f"❌ ERROR: Missing time for stage {s['stage']}. Session NOT saved.")
                if recapture_callback:
                    print("🔄 Let's try entering the roast again...")
                    session_data = recapture_callback()
                    continue
                return

        # --- Build lean features set ---
        weight_loss_lbs = session_data["batch_weight_lbs"] - session_data["post_roast_batch_weight_lbs"]
        weight_loss_kg = weight_loss_lbs * 0.453592
        weight_loss_pct = (weight_loss_lbs / session_data["batch_weight_lbs"]) * 100

        features = {
            "moisture_delta": round(session_data["green_bean_moisture_pct"] - (session_data["moisture_post_pct"] or 0), 2),
            "weight_loss_lbs": round(weight_loss_lbs, 2),
            "weight_loss_kg": round(weight_loss_kg, 5),
            "weight_loss_pct": round(weight_loss_pct, 2),
            "green_age_days": (
                (session_data["roast_date"].date() - session_data["purchase_date"].date()).days
                if session_data.get("purchase_date") else None
            ),
        }

        times = [s["time_in_secs"] for s in stages if isinstance(s.get("time_in_secs"), (int, float))]
        if times:
            features["total_roast_time_s"] = max(times)
            features["stage_durations_s"] = [j - i for i, j in zip(times, times[1:])]

        # add TP as a feature
        tp_time = session_data.get("turning_point_time")
        if tp_time is not None:
            features["time_to_tp_s"] = tp_time

        # --- Review (unchanged) ---
        # ... [all your printout code stays the same] ...

        # --- Confirmation ---
        confirm = input("Save this session? (y/n): ").strip().lower()
        if confirm == "y":
            OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            record = {"session_data": session_data, "features": features}
            with OUT_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=serialize) + "\n")
            print(f"💾 Session appended to {OUT_FILE}")
            return
        else:
            print("❌ Session NOT saved.")
            if recapture_callback:
                print("🔄 Let's try entering the roast again...")
                session_data = recapture_callback()
                continue

def serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return obj
