from scripts.utilities.capture import seconds_to_mmss

def fmt_value(value, key=None, ml_filled_fields=None):
    if value is None:
        return "n/a"
    value_str = str(value)
    if ml_filled_fields is None:
        return value_str
    return f"\033[94m{value_str}\033[0m" if key in ml_filled_fields else value_str


def print_roast_report(session_data, confidence, ml_filled_fields):
    print("\n--- ML Prediction Results ---")
    print(confidence)
    print("\nYour Predicted Roast:\n")

    # --- Metadata ---
    for key, label in [
        ("supplier_name", "Supplier Name"),
        ("origin_country", "Origin"),
        ("altitude_meters", "Altitude"),
        ("variety", "Variety"),
        ("process_method", "Process")
    ]:
        print(f"{label}: {fmt_value(session_data.get(key), key, ml_filled_fields)}")

    # --- Bean Age ---
    if session_data.get("purchase_date") and session_data.get("roast_date"):
        age_days = (session_data["roast_date"] - session_data["purchase_date"]).days
        print(f"Bean Age in Days: {age_days}")

    for key, label in [
        ("room_temp_f", "Room Temp"),
        ("room_rh_pct", "Room Humidity"),
        ("bean_temp_pre_f", "Bean Temp"),
        ("green_bean_moisture_pct", "Bean Humidity"),
        ("batch_weight_lbs", "Batch Weight")
    ]:
        suffix = " lbs" if key == "batch_weight_lbs" else ""
        print(f"{label}: {fmt_value(session_data.get(key), key, ml_filled_fields)}{suffix}")

    # --- Roast Stages ---
    for stage in session_data["stages"]:
        i = stage["stage"]
        temp = stage.get("bean_temp")
        burner = stage.get("burner_pct")
        secs = stage.get("time_in_secs")

        time_str = seconds_to_mmss(secs) if secs is not None else None
        print(
            f"Stage {i} - Temp: {fmt_value(round(temp, 0) if temp is not None else None, f'stage_{i}_temp', ml_filled_fields)} "
            f"- Burner: {fmt_value(round(burner, 0) if burner is not None else None, f'burner_pct_{i}', ml_filled_fields)} "
            f"- Time: {fmt_value(time_str, f'time_in_secs_{i}', ml_filled_fields)}"
        )

        # Print Turning Point once, immediately after Stage 0
        if i == 0:
            tp_temp = session_data.get("turning_point_temp")
            tp_time = session_data.get("turning_point_time")

            # Suppress bogus 0.0 values
            tp_temp = None if tp_temp in (0, 0.0) else tp_temp
            tp_time = None if tp_time in (0, 0.0) else tp_time

            tp_time_str = seconds_to_mmss(tp_time) if tp_time is not None else None
            print(
                f"Turning Point - Temp: {fmt_value(round(tp_temp, 0) if tp_temp is not None else None, 'turning_point_temp', ml_filled_fields)} "
                f"- Time: {fmt_value(tp_time_str, 'turning_point_time', ml_filled_fields)}"
            )

    # --- End of Roast ---
    for key, label in [
        ("end_temp", "End of Roast"),
        ("agtron_whole", "Agtron"),
        ("moisture_post_pct", "Post Roast Moisture"),
    ]:
        value = session_data.get(key)
        if isinstance(value, (float, int)):
            value = round(float(value), 1)
        print(f"{label}: {fmt_value(value, key, ml_filled_fields)}")

    # --- Sensory Scores ---
    sensory = session_data.get("sensory_scores", {})
    for key, label in [
        ("clarity", "Clarity"),
        ("acidity", "Acidity"),
        ("body", "Body"),
        ("sweetness", "Sweetness"),
        ("overall", "Overall"),
        ("descriptors", "Comments")
    ]:
        print(f"{label}: {fmt_value(sensory.get(key), key, ml_filled_fields)}")
