from datetime import datetime
from typing import Dict, Any
from scripts_utility.capture import (
    get_optional_choice,
    get_validated_date,
    get_validated_input,
    get_optional_validated_input,
    get_optional_valid_time
)
from scripts_main.edit_coffee_inventory import choose_inventory_entry


def roast_data_input_session() -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    stages: Dict[int, Dict[str, Any]] = {}

    # --- Inventory check ---
    inventory_entry = choose_inventory_entry()
    if inventory_entry:
        print("✅ Using inventory entry for bean metadata.")
        values.update({
            "supplier": inventory_entry.get("supplier"),
            "country": inventory_entry.get("country"),
            "region": inventory_entry.get("region"),
            "altitude_meters": inventory_entry.get("altitude_meters"),
            "variety": inventory_entry.get("variety"),
            "process_method": inventory_entry.get("process_method"),
        })
        # roast_date is always roast‑specific
        values["roast_date"] = get_validated_date("Roast Date [Blank = Today]: ", allow_blank=True) or datetime.today()
    else:
        # --- Bean Metadata sequence (manual entry) ---
        bean_fields = [
            ("supplier", lambda: get_optional_validated_input("Supplier [Optional]: ", str)),
            ("country", lambda: get_optional_validated_input("Country [Optional]: ", str)),
            ("region", lambda: get_optional_validated_input("Region [Optional]: ", str)),
            ("altitude_meters", lambda: get_optional_validated_input("Altitude (meters) [Optional]: ", int, 0, 4000)),
            ("variety", lambda: get_optional_validated_input("Variety [Optional]: ", str)),
            ("process_method", lambda: get_optional_choice("Process Method [Optional]:", {
                "1": "Natural", "2": "Washed", "3": "Honey", "4": "Wet-Hulled", "5": "Other"
            })),
            ("purchase_date", lambda: get_validated_date("Purchase Date: ", allow_blank=True)),
            ("roast_date", lambda: get_validated_date("Roast Date [Blank = Today]: ", allow_blank=True) or datetime.today()),
            ("room_temp_f", lambda: get_validated_input("Room Temp (°F) [Required]: ", float)),
            ("humidity_pct", lambda: get_validated_input("Humidity (%) [Required]: ", float)),
            ("room_bean_temp_f", lambda: get_validated_input("Starting Bean Temp (°F) [Required]: ", float)),
            ("green_bean_moisture_pct", lambda: get_validated_input("Green Bean Moisture (%) [Required]: ", float)),
            ("batch_weight_lbs", lambda: get_validated_input("Batch Weight (lbs) [Required]: ", float, min_val=150)),
        ]

        i = 0
        while i < len(bean_fields):
            name, func = bean_fields[i]
            val = func()
            if val == "__BACK__":
                if i > 0:
                    i -= 1
                continue
            elif val == "__REDO__":
                continue
            else:
                values[name] = val
                i += 1

    # --- Roast Stages ---
    print("\nStage 0 - at Charge (time is always 00:00)")
    stages[0] = {
        "stage_0_temp_f": get_validated_input("Stage 0 - Bean Temp (°F) [Required]: ", float, 200, 500),
        "stage_0_time_sec": 0,
        "stage_0_burner_pct": get_optional_validated_input("Stage 0 - Burner % [Optional]: ", float, 0, 100),
    }

    print("\nTurning Point")
    turning_point_temp_f = get_optional_validated_input("Turning Point - Bean Temp (°F): ", float, 200, 500)
    turning_point_time_sec = get_optional_valid_time("Turning Point - Time (MMSS, e.g. 1230 for 12:30): ")

    i = 1
    while i < 10:
        print(f"\nStage {i}")
        if i == 9:
            bean_temp = get_validated_input("Stage 9 - Bean Temp (°F) [Required]: ", float, 380, 500)
        else:
            bean_temp = get_optional_validated_input(f"Stage {i} - Bean Temp (°F) [Optional]: ", float, 200, 500)

        if bean_temp == "__BACK__":
            if i > 1:
                i -= 1
            continue
        elif bean_temp == "__REDO__":
            continue

        burner_pct = get_optional_validated_input(f"Stage {i} - Burner % [Optional]: ", float, 0, 100)
        stage_time_in_secs = get_optional_valid_time("Time (MMSS, e.g. 1230 for 12:30): ")

        stages[i] = {
            f"stage_{i}_temp_f": bean_temp,
            f"stage_{i}_time_sec": stage_time_in_secs,
            f"stage_{i}_burner_pct": burner_pct,
        }
        i += 1

    # --- Sensory Scores ---
    print("\nSensory Scores (optional, 1–10, 10 is best)")
    sensory = {}
    for field, prompt in [
        ("target_clarity", "Clarity: "),
        ("target_acidity", "Acidity: "),
        ("target_body", "Body: "),
        ("target_sweetness", "Sweetness: "),
        ("target_overall", "Overall: "),
    ]:
        while True:
            val = get_optional_validated_input(prompt, int)
            if val in ("__BACK__", "__REDO__"):
                continue
            sensory[field] = val
            break

    notes = get_optional_validated_input("Comments: ", str)
    if notes and notes not in ("__BACK__", "__REDO__"):
        sensory["notes"] = notes.lower()

    # --- Flat session dict ---
    flat_inputs = {
        **values,
        "end_temp_f": None,
        "roasted_bean_moisture_pct": None,
        "agtron": None,
        "turning_point_temp_f": turning_point_temp_f,
        "turning_point_time_sec": turning_point_time_sec,
        **{k: v for stage in stages.values() for k, v in stage.items()},
        **sensory,
    }

    return flat_inputs
