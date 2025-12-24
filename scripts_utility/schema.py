from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class RoastSession:
    # --- identifiers & metrics ---
    id: str
    roast_date: datetime
    batch_weight_lbs: float

    # --- Pre-Roast Metrics (required) --- 
    room_temp_f: float
    humidity_pct: float
    room_bean_temp_f: float
    green_bean_moisture_pct: float

    # --- Roast curve (flattened) ---
    stage_0_temp_f: float
    stage_9_temp_f: float # required
    stage_0_time_sec: int = 0 
    stage_0_burner_pct: Optional[float] = None
    stage_1_temp_f: Optional[float] = None
    stage_1_time_sec: Optional[int] = None
    stage_1_burner_pct: Optional[float] = None
    stage_2_temp_f: Optional[float] = None
    stage_2_time_sec: Optional[int] = None
    stage_2_burner_pct: Optional[float] = None
    stage_3_temp_f: Optional[float] = None
    stage_3_time_sec: Optional[int] = None
    stage_3_burner_pct: Optional[float] = None
    stage_4_temp_f: Optional[float] = None
    stage_4_time_sec: Optional[int] = None
    stage_4_burner_pct: Optional[float] = None
    stage_5_temp_f: Optional[float] = None
    stage_5_time_sec: Optional[int] = None
    stage_5_burner_pct: Optional[float] = None
    stage_6_temp_f: Optional[float] = None
    stage_6_time_sec: Optional[int] = None
    stage_6_burner_pct: Optional[float] = None
    stage_7_temp_f: Optional[float] = None
    stage_7_time_sec: Optional[int] = None
    stage_7_burner_pct: Optional[float] = None
    stage_8_temp_f: Optional[float] = None
    stage_8_time_sec: Optional[int] = None
    stage_8_burner_pct: Optional[float] = None
    # stage_9_temp_f: float (moved up, placehold here not break my brain)
    stage_9_time_sec: Optional[int] = None
    stage_9_burner_pct: Optional[float] = None
    turning_point_temp_f: Optional[float] = None
    turning_point_time_sec: Optional[int] = None
    end_temp_f: Optional[float] = None

    # --- bean metadata ---
    supplier: Optional[str] = None
    country: Optional[str] = None  
    region: Optional[str] = None    
    altitude_meters: Optional[int] = None
    variety: Optional[str] = None
    process_method: Optional[str] = None
    purchase_date: Optional[datetime] = None

    # --- Post Input bean metadata --- 
    bean_age_days_at_roast: Optional[int] = None

    # --- Post Roast Metrics --- 
    roasted_bean_moisture_pct: Optional[float] = None
    agtron: Optional[str] = None
    post_roast_batch_weight_lbs: Optional[float] = None
    
    # --- Sensory profile (optional until labeled) ---
    clarity: Optional[int] = None
    acidity: Optional[int] = None
    body: Optional[int] = None
    sweetness: Optional[int] = None
    overall_rating: Optional[int] = None


