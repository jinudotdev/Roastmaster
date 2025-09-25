from datetime import datetime
from scripts.utilities.capture import (
    get_optional_choice,
    get_validated_date,
    get_validated_input,
    get_optional_validated_input,
    get_valid_time,
    get_optional_valid_time
)
from models.ml import flatten_data, predict_with_ml
from scripts.utilities.print_model_output import print_roast_report

def run_model_session() -> None:
    # --- Bean Metadata ---
    supplier_name = get_optional_validated_input("Supplier [Optional]: ", str)
    origin_country = get_optional_validated_input("Origin Country [Optional]: ", str)
    altitude_meters = get_optional_validated_input("Altitude (meters) [Optional]: ", int, 0, 4000)
    variety = get_optional_validated_input("Variety [Optional]: ", str)
    process_method = get_optional_choice("Process Method [Optional]:", {
        "1": "Natural", "2": "Washed", "3": "Honey", "4": "Wet-Hulled", "5": "Other"
    })
    purchase_date = get_validated_date("Purchase Date [Optional]: ", allow_blank=True)
    roast_date = get_validated_date("Roast Date [Blank = Today]: ", allow_blank=True) or datetime.today()

    room_temp = get_optional_validated_input("Room Temp (°F) [Optional]: ", float)
    humidity = get_optional_validated_input("Humidity (%) [Optional]: ", float)
    bean_temp_start = get_optional_validated_input("Starting Bean Temp (°F) [Optional]: ", float)
    green_bean_moisture = get_optional_validated_input("Green Bean Moisture (%) [Optional]: ", float)

    batch_weight_lbs = get_validated_input("Batch Weight (lbs) [Required]: ", float, min_val=150)
    batch_weight_kg = batch_weight_lbs * 0.453592

    # --- Roast Stages ---
    stages = []

    # Stage 0 - Charge
    print("\nStage 0 - at Charge (time is always 00:00)")
    stages.append({
        "stage": 0,
        "time_in_secs": 0,
        "bean_temp": get_optional_validated_input("Stage 0 - Bean Temp (°F): ", float, 200, 500),
        "burner_pct": get_optional_validated_input("Stage 0 - Burner %: ", float, 0, 100)
    })

    # Turning Point
    print("\nTurning Point")
    tp_temp = get_optional_validated_input("Turning Point - Bean Temp (°F): ", float, 200, 500)
    tp_time_in_secs = get_optional_valid_time("Turning Point - Time (MMSS, e.g. 1230 for 12:30): ")

    # Stages 1–9
    for i in range(1, 10):
        print(f"\nStage {i}")
        if i == 9:
            # stricter validation for final temp
            bean_temp = get_validated_input("Stage 9 - Bean Temp (°F): ", float, 380, 500)
        else:
            bean_temp = get_optional_validated_input(f"Stage {i} - Bean Temp (°F): ", float, 200, 500)
        burner_pct = get_optional_validated_input(f"Stage {i} - Burner %: ", float, 0, 100)
        stage_time_in_secs = get_optional_valid_time("Time (MMSS, e.g. 1230 for 12:30): ")
        stages.append({
            "stage": i,
            "time_in_secs": stage_time_in_secs,
            "bean_temp": bean_temp,
            "burner_pct": burner_pct
        })


    # --- Sensory Scores ---
    print("\nSensory Scores (optional, 1–10)")
    sensory_scores = {
        key: get_optional_validated_input(f"{label}: ", int)
        for key, label in [
            ("clarity", "Clarity"), ("acidity", "Acidity"), ("body", "Body"),
            ("sweetness", "Sweetness"), ("overall", "Overall")
        ]
    }
    sensory_scores["descriptors"] = get_optional_validated_input("Comments: ", str)
    if sensory_scores["descriptors"]:
        sensory_scores["descriptors"] = sensory_scores["descriptors"].lower()

    # --- Session Assembly ---
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
        "stages": stages,  # strictly 0–9
        "turning_point_temp": tp_temp,
        "turning_point_time": tp_time_in_secs,
        "end_temp": None,
        "agtron_whole": None,
        "moisture_post_pct": None,
        "sensory_scores": sensory_scores,
    }

    # --- ML Prediction ---
    flat_inputs = flatten_data(session_data)
    confidence, predictions = predict_with_ml(flat_inputs)

    # --- Merge Predictions ---
    ml_filled_fields = set()

    # End of roast + turning point values
    for key in ["end_temp", "moisture_post_pct", "agtron_whole",
                "turning_point_temp", "turning_point_time"]:
        if session_data.get(key) is None and key in predictions:
            session_data[key] = predictions[key]
            ml_filled_fields.add(key)


    # Stage values
    for stage in session_data["stages"]:
        i = stage["stage"]

        if stage.get("burner_pct") is None and "burner_pct" in predictions and i in predictions["burner_pct"]:
            stage["burner_pct"] = predictions["burner_pct"][i]
            ml_filled_fields.add(f"burner_pct_{i}")

        pred_time = predictions.get(f"stage_{i}_time")
        if pred_time is not None:
            stage["time_in_secs"] = pred_time
            ml_filled_fields.add(f"time_in_secs_{i}")

    # Sensory scores
    for key in sensory_scores:
        if sensory_scores.get(key) is None and key in predictions:
            sensory_scores[key] = predictions[key]
            ml_filled_fields.add(key)



    # --- Final Report ---
    print_roast_report(session_data, confidence, ml_filled_fields)
