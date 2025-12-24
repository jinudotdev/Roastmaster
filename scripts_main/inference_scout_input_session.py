# scripts_main/inference_scout_input_session.py

from datetime import datetime
from typing import Dict, Any
from scripts_utility.capture import (
    get_validated_input,
    get_valid_time,
)
from scripts_main.edit_coffee_inventory import choose_inventory_entry


# -------------------------------------------------------------------
# SCOUT INPUT SESSION (minimal, matches SCOUT_FEATURE_ORDER)
# -------------------------------------------------------------------

def scout_input_session() -> Dict[str, Any]:
    """Collect the inputs Scout needs for inference (anchors only)."""

    values: Dict[str, Any] = {}

    # --- Inventory check ---
    inventory_entry = choose_inventory_entry()
    if inventory_entry:
        print("✅ Using inventory entry for bean metadata.")
        values["process_method"] = inventory_entry.get("process_method")
    else:
        # Manual process method choice
        choice_map = {
            "1": "Natural",
            "2": "Washed",
            "3": "Honey",
            "4": "Wet-Hulled",
            "5": "Other",
        }
        process_choice = input(
            "Process Method:\n1. Natural\n2. Washed\n3. Honey\n4. Wet-Hulled\n5. Other\nChoose (1–5): "
        ).strip()
        values["process_method"] = choice_map.get(process_choice, None)

    # --- Required environment + roast anchors ---
    values.update({
        "room_temp_f": get_validated_input("Room Temp (°F): ", float),
        "humidity_pct": get_validated_input("Humidity (%): ", float),
        "room_bean_temp_f": get_validated_input("Starting Bean Temp (°F): ", float),
        "green_bean_moisture_pct": get_validated_input("Green Bean Moisture (%): ", float),
        "batch_weight_lbs": get_validated_input("Batch Weight (lbs): ", float, min_val=150),

        "stage_0_temp_f": get_validated_input("Stage 0 - Bean Temp (°F): ", float, 200, 500),

        "stage_1_temp_f": get_validated_input("Stage 1 - Bean Temp (°F): ", float, 200, 500),
        "stage_1_time_sec": get_valid_time("Stage 1 - Time (MMSS, e.g. 1230 for 12:30): "),

        "stage_2_temp_f": get_validated_input("Stage 2 - Bean Temp (°F): ", float, 200, 500),
        "stage_3_temp_f": get_validated_input("Stage 3 - Bean Temp (°F): ", float, 200, 500),
        "stage_4_temp_f": get_validated_input("Stage 4 - Bean Temp (°F): ", float, 200, 500),
        "stage_5_temp_f": get_validated_input("Stage 5 - Bean Temp (°F): ", float, 200, 500),

        "stage_6_temp_f": get_validated_input("Stage 6 - Bean Temp (°F): ", float, 200, 500),
        "stage_6_time_sec": get_valid_time("Stage 6 - Time (MMSS, e.g. 1230 for 12:30): "),

        "stage_7_temp_f": get_validated_input("Stage 7 - Bean Temp (°F): ", float, 200, 500),
        "stage_8_temp_f": get_validated_input("Stage 8 - Bean Temp (°F): ", float, 200, 500),

        "stage_9_temp_f": get_validated_input("Stage 9 - Bean Temp (°F): ", float, 380, 500),
        "stage_9_time_sec": get_valid_time("Stage 9 - Time (MMSS, e.g. 1230 for 12:30): "),
    })

    return values
