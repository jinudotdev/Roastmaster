import json
from pathlib import Path
from datetime import date, datetime

def save_session(session_data, recapture_callback=None):
    """
    Saves a roast session after validation and user confirmation.
    If the user rejects the data and recapture_callback is provided,
    it will call that function to re-enter the session.
    """

    while True:
        # --- Validation ---
        stages = session_data.get("stages", [])
        if len(stages) != 11:  # Stage 0 + TP + Stages 1–9
            print(f"❌ ERROR: Expected 11 entries (Stage 0, TP, Stages 1–9), got {len(stages)}. Session NOT saved.")
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
            if isinstance(s["stage"], str) and s["stage"].lower() in ["tp", "turning point"] and s.get("time_in_secs") is None:
                print("❌ ERROR: Missing time for Turning Point. Session NOT saved.")   
                if recapture_callback:
                    print("🔄 Let's try entering the roast again...")
                    session_data = recapture_callback()
                    continue
                return

        # --- Build lean features set ---
        weight_loss_lbs = session_data["batch_weight_lbs"] - session_data["post_roast_batch_weight_lbs"]
        weight_loss_kg = weight_loss_lbs * 0.453592
        weight_loss_pct = (weight_loss_lbs / session_data["batch_weight_lbs"]) * 100

        # base features
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

        # conditional features
        times = [s["time_in_secs"] for s in stages if isinstance(s.get("time_in_secs"), (int, float))]
        # you add one at a time to append, if you do it in a list comprehension it makes a nested list
        if times:
            features["total_roast_time_s"] = max(times)
            features["stage_durations_s"] = [j - i for i, j in zip(times, times[1:])]

        # --- Review ---
        print("\n📋 Roast Session Review")
        print("=" * 50)
        print(f"Roast Date: {session_data['roast_date']}")
        print(f"Batch Weight: {session_data['batch_weight_lbs']} lbs / {session_data['batch_weight_kg']:.3f} kg")
        print(f"Post-Roast Weight: {session_data['post_roast_batch_weight_lbs']} lbs / {session_data['post_roast_batch_weight_kg']:.3f} kg")
        print(f"Room Temp: {session_data['room_temp_f']}°F")
        print(f"Humidity: {session_data['room_rh_pct']}%")
        print(f"Starting Bean Temp: {session_data['bean_temp_pre_f']}°F")
        print(f"Green Bean Moisture: {session_data['green_bean_moisture_pct']}%")
        print(f"Bean ID: {session_data['supplier_name']}")
        print(f"Origin Country: {session_data['origin_country']}")
        print(f"Altitude: {session_data['altitude_meters']} m")
        print(f"Variety: {session_data['variety']}")
        print(f"Process Method: {session_data['process_method']}")
        print("-" * 50)
        print(f"{'Stage':<14} {'Time':<8} {'Bean Temp (°F)':<16} {'Burner %':<10}")
        print("-" * 50)

        def stage_sort_key(s):
            if s["stage"] == 0:
                return (0, "")
            if isinstance(s["stage"], str) and s["stage"].lower() in ["tp", "turning point"]:
                return (1, "")
            return (2, s["stage"])

        for s in sorted(stages, key=stage_sort_key):
            stage_label = "Turning Point" if isinstance(s["stage"], str) else f"Stage {s['stage']}"
            secs = s.get("time_in_secs")
            time_str = f"{secs//60:02d}:{secs%60:02d}" if secs is not None else "—"
            
            print(f"{stage_label:<14} {time_str:<8} {s['bean_temp']:<16} {s['burner_pct']:<10}")    
        
        print("-" * 50)
        print(f"End Temp: {session_data['end_temp']}°F")
        print(f"Agtron Whole: {session_data['agtron_whole']}")
        print(f"Post-Roast Moisture: {session_data['moisture_post_pct']}%")
        print("=" * 50)
        print("Computed Features:")
        for k, v in features.items():
            print(f"  {k}: {v}")
        print("=" * 50)

        # --- Confirmation ---
        confirm = input("Save this session? (y/n): ").strip().lower()
        if confirm == "y":
            sessions_dir = Path("data/sessions")
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Safe roast_date handling
            roast_date_val = session_data["roast_date"]
            if isinstance(roast_date_val, datetime):
                roast_date_obj = roast_date_val
            elif isinstance(roast_date_val, date):
                roast_date_obj = datetime.combine(roast_date_val, datetime.min.time())
            else:
                try:
                    roast_date_obj = datetime.strptime(str(roast_date_val), "%Y-%m-%d")
                except ValueError:
                    roast_date_str = str(roast_date_val).replace(" ", "_")
                    filename = sessions_dir / f"session_{roast_date_str}_{session_data['supplier_name']}.json"
                    record = {"session_data": session_data, "features": features}
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(record, f, indent=4, default=serialize)
                    print(f"💾 Session written to {filename}")
                    return

            roast_date_str = roast_date_obj.strftime("%Y-%m-%d")
            filename = sessions_dir / f"session_{roast_date_str}_{session_data['supplier_name']}.json"

            record = {
                "session_data": session_data,
                "features": features
            }

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=4, default=serialize)

            print(f"💾 Session written to {filename}")
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
