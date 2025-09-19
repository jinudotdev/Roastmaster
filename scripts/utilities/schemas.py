from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class SensoryScores:
    clarity: Optional[int] = None
    acidity: Optional[int] = None
    body: Optional[int] = None
    sweetness: Optional[int] = None
    overall: Optional[int] = None
    descriptors: Optional[str] = None

@dataclass
class RoastStage:
    stage: int
    time_in_secs: int
    bean_temp: float
    burner_pct: float

@dataclass
class RoastSession:
    # --- Required identifiers & metrics ---
    id: str
    roast_date: datetime
    supplier_name: str
    roaster_id: str
    batch_weight_lbs: float
    batch_weight_kg: float
    charge_temp_f: float
    end_temp: float
    turning_point_temp: float
    turning_point_time: int
    stages: List[RoastStage]

    # --- Optional metadata & outcomes ---
    origin_country: Optional[str] = None
    altitude_meters: Optional[int] = None
    variety: Optional[str] = None
    process_method: Optional[str] = None
    purchase_date: Optional[datetime] = None
    room_temp_f: Optional[float] = None
    room_rh_pct: Optional[float] = None
    bean_temp_pre_f: Optional[float] = None
    green_bean_moisture_pct: Optional[float] = None
    moisture_pre_pct: Optional[float] = None
    moisture_post_pct: Optional[float] = None
    agtron_whole: Optional[int] = None
    agtron_ground: Optional[int] = None
    post_roast_batch_weight_lbs: Optional[float] = None
    post_roast_batch_weight_kg: Optional[float] = None
    notes: Optional[str] = None
    sensory_scores: Optional[SensoryScores] = None
