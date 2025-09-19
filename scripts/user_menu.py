from datetime import datetime
from scripts.run_model_session import run_model_session
from scripts.utilities.capture import (
    get_optional_choice,
    get_validated_date,
    get_valid_time,
    get_validated_input,
    get_optional_validated_input
)

def menu_session():
    # --- Bean Metadata ---
    supplier_name = get_optional_validated_input("Supplier: ", str)
    origin_country = get_optional_validated_input("Origin Country: ", str)
    altitude_meters = get_optional_validated_input("Altitude (meters): ", int, 0, 4000)
    variety = get_optional_validated_input("Variety: ", str)
    process_choices = {
        "1": "Natural",
        "2": "Washed",
        "3": "Honey",
        "4": "Wet-Hulled",
        "5": "Other"
    }
    process_method = get_optional_choice("Process Method:", process_choices)
    purchase_date = get_validated_date("Purchase Date (MM/DD/YYYY, MM/DD/YY, or YYYY-MM-DD): ", allow_blank=True)
    roast_date = get_validated_date("Roast Date (MM/DD/YYYY, MM/DD/YY, or YYYY-MM-DD) [Enter for today]: ", allow_blank=True) or datetime.today()

    room_temp = get_optional_validated_input("Room Temp (°F): ", float)
    humidity = get_optional_validated_input("Humidity (%): ", float)
    bean_temp_start = get_optional_validated_input("Starting Bean Temp (°F): ", float)
    green_bean_moisture = get_optional_validated_input("Green Bean Moisture (%): ", float)

    # --- Pre-roast batch weight ---
    batch_weight_lbs = get_validated_input("Batch Weight (lbs): ", float, min_val=150)
    batch_weight_kg = batch_weight_lbs * 0.453592

    # --- Post-roast batch weight ---
    post_roast_batch_weight_lbs = get_validated_input(
        f"Post-Roast Batch Weight (lbs) [must be less than {batch_weight_lbs}]: ",
        float,
        min_val=batch_weight_lbs*0.5,
        max_val=batch_weight_lbs - 0.0001
    )
    post_roast_batch_weight_kg = post_roast_batch_weight_lbs * 0.453592

    stages = []

    # Stage 0 - Charge
    print("\nStage 0 - Charge time is 00:00")
    stage_temp = get_validated_input("Stage 0 - Bean Temp (°F): ", float, 200, 500)
    burner_pct = get_validated_input("Stage 0 - Burner %: ", float, 0, 100)
    stages.append({"stage": 0, "time_in_secs": 0, "bean_temp": stage_temp, "burner_pct": burner_pct})

    # Turning Point
    print("\nTurning Point")
    tp_time_in_secs = get_valid_time("Time (MMSS, e.g. 1230 for 12:30): ")
    tp_temp = get_validated_input("Turning Point - Bean Temp (°F): ", float, 200, 500)

    # Stages 1–9
    later_stages = []
    for stage_num in range(1, 10):
        print(f"\nStage {stage_num}")
        stage_time_in_secs = get_valid_time("Time (MMSS, e.g. 1230 for 12:30): ")
        bean_temp = get_validated_input(f"Stage {stage_num} - Bean Temp (°F): ", float, 200, 500)
        burner_pct = get_validated_input(f"Stage {stage_num} - Burner %: ", float, 0, 100)
        later_stages.append({"stage": stage_num, "time_in_secs": stage_time_in_secs, "bean_temp": bean_temp, "burner_pct": burner_pct})

    stages.extend(later_stages)

    # End of roast
    print("\nEnd of Roast")
    stage_9_temp = later_stages[-1]
    while True:
        end_temp = get_validated_input("End Temp (°F): ", float)
        if end_temp > stage_9_temp["bean_temp"]:
            break
        print(f"⚠️ End Temp must be greater than Stage 9 temp ({stage_9_temp['bean_temp']}°F). Try again.")

    agtron_score = get_optional_validated_input("Agtron Score (optional): ", float, 0, 100)
    moisture_pct = get_optional_validated_input("Ending Moisture % (optional): ", float, 0, 10)

    # --- Sensory Scores ---
    print("\nSensory Scores (optional, 1–10)")
    sensory_kwargs = {
        "clarity": get_optional_validated_input("Clarity (1-10): ", int),
        "acidity": get_optional_validated_input("Acidity (1-10): ", int),
        "body": get_optional_validated_input("Body (1-10): ", int),
        "sweetness": get_optional_validated_input("Sweetness (1-10): ", int),
        "overall": get_optional_validated_input("Overall (1-10): ", int),
        "descriptors": get_optional_validated_input("Comments: ", str)
    }
    if sensory_kwargs["descriptors"]:
        sensory_kwargs["descriptors"] = sensory_kwargs["descriptors"].lower()

    # --- Final session dict ---
    session_data = {
        "roast_date": roast_date,
        "supplier_name": supplier_name,
        "origin_country": origin_country,
        "altitude_meters": altitude_meters,
        "variety": variety,
        "process_method": process_method,
        "purchase_date": purchase_date,
        "room_temp_f": room_temp,
        "room_rh_pct": humidity,
        "bean_temp_pre_f": bean_temp_start,
        "green_bean_moisture_pct": green_bean_moisture,
        "batch_weight_lbs": batch_weight_lbs,
        "batch_weight_kg": batch_weight_kg,
        "post_roast_batch_weight_lbs": post_roast_batch_weight_lbs,
        "post_roast_batch_weight_kg": post_roast_batch_weight_kg,
        "stages": stages,
        "turning_point_temp": tp_temp,
        "turning_point_time": tp_time_in_secs,
        "end_temp": end_temp,
        "agtron_whole": agtron_score,
        "moisture_post_pct": moisture_pct,
        "sensory_scores": sensory_kwargs
    }

    return session_data

def predict_mode():
    # Reuse menu_session to collect the same roast data
    run_model_session()