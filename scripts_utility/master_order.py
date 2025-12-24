# Canonical roast data schema order for CSV/JSONL

MASTER_ORDER = [
    "line_number",  # internal bookkeeping
    "id",
    "roast_date",
    "country",
    "region",
    "altitude_meters",
    "variety",
    "process_method",
    "purchase_date",
    "supplier",
    "room_temp_f",
    "humidity_pct",
    "room_bean_temp_f",
    "green_bean_moisture_pct",
    "batch_weight_lbs",
    "post_roast_batch_weight_lbs",
    "turning_point_temp_f",
    "turning_point_time_sec",
    "end_temp_f",
    "agtron",
    "roasted_bean_moisture_pct",
    "clarity",
    "acidity",
    "body",
    "sweetness",
    "overall_rating",
    # Stages
    "stage_0_time_sec", "stage_0_temp_f", "stage_0_burner_pct",
    "stage_1_time_sec", "stage_1_temp_f", "stage_1_burner_pct",
    "stage_2_time_sec", "stage_2_temp_f", "stage_2_burner_pct",
    "stage_3_time_sec", "stage_3_temp_f", "stage_3_burner_pct",
    "stage_4_time_sec", "stage_4_temp_f", "stage_4_burner_pct",
    "stage_5_time_sec", "stage_5_temp_f", "stage_5_burner_pct",
    "stage_6_time_sec", "stage_6_temp_f", "stage_6_burner_pct",
    "stage_7_time_sec", "stage_7_temp_f", "stage_7_burner_pct",
    "stage_8_time_sec", "stage_8_temp_f", "stage_8_burner_pct",
    "stage_9_time_sec", "stage_9_temp_f", "stage_9_burner_pct",
]

# -------------------------------------------------------------------
# CORE MODEL
# -------------------------------------------------------------------

CORE_FEATURE_ORDER = [
    "supplier",
    "country",
    "region",
    "variety",
    "process_method",
    "altitude_meters",
    "roast_date",
    "bean_age_days_at_roast",
    "room_temp_f",
    "humidity_pct",
    "room_bean_temp_f",
    "green_bean_moisture_pct",
    "batch_weight_lbs",

    # Turning point features
    "turning_point_temp_f",
    "turning_point_time_sec",

    # End-of-roast features
    "end_temp_f",
    "agtron",
    "roasted_bean_moisture_pct",
]

# Dynamically add stage features
MAX_STAGES = 10  # adjust as needed
for i in range(MAX_STAGES):
    CORE_FEATURE_ORDER.extend([
        f"stage_{i}_temp_f",
        f"stage_{i}_burner_pct",
        f"stage_{i}_time_sec",
    ])

CORE_PREDICTABLES = [
    # Metadata targets
    "post_roast_batch_weight_lbs",
    "turning_point_temp_f", "turning_point_time_sec", 
    "end_temp_f",
    "agtron",
    "roasted_bean_moisture_pct",
    "clarity",
    "acidity",
    "body",
    "sweetness",
    "overall_rating",
    # Stages
    "stage_0_time_sec","stage_0_burner_pct",
    "stage_1_burner_pct",
    "stage_2_time_sec","stage_2_burner_pct",
    "stage_3_time_sec","stage_3_burner_pct",
    "stage_4_time_sec","stage_4_burner_pct",
    "stage_5_time_sec","stage_5_burner_pct",
    "stage_6_burner_pct",
    "stage_7_time_sec","stage_7_burner_pct",
    "stage_8_time_sec","stage_8_burner_pct",
    "stage_9_burner_pct",
]

# -------------------------------------------------------------------
# SCOUT MODEL 
# -------------------------------------------------------------------

SCOUT_FEATURE_ORDER = [
    "process_method",
    "room_temp_f",
    "humidity_pct",
    "room_bean_temp_f",
    "green_bean_moisture_pct",
    "batch_weight_lbs",
    # Anchors
    "stage_0_temp_f",
    "stage_1_temp_f", "stage_1_time_sec",
    "stage_2_temp_f", 
    "stage_3_temp_f", 
    "stage_4_temp_f", 
    "stage_5_temp_f", 
    "stage_6_temp_f", "stage_6_time_sec",
    "stage_7_temp_f",
    "stage_8_temp_f",
    "stage_9_temp_f", "stage_9_time_sec",
]

SCOUT_PREDICTABLES = [
    "turning_point_temp_f",
    "turning_point_time_sec",
    "end_temp_f",
    # Stages
    "stage_0_time_sec","stage_0_burner_pct",
    "stage_1_burner_pct",
    "stage_2_time_sec","stage_2_burner_pct",
    "stage_3_time_sec","stage_3_burner_pct",
    "stage_4_time_sec","stage_4_burner_pct",
    "stage_5_time_sec","stage_5_burner_pct",
    "stage_6_burner_pct",
    "stage_7_time_sec","stage_7_burner_pct",
    "stage_8_time_sec","stage_8_burner_pct",
    "stage_9_burner_pct",
]

# Scout-specific categorical and date columns
SCOUT_CATEGORICAL_COLS = ["process_method"]
SCOUT_DATE_COLS = []  # no dates for Scout

# -------------------------------------------------------------------

if __name__ == "__main__":
    print("MASTER_ORDER length:", len(MASTER_ORDER))
    print("CORE_FEATURE_ORDER length:", len(CORE_FEATURE_ORDER))
    print("CORE_PREDICTABLES length:", len(CORE_PREDICTABLES))
    print("SCOUT_FEATURE_ORDER length:", len(SCOUT_FEATURE_ORDER))
    print("SCOUT_PREDICTABLES length:", len(SCOUT_PREDICTABLES))
    print("SCOUT_CATEGORICAL_COLS:", SCOUT_CATEGORICAL_COLS)
    print("SCOUT_DATE_COLS:", SCOUT_DATE_COLS)
