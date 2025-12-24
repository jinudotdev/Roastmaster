# scripts_main/inference_core_input_session.py

from datetime import datetime
from typing import Dict, Any
from scripts_utility.capture import (
    get_validated_date,
    get_validated_input,
    get_optional_validated_input,
    get_valid_time,
    get_optional_valid_time,
)
from scripts_main.edit_coffee_inventory import choose_inventory_entry


# -------------------------------------------------------------------
# CORE INPUT SESSION (required = Scout anchors, rest optional)
# -------------------------------------------------------------------

def core_input_session() -> Dict[str, Any]:
    """Collect the inputs Core needs for inference.
    Required fields match Scout anchors; rest optional (blank = skip)."""

    values: Dict[str, Any] = {}

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
            "purchase_date": (
                datetime.strptime(inventory_entry["purchase_date"], "%Y-%m-%d")
                if inventory_entry.get("purchase_date") else None
            ),
        })

    # Roast date (optional, defaults to today)
    values["roast_date"] = (
        get_validated_date("Roast Date [Blank = Today]: ", allow_blank=True)
        or datetime.today()
    )

    # --- Required environment ---
    values.update({
        "room_temp_f": get_validated_input("Room Temp (°F): ", float),
        "humidity_pct": get_validated_input("Humidity (%): ", float),
        "room_bean_temp_f": get_validated_input("Starting Bean Temp (°F): ", float),
        "green_bean_moisture_pct": get_validated_input("Green Bean Moisture (%): ", float),
        "batch_weight_lbs": get_validated_input("Batch Weight (lbs): ", float, min_val=150),
    })

    # --- Stage 0 (special case: time always 0) ---
    values["stage_0_temp_f"] = get_validated_input("Stage 0 - Bean Temp (°F): ", float, 200, 500)
    values["stage_0_burner_pct"] = get_optional_validated_input("Stage 0 - Burner (%), optional: ", float, 0, 100)
    values["stage_0_time_sec"] = 0  # always 0

    # --- Turning point (optional) ---
    values["turning_point_temp_f"] = get_optional_validated_input("Turning Point Temp (°F), optional: ", float, 200, 500)
    values["turning_point_time_sec"] = get_optional_valid_time("Turning Point Time (MMSS, e.g. 1230 for 12:30), optional: ")

    # --- Stages 1–9 ---
    for i in range(1, 10):
        values[f"stage_{i}_temp_f"] = get_validated_input(
            f"Stage {i} - Bean Temp (°F): ", float, 200, 500
        )

        # Required times for stages 1, 6, 9
        if i in (1, 6, 9):
            values[f"stage_{i}_time_sec"] = get_valid_time(
                f"Stage {i} - Time (MMSS, e.g. 1230 for 12:30): "
            )
        else:
            values[f"stage_{i}_time_sec"] = get_optional_valid_time(
                f"Stage {i} - Time (MMSS, e.g. 1230 for 12:30), optional: "
            )

        # Burner always optional
        values[f"stage_{i}_burner_pct"] = get_optional_validated_input(
            f"Stage {i} - Burner (%), optional: ", float, 0, 100
        )

    # --- Optional end-of-roast + sensory ---
    values["end_temp_f"] = get_optional_validated_input("End of Roast Temp (°F), optional: ", float, 200, 500)
    values["agtron"] = get_optional_validated_input("Agtron, optional: ", float)
    values["roasted_bean_moisture_pct"] = get_optional_validated_input("Post Roast Moisture (%), optional: ", float)
    values["clarity"] = get_optional_validated_input("Clarity (1–10), optional: ", int, 1, 10)
    values["acidity"] = get_optional_validated_input("Acidity (1–10), optional: ", int, 1, 10)
    values["body"] = get_optional_validated_input("Body (1–10), optional: ", int, 1, 10)
    values["sweetness"] = get_optional_validated_input("Sweetness (1–10), optional: ", int, 1, 10)
    values["overall_rating"] = get_optional_validated_input("Overall Rating (1–10), optional: ", int, 1, 10)

    return values
