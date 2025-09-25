import numpy as np
from datetime import datetime

def time_to_sec(t):
    return int(t.split(":")[0]) * 60 + int(t.split(":")[1])

def extract_features(session_data):
    stages = session_data["stages"]

    # Separate numeric stages and TP
    numeric_stages = [s for s in stages if isinstance(s["stage"], int)]
    tp_stage = next(
        (s for s in stages if isinstance(s["stage"], str) and s["stage"].lower() in ["tp", "turning point"]),
        None
    )

    # Average bean temp across numeric stages
    avg_temp = sum(s["bean_temp"] for s in numeric_stages) / len(numeric_stages)

    # Burner % changes
    burner_changes = sum(
        1 for i in range(1, len(numeric_stages))
        if numeric_stages[i]["burner_pct"] != numeric_stages[i - 1]["burner_pct"]
    )

    # TP deltas (if TP exists)
    tp_delta_temp = None
    tp_delta_time = None
    if tp_stage:
        stage0 = next(s for s in stages if s["stage"] == 0)
        tp_delta_temp = tp_stage["bean_temp"] - stage0["bean_temp"]
        tp_delta_time = time_to_sec(tp_stage["time"]) - time_to_sec(stage0["time"])

    # Stage durations and total roast time
    stage_times_s = [time_to_sec(s["time"]) for s in numeric_stages]
    stage_durations_s = [
        stage_times_s[i] - stage_times_s[i - 1]
        for i in range(1, len(stage_times_s))
    ]
    total_roast_time_s = stage_times_s[-1] if stage_times_s else None

    # Green coffee age
    green_age_days = None
    if session_data.get("purchase_date"):
        try:
            roast_date = session_data["roast_date"]
            green_age_days = (roast_date - session_data["purchase_date"]).days
        except Exception:
            green_age_days = None

    # Moisture delta
    moisture_delta = None
    if "green_bean_moisture_pct" in session_data and "moisture_post_pct" in session_data:
        try:
            moisture_delta = session_data["green_bean_moisture_pct"] - session_data["moisture_post_pct"]
        except TypeError:
            moisture_delta = None

    altitude_m = session_data.get("altitude_meters")
    origin_country = session_data.get("origin_country")
    process_method = session_data.get("process_method")
    batch_weight_kg = session_data.get("batch_weight_kg")

    return {
        "avg_temp": avg_temp,
        "burner_changes": burner_changes,
        "tp_delta_temp": tp_delta_temp,
        "tp_delta_time_s": tp_delta_time,
        "end_temp": session_data["end_temp"],  # replaced end_peak_temp
        "moisture_delta": moisture_delta,
        "altitude_m": altitude_m,
        "origin_country": origin_country,
        "process_method": process_method,
        "batch_weight_kg": batch_weight_kg,  # for ML
        "green_age_days": green_age_days,
        "stage_durations_s": stage_durations_s,
        "total_roast_time_s": total_roast_time_s,
    }
