from datetime import datetime
from scripts.utilities.capture import (
    get_optional_choice,
    get_validated_date,
    get_validated_input,
    get_optional_validated_input,
    get_optional_valid_time
)
from models.ml_inference import predict_with_ml
from scripts.utilities.print_model_output import print_roast_report


def run_model_session() -> None:
    # --- Bean Metadata ---
    supplier = get_optional_validated_input("Supplier [Optional]: ", str)
    origin_country = get_optional_validated_input("Origin Country [Optional]: ", str)
    altitude_meters = get_optional_validated_input("Altitude (meters) [Optional]: ", int, 0, 4000)
    variety = get_optional_validated_input("Variety [Optional]: ", str)
    process_method = get_optional_choice("Process Method [Optional]:", {
        "1": "Natural", "2": "Washed", "3": "Honey", "4": "Wet-Hulled", "5": "Other"
    })
    purchase_date = get_validated_date("Purchase Date [Optional]: ", allow_blank=True)
    roast_date = get_validated_date("Roast Date [Blank = Today]: ", allow_blank=True) or datetime.today()

    room_temp_f = get_optional_validated_input("Room Temp (°F) [Optional]: ", float)
    humidity_pct = get_optional_validated_input("Humidity (%) [Optional]: ", float)
    bean_temp_start_f = get_optional_validated_input("Starting Bean Temp (°F) [Optional]: ", float)
    green_bean_moisture_pct = get_optional_validated_input("Green Bean Moisture (%) [Optional]: ", float)

    batch_weight_lbs = get_validated_input("Batch Weight (lbs) [Required]: ", float, min_val=150)

    # --- Roast Stages ---
    stages = {}
    print("\nStage 0 - at Charge (time is always 00:00)")
    stages[0] = {
        "stage_0_temp": get_optional_validated_input("Stage 0 - Bean Temp (°F): ", float, 200, 500),
        "stage_0_time": 0,
        "stage_0_burner": get_optional_validated_input("Stage 0 - Burner %: ", float, 0, 100),
    }

    print("\nTurning Point")
    turning_point_temp = get_optional_validated_input("Turning Point - Bean Temp (°F): ", float, 200, 500)
    turning_point_time = get_optional_valid_time("Turning Point - Time (MMSS, e.g. 1230 for 12:30): ")

    for i in range(1, 10):
        print(f"\nStage {i}")
        if i == 9:
            bean_temp = get_validated_input("Stage 9 - Bean Temp (°F): ", float, 380, 500)
        else:
            bean_temp = get_optional_validated_input(f"Stage {i} - Bean Temp (°F): ", float, 200, 500)
        burner_pct = get_optional_validated_input(f"Stage {i} - Burner %: ", float, 0, 100)
        stage_time_in_secs = get_optional_valid_time("Time (MMSS, e.g. 1230 for 12:30): ")

        stages[i] = {
            f"stage_{i}_temp": bean_temp,
            f"stage_{i}_time": stage_time_in_secs,
            f"stage_{i}_burner": burner_pct,
        }

    # --- Sensory Scores ---
    print("\nSensory Scores (optional, 1–10)")
    sensory = {
        "target_clarity": get_optional_validated_input("Clarity: ", int),
        "target_acidity": get_optional_validated_input("Acidity: ", int),
        "target_body": get_optional_validated_input("Body: ", int),
        "target_sweetness": get_optional_validated_input("Sweetness: ", int),
        "target_overall": get_optional_validated_input("Overall: ", int),
    }
    descriptors = get_optional_validated_input("Comments: ", str)
    if descriptors:
        sensory["descriptors"] = descriptors.lower()

    # --- Flat session dict (already matches FEATURE_ORDER) ---
    flat_inputs = {
        "supplier": supplier,
        "origin_country": origin_country,
        "altitude_meters": altitude_meters,
        "variety": variety,
        "process_method": process_method,
        "purchase_date": purchase_date,
        "roast_date": roast_date,
        "room_temp_f": room_temp_f,
        "humidity_pct": humidity_pct,
        "bean_temp_start_f": bean_temp_start_f,
        "green_bean_moisture_pct": green_bean_moisture_pct,
        "batch_weight_lbs": batch_weight_lbs,
        "end_temp": None,
        "moisture_post_pct": None,
        "agtron_whole": None,
        "turning_point_temp": turning_point_temp,
        "turning_point_time": turning_point_time,
        **{k: v for stage in stages.values() for k, v in stage.items()},
        **sensory,
    }

    # --- ML Prediction ---
    confidence, predictions = predict_with_ml(flat_inputs)

    # --- Merge predictions into flat_inputs ---
    ml_filled_fields = set()
    for key, val in predictions.items():
        if flat_inputs.get(key) is None and val is not None:
            flat_inputs[key] = val
            ml_filled_fields.add(key)

    # --- Final Report ---
    print_roast_report(flat_inputs, confidence, ml_filled_fields)
