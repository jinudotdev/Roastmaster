import statistics
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

def print_core_report(session_data, confidence, ml_filled_fields):
    print("\nYour Predicted Roast:\n")

    # --- Confidence ---
    if confidence is not None and isinstance(confidence, dict):
        vals = list(confidence.values())
        mean = statistics.mean(vals)
        stdev = statistics.pstdev(vals)

        print("Raw confidence values:")
        for k, v in confidence.items():
            print(f"  {k}: {v:.3f}")

        print(f"\nStep 1: Mean = {mean:.3f}")
        print(f"Step 2: Std Dev = {stdev:.3f}")

        print("\nStep 3: Distance from mean for each value:")
        for k, v in confidence.items():
            print(f"  {k}: |{v:.3f} - {mean:.3f}| = {abs(v - mean):.3f}")

        inside = {k: v for k, v in confidence.items() if abs(v - mean) <= stdev}
        outside = {k: v for k, v in confidence.items() if abs(v - mean) > stdev}

        print("\nStep 4: Values within ±1σ:")
        for k, v in inside.items():
            print(f"  {k}: {v:.3f}")

        print("\nStep 5: Values excluded (outside ±1σ):")
        for k, v in outside.items():
            print(f"  {k}: {v:.3f}")

        filtered_mean = sum(inside.values()) / len(inside) if inside else mean
        print(f"\nStep 6: Filtered mean (±1σ) = {filtered_mean:.3f}\n")

    elif confidence is not None:
        # fallback if confidence is a single float
        print(f"Model Confidence: {confidence:.2f}\n")

    # --- Bean Summary Echo ---
    supplier = get_value("supplier", session_data, ml_filled_fields)
    country = get_value("country", session_data, ml_filled_fields)
    region = get_value("region", session_data, ml_filled_fields)
    variety = get_value("variety", session_data, ml_filled_fields)
    process = get_value("process_method", session_data, ml_filled_fields)
    altitude = get_value("altitude_meters", session_data, ml_filled_fields)
    purchase_date = get_value("purchase_date", session_data, ml_filled_fields)

    summary_parts = []
    if supplier: summary_parts.append(str(supplier))
    if country: summary_parts.append(str(country))
    if region: summary_parts.append(str(region))
    if variety: summary_parts.append(f"({variety}")
    if process: summary_parts[-1] = summary_parts[-1] + f", {process})" if variety else f"({process})"
    if altitude: summary_parts.append(f"{altitude}m")
    if purchase_date: summary_parts.append(f"purchased {purchase_date}")

    if summary_parts:
        print("Using: " + " – ".join(summary_parts) + "\n")

    # --- Metadata ---
    for key, label in [
        ("supplier", "Supplier Name"),
        ("country", "Country"),
        ("altitude_meters", "Altitude"),
        ("variety", "Variety"),
        ("region", "Region"),
    ]:
        print(f"{label}: {fmt_value(get_value(key, session_data, ml_filled_fields), key, ml_filled_fields)}")

    # --- Roast Date & Bean Age ---
    roast_day = get_value("roast_date", session_data, ml_filled_fields)
    bean_age = get_value("bean_age_days_at_roast", session_data, ml_filled_fields)

    if roast_day is not None:
        def season_from_day(day: int) -> str:
            if 80 <= day < 172:
                return "Spring"
            elif 172 <= day < 266:
                return "Summer"
            elif 266 <= day < 355:
                return "Fall"
            else:
                return "Winter"
        season = season_from_day(int(roast_day))
        print(f"Roast Day of Year: {fmt_value(roast_day, 'roast_date', ml_filled_fields)} ({season})")

    if bean_age is not None:
        print(f"Bean Age in Days: {fmt_value(bean_age, 'bean_age_days_at_roast', ml_filled_fields)}")

    # --- Environment ---
    for key, label in [
        ("room_temp_f", "Room Temp"),
        ("humidity_pct", "Room Humidity"),
        ("bean_temp_start_f", "Bean Temp"),
        ("green_bean_moisture_pct", "Bean Humidity"),
        ("batch_weight_lbs", "Batch Weight"),
    ]:
        suffix = " lbs" if key == "batch_weight_lbs" else ""
        print(f"{label}: {fmt_value(get_value(key, session_data, ml_filled_fields), key, ml_filled_fields)}{suffix}")

    # --- Roast Stages ---
    for i in range(10):
        temp_key = f"stage_{i}_temp_f"
        burner_key = f"stage_{i}_burner_pct"
        time_key = f"stage_{i}_time_sec"

        temp = get_value(temp_key, session_data, ml_filled_fields)
        burner = get_value(burner_key, session_data, ml_filled_fields)
        secs = get_value(time_key, session_data, ml_filled_fields)
        time_str = seconds_to_mmss(secs) if secs is not None else None

        print(
            f"Stage {i} - Temp: {fmt_value(round(temp, 0) if temp is not None else None, temp_key, ml_filled_fields)} "
            f"- Burner: {fmt_value(round(burner, 0) if burner is not None else None, burner_key, ml_filled_fields)} "
            f"- Time: {fmt_value(time_str, time_key, ml_filled_fields)}"
        )

        if i == 0:
            tp_temp = get_value("turning_point_temp_f", session_data, ml_filled_fields)
            tp_time = get_value("turning_point_time_sec", session_data, ml_filled_fields)
            tp_temp = None if tp_temp in (0, 0.0) else tp_temp
            tp_time = None if tp_time in (0, 0.0) else tp_time
            tp_time_str = seconds_to_mmss(tp_time) if tp_time is not None else None

            print(
                f"Turning Point - Temp: {fmt_value(round(tp_temp, 0) if tp_temp is not None else None, 'turning_point_temp_f', ml_filled_fields)} "
                f"- Time: {fmt_value(tp_time_str, 'turning_point_time_sec', ml_filled_fields)}"
            )

    # --- End of Roast ---
    for key, label in [
        ("end_temp_f", "End of Roast"),
        ("agtron", "Agtron"),
        ("roasted_bean_moisture_pct", "Post Roast Moisture"),
    ]:
        value = get_value(key, session_data, ml_filled_fields)
        if isinstance(value, (float, int)):
            value = round(float(value), 1)
        print(f"{label}: {fmt_value(value, key, ml_filled_fields)}")

    # --- Sensory Scores ---
    for key, label in [
        ("clarity", "Clarity"),
        ("acidity", "Acidity"),
        ("body", "Body"),
        ("sweetness", "Sweetness"),
        ("overall_rating", "Overall"),
        ("comments", "Comments"),
    ]:
        print(f"{label}: {fmt_value(get_value(key, session_data, ml_filled_fields), key, ml_filled_fields)}")
