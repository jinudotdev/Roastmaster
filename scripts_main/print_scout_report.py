from scripts_utility.capture import seconds_to_mmss


def fmt_value(value, key=None, ml_filled_fields=None):
    if value is None:
        return "n/a"
    value_str = str(value)
    if ml_filled_fields is None:
        return value_str
    return f"\033[94m{value_str}\033[0m" if key in ml_filled_fields else value_str


def get_value(key, session_data, ml_filled_fields):
    return ml_filled_fields.get(key, session_data.get(key))


def print_scout_report(session_data, confidence, ml_filled_fields):
    print("\n--- Scout ML Prediction Results ---")
    print("\nYour Predicted Roast (Scout):\n")

    # --- Environment / Metadata ---
    for key, label in [
        ("process_method", "Process Method"),
        ("room_temp_f", "Room Temp"),
        ("humidity_pct", "Room Humidity"),
        ("room_bean_temp_f", "Room Bean Temp"),
        ("green_bean_moisture_pct", "Green Bean Moisture"),
        ("batch_weight_lbs", "Batch Weight"),
    ]:
        suffix = " lbs" if key == "batch_weight_lbs" else ""
        print(f"{label}: {fmt_value(get_value(key, session_data, ml_filled_fields), key, ml_filled_fields)}{suffix}")

    # --- Roast Stages ---
    for i in range(10):
        temp_key   = f"stage_{i}_temp_f"
        burner_key = f"stage_{i}_burner_pct"
        time_key   = f"stage_{i}_time_sec"

        temp   = get_value(temp_key, session_data, ml_filled_fields)
        burner = get_value(burner_key, session_data, ml_filled_fields)
        secs   = get_value(time_key, session_data, ml_filled_fields)
        time_str = seconds_to_mmss(secs) if isinstance(secs,(int,float)) else None

        print(
            f"Stage {i} - Temp: {fmt_value(round(temp,0) if isinstance(temp,(int,float)) else temp, temp_key, ml_filled_fields)} "
            f"- Burner: {fmt_value(round(burner,0) if isinstance(burner,(int,float)) else burner, burner_key, ml_filled_fields)} "
            f"- Time: {fmt_value(time_str, time_key, ml_filled_fields)}"
        )

        if i == 0:
            tp_temp = get_value("turning_point_temp_f", session_data, ml_filled_fields)
            tp_time = get_value("turning_point_time_sec", session_data, ml_filled_fields)
            tp_time_str = seconds_to_mmss(tp_time) if isinstance(tp_time,(int,float)) else None
            print(
                f"Turning Point - Temp: {fmt_value(round(tp_temp,0) if isinstance(tp_temp,(int,float)) else tp_temp, 'turning_point_temp_f', ml_filled_fields)} "
                f"- Time: {fmt_value(tp_time_str, 'turning_point_time_sec', ml_filled_fields)}"
            )
