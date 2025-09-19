from datetime import datetime
from models.ml import flatten_data, predict_with_ml, FEATURE_ORDER
from scripts.utilities.print_model_output import print_roast_report

def test_run():
    roast_input = {
        "roast_date": datetime.today(),
        "supplier_name": "royal",
        "origin_country": "brazil",
        "altitude_meters": None,
        "variety": None,
        "process_method": "Natural",
        "purchase_date": datetime.strptime("03/03/25", "%m/%d/%y"),
        "room_temp_f": 70.0,
        "room_rh_pct": 50.0,
        "bean_temp_pre_f": 70.0,
        "green_bean_moisture_pct": 10.0,
        "batch_weight_lbs": 200.0,
        "batch_weight_kg": 200.0 * 0.453592,
        "turning_point_time": None,   
        "turning_point_temp": None,  

        "stages": [
            {"stage": 0,  "time_in_secs": 0,   "bean_temp": 400.0, "burner_pct": 40.0},
            {"stage": 1,  "time_in_secs": 750, "bean_temp": 300.0, "burner_pct": 45.0},
            {"stage": 2,  "time_in_secs": 750, "bean_temp": 320.0, "burner_pct": 43.0},
            {"stage": 3,  "time_in_secs": 750, "bean_temp": 340.0, "burner_pct": 40.0},
            {"stage": 4,  "time_in_secs": 750, "bean_temp": 360.0, "burner_pct": 36.0},
            {"stage": 5,  "time_in_secs": 750, "bean_temp": 380.0, "burner_pct": 35.0},
            {"stage": 6,  "time_in_secs": 750, "bean_temp": 400.0, "burner_pct": 34.0},
            {"stage": 7,  "time_in_secs": 750, "bean_temp": 430.0, "burner_pct": 34.0},
            {"stage": 8,  "time_in_secs": 750, "bean_temp": 440.0, "burner_pct": 32.0},
            {"stage": 9,  "time_in_secs": 750, "bean_temp": 455.0, "burner_pct": 31.0},
        ],
        "end_temp": None,
        "agtron_whole": None,
        "moisture_post_pct": None,
        "sensory_scores": {
            "clarity": None,
            "acidity": None,
            "body": None,
            "sweetness": None,
            "overall": None,
            "descriptors": None
        }
    }

    flat_inputs = flatten_data(roast_input)

    # 🔍 Schema alignment check
    expected = set(FEATURE_ORDER)
    actual = set(flat_inputs)
    missing = expected - actual
    extra = actual - expected

    assert len(flat_inputs) == len(FEATURE_ORDER), (
        f"[ERROR] Expected {len(FEATURE_ORDER)} features, got {len(flat_inputs)}.\n"
        f"Missing: {missing}\nExtra: {extra}"
    )

    confidence, predictions = predict_with_ml(flat_inputs)

    print("\n[DEBUG] Flattened inputs:", flat_inputs)
    print("[DEBUG] Predictions returned:", predictions)
    print("[DEBUG] Confidence:", confidence)

    ml_filled_fields = set()

    for key in ["end_temp", "moisture_post_pct", "agtron_whole",
                "turning_point_temp", "turning_point_time"]:
        if roast_input.get(key) is None and key in predictions:
            roast_input[key] = predictions[key]
            ml_filled_fields.add(key)


    for stage in roast_input["stages"]:
        i = stage["stage"]
        if stage.get("burner_pct") is None and "burner_pct" in predictions and i in predictions["burner_pct"]:
            stage["burner_pct"] = predictions["burner_pct"][i]
            ml_filled_fields.add(f"burner_pct_{i}")
        if stage.get("duration_secs") is None and "stage_times" in predictions and i in predictions["stage_times"]:
            stage["duration_secs"] = predictions["stage_times"][i]
            ml_filled_fields.add(f"duration_secs_{i}")
        pred_time = predictions.get(f"stage_{i}_time")
        if pred_time is not None:
            stage["time_in_secs"] = pred_time
            ml_filled_fields.add(f"time_in_secs_{i}")

    for key in roast_input["sensory_scores"]:
        if roast_input["sensory_scores"].get(key) is None and key in predictions:
            roast_input["sensory_scores"][key] = predictions[key]
            ml_filled_fields.add(key)

    print_roast_report(roast_input, confidence, ml_filled_fields)

if __name__ == "__main__":
    test_run()
