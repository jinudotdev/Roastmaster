# gui/gui_inference_core_input_session.py

import os
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Callable

import pandas as pd
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QScrollArea,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
)

# Local curve + report
from .gui_curve_plot import CurvePlotWindow
from .gui_print_core_report import open_core_report_dialog

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

INVENTORY_PATH = os.path.join("data", "coffee_inventory.csv")
ROAST_PATH = os.path.join("data", "roast_data.csv")

# -------------------------------------------------------------------
# Default stage values (so you can just tweak instead of typing)
# -------------------------------------------------------------------

# Typical bean-temp curve you were already using in your samples
STAGE_TEMP_DEFAULTS: Dict[int, str] = {
    1: "300",
    2: "320",
    3: "340",
    4: "360",
    5: "380",
    6: "400",
    7: "430",
    8: "445",
    9: "455",
}

# Default key anchors for Core (MMSS)
STAGE_TIME_MMSS_DEFAULTS: Dict[int, str] = {
    1: "0400",  # 4:00
    6: "0800",  # 8:00
    9: "1100",  # 11:00
}

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def mmss_to_seconds(mmss_str: Optional[str]) -> Optional[float]:
    """Convert MMSS (e.g. '0400') to seconds."""
    if not mmss_str:
        return None
    s = mmss_str.strip()
    if not s.isdigit():
        return None
    if len(s) <= 2:
        minutes = 0
        seconds = int(s)
    else:
        minutes = int(s[:-2])
        seconds = int(s[-2:])
    return float(minutes * 60 + seconds)


def parse_date_yyyy_mm_dd(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def load_inventory_rows() -> List[Dict[str, Any]]:
    if not os.path.exists(INVENTORY_PATH):
        return []
    try:
        df = pd.read_csv(INVENTORY_PATH)
    except Exception:
        return []

    rows: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rows.append(row.to_dict())
    return rows


# -------------------------------------------------------------------
# Core Input Session Window (GUI)
# -------------------------------------------------------------------

class CoreInputSessionWindow(QWidget):
    """
    GUI version of core_input_session().

    submit_callback must accept a dict of session_data and return:
        (predicted_session, confidence, ml_filled_fields)
    """

    def __init__(self, submit_callback: Callable[[Dict[str, Any]], Any]):
        super().__init__()
        self.setWindowTitle("Core Input – Roast Prediction (Big Model)")
        self.resize(900, 750)

        self._submit_callback = submit_callback
        self._child_windows: List[QWidget] = []  # keep plot/report alive

        # key -> QLineEdit
        self.inputs: Dict[str, QLineEdit] = {}

        # track required keys for simple "non-empty" validation
        self.required_env_keys = [
            "room_temp_f",
            "humidity_pct",
            "bean_temp_start_f",
            "green_bean_moisture_pct",
            "batch_weight_lbs",
        ]
        self.required_stage_temp_keys = [f"stage_{i}_temp_f" for i in range(0, 10)]
        self.required_stage_time_mmss_keys = [
            "stage_1_time_mmss",
            "stage_6_time_mmss",
            "stage_9_time_mmss",
        ]

        outer_layout = QVBoxLayout()

        # --------------------------
        # Inventory row
        # --------------------------
        inv_row = QHBoxLayout()
        inv_label = QLabel("Use inventory coffee (optional):")
        inv_row.addWidget(inv_label)

        self.inventory_combo = QComboBox()
        self.inventory_combo.addItem("— None —", userData=None)

        for row in load_inventory_rows():
            supplier = row.get("supplier", "?")
            country = row.get("country", "?")
            region = row.get("region", "")
            desc = f"{supplier} – {country}"
            if region and not pd.isna(region):
                desc += f" – {region}"

            variety = row.get("variety", None)
            process = row.get("process_method", None)
            extras = []
            if variety is not None and not pd.isna(variety):
                extras.append(str(variety))
            if process is not None and not pd.isna(process):
                extras.append(str(process))
            if extras:
                desc += f" ({', '.join(extras)})"

            purchase = row.get("purchase_date", None)
            if purchase is not None and not pd.isna(purchase):
                desc += f" | Purchased: {purchase}"

            self.inventory_combo.addItem(desc, userData=row)

        inv_row.addWidget(self.inventory_combo)
        outer_layout.addLayout(inv_row)

        # --------------------------
        # Scrollable form
        # --------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form_layout = QFormLayout()
        inner.setLayout(form_layout)
        scroll.setWidget(inner)
        outer_layout.addWidget(scroll)

        def add_field(
            key: str,
            label: str,
            placeholder: str = "",
            default: Optional[str] = None,
        ):
            box = QLineEdit()
            if placeholder:
                box.setPlaceholderText(placeholder)
            if default is not None:
                box.setText(default)
            self.inputs[key] = box
            form_layout.addRow(label, box)

        # --------------------------
        # Roast date
        # --------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Roast Info"))
        form_layout.addRow(QLabel(""))

        add_field(
            "roast_date",
            "Roast Date [Blank = Today] (YYYY-MM-DD)",
            placeholder="YYYY-MM-DD (blank = today)",
        )

        # --------------------------
        # Environment
        # --------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Environment / Batch (required)"))
        form_layout.addRow(QLabel(""))

        add_field("room_temp_f", "Room Temp (°F)", default="70")
        add_field("humidity_pct", "Humidity (%)", default="50")
        add_field("bean_temp_start_f", "Starting Bean Temp (°F)", default="70")
        add_field("green_bean_moisture_pct", "Green Bean Moisture (%)", default="10.0")
        add_field("batch_weight_lbs", "Batch Weight (lbs)", default="200")

        # --------------------------
        # Stage 0 (Charge)
        # --------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Stage 0 – at Charge (time is always 00:00)"))
        form_layout.addRow(QLabel(""))

        add_field(
            "stage_0_temp_f",
            "Stage 0 – Bean Temp (°F) [Required]",
            default="400",
        )
        add_field(
            "stage_0_burner_pct",
            "Stage 0 – Burner (%) [Optional]",
        )

        # --------------------------
        # Turning point
        # --------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Turning Point (optional)"))
        form_layout.addRow(QLabel(""))

        add_field(
            "turning_point_temp_f",
            "Turning Point – Bean Temp (°F)",
        )
        add_field(
            "turning_point_time_mmss",
            "Turning Point – Time (MMSS, e.g. 1230 for 12:30)",
        )

        # --------------------------
        # Stages 1–9
        # --------------------------
        for i in range(1, 10):
            form_layout.addRow(QLabel(""))
            if i == 1:
                form_layout.addRow(QLabel("Stage 1"))
            elif i == 9:
                form_layout.addRow(QLabel("Stage 9 (End Stage)"))
            else:
                form_layout.addRow(QLabel(f"Stage {i}"))
            form_layout.addRow(QLabel(""))

            # Temps: required for 1–9 in Core, with defaults
            temp_default = STAGE_TEMP_DEFAULTS.get(i)
            add_field(
                f"stage_{i}_temp_f",
                f"Stage {i} – Bean Temp (°F) [Required]",
                default=temp_default,
            )

            # Burners always optional
            add_field(
                f"stage_{i}_burner_pct",
                f"Stage {i} – Burner (%) [Optional]",
            )

            # Times: required for stages 1,6,9; optional otherwise, with defaults on required
            if i in (1, 6, 9):
                label = f"Stage {i} – Time (MMSS, e.g. 1230 for 12:30) [Required]"
                time_default = STAGE_TIME_MMSS_DEFAULTS.get(i)
            else:
                label = f"Stage {i} – Time (MMSS, e.g. 1230 for 12:30) [Optional]"
                time_default = None

            add_field(
                f"stage_{i}_time_mmss",
                label,
                default=time_default,
            )

        # --------------------------
        # Optional end-of-roast + sensory
        # --------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("End of Roast / Sensory (optional)"))
        form_layout.addRow(QLabel(""))

        add_field("end_temp_f", "End of Roast Temp (°F)")
        add_field("agtron", "Agtron")
        add_field("roasted_bean_moisture_pct", "Post Roast Moisture (%)")

        add_field("clarity", "Clarity (1–10)")
        add_field("acidity", "Acidity (1–10)")
        add_field("body", "Body (1–10)")
        add_field("sweetness", "Sweetness (1–10)")
        add_field("overall_rating", "Overall Rating (1–10)")

        # --------------------------
        # Buttons
        # --------------------------
        btn_row = QHBoxLayout()
        btn_run = QPushButton("Run Core Prediction")
        btn_cancel = QPushButton("Cancel")

        btn_run.clicked.connect(self.on_submit)
        btn_cancel.clicked.connect(self.close)

        btn_row.addWidget(btn_run)
        btn_row.addWidget(btn_cancel)
        outer_layout.addLayout(btn_row)

        self.setLayout(outer_layout)

    # ------------------------------------------------------------------
    # Submit → build session_data, call callback, show report + curve
    # ------------------------------------------------------------------
    def on_submit(self):
        # Clear any old red borders
        for box in self.inputs.values():
            box.setStyleSheet("")

        session_data: Dict[str, Any] = {}
        missing_fields: List[str] = []

        # 1) Raw text capture
        for key, box in self.inputs.items():
            txt = box.text().strip()
            session_data[key] = txt if txt != "" else None

        # 2) Roast date → datetime
        roast_date_text = session_data.get("roast_date")
        if roast_date_text:
            rd = parse_date_yyyy_mm_dd(roast_date_text)
            if rd is None:
                self.inputs["roast_date"].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Roast Date",
                    "Roast date must be YYYY-MM-DD or blank.",
                )
                return
            # Core uses datetime
            session_data["roast_date"] = datetime.combine(rd, datetime.min.time())
        else:
            today = date.today()
            session_data["roast_date"] = datetime.combine(today, datetime.min.time())

        # 3) Inventory metadata → session_data
        inv_row = self.inventory_combo.currentData()
        if isinstance(inv_row, dict):
            # Basic metadata
            supplier = inv_row.get("supplier")
            country = inv_row.get("country")
            region = inv_row.get("region")
            altitude = inv_row.get("altitude_meters")
            variety = inv_row.get("variety")
            process = inv_row.get("process_method")

            if supplier:
                session_data["supplier"] = str(supplier)
            if country:
                session_data["country"] = str(country)
            if region and not pd.isna(region):
                session_data["region"] = str(region)
            if altitude not in (None, "", "NaN") and not pd.isna(altitude):
                try:
                    session_data["altitude_meters"] = float(altitude)
                except Exception:
                    pass
            if variety and not pd.isna(variety):
                session_data["variety"] = str(variety)
            if process and not pd.isna(process):
                session_data["process_method"] = str(process)

            # purchase_date → datetime for bean age calc
            raw_pd = inv_row.get("purchase_date")
            if raw_pd and not pd.isna(raw_pd):
                pd_str = str(raw_pd).strip()
                if " " in pd_str:
                    pd_str = pd_str.split(" ")[0]
                pd_date = parse_date_yyyy_mm_dd(pd_str)
                if pd_date is not None:
                    session_data["purchase_date"] = datetime.combine(
                        pd_date, datetime.min.time()
                    )

        # 4) Required environment fields → float
        for key in self.required_env_keys:
            raw = session_data.get(key)
            if raw is None:
                missing_fields.append(key)
                self.inputs[key].setStyleSheet("border: 2px solid red;")
                continue
            try:
                session_data[key] = float(raw)
            except Exception:
                self.inputs[key].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    f"{key} must be a number.",
                )
                return

        # 5) Stage 0
        s0_temp_raw = session_data.get("stage_0_temp_f")
        if not s0_temp_raw:
            missing_fields.append("stage_0_temp_f")
            self.inputs["stage_0_temp_f"].setStyleSheet("border: 2px solid red;")
        else:
            try:
                session_data["stage_0_temp_f"] = float(s0_temp_raw)
            except Exception:
                self.inputs["stage_0_temp_f"].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Stage 0 temp must be a number.",
                )
                return

        s0_burn_raw = session_data.get("stage_0_burner_pct")
        if s0_burn_raw is not None:
            try:
                session_data["stage_0_burner_pct"] = float(s0_burn_raw)
            except Exception:
                self.inputs["stage_0_burner_pct"].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Stage 0 burner must be a number if provided.",
                )
                return

        session_data["stage_0_time_sec"] = 0.0

        # 6) Turning point (optional)
        tp_temp_raw = session_data.get("turning_point_temp_f")
        if tp_temp_raw:
            try:
                session_data["turning_point_temp_f"] = float(tp_temp_raw)
            except Exception:
                self.inputs["turning_point_temp_f"].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Turning point temp must be a number.",
                )
                return

        tp_mmss = session_data.get("turning_point_time_mmss")
        if tp_mmss:
            tp_sec = mmss_to_seconds(tp_mmss)
            if tp_sec is None:
                self.inputs["turning_point_time_mmss"].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Turning point time must be MMSS (e.g. 0430).",
                )
                return
            session_data["turning_point_time_sec"] = tp_sec

        session_data.pop("turning_point_time_mmss", None)

        # 7) Stages 1–9 temps / times / burners
        for i in range(1, 10):
            temp_key = f"stage_{i}_temp_f"
            t_raw = session_data.get(temp_key)
            if not t_raw:
                missing_fields.append(temp_key)
                self.inputs[temp_key].setStyleSheet("border: 2px solid red;")
            else:
                try:
                    session_data[temp_key] = float(t_raw)
                except Exception:
                    self.inputs[temp_key].setStyleSheet("border: 2px solid red;")
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"{temp_key} must be a number.",
                    )
                    return

            burn_key = f"stage_{i}_burner_pct"
            b_raw = session_data.get(burn_key)
            if b_raw is not None:
                try:
                    session_data[burn_key] = float(b_raw)
                except Exception:
                    self.inputs[burn_key].setStyleSheet("border: 2px solid red;")
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"{burn_key} must be a number if provided.",
                    )
                    return

            mmss_key = f"stage_{i}_time_mmss"
            mmss_raw = session_data.get(mmss_key)

            if i in (1, 6, 9):
                if not mmss_raw:
                    missing_fields.append(mmss_key)
                    self.inputs[mmss_key].setStyleSheet("border: 2px solid red;")
                else:
                    sec = mmss_to_seconds(mmss_raw)
                    if sec is None:
                        self.inputs[mmss_key].setStyleSheet("border: 2px solid red;")
                        QMessageBox.warning(
                            self,
                            "Invalid Input",
                            f"{mmss_key} must be MMSS (e.g. 0430).",
                        )
                        return
                    session_data[f"stage_{i}_time_sec"] = sec
            else:
                if mmss_raw:
                    sec = mmss_to_seconds(mmss_raw)
                    if sec is None:
                        self.inputs[mmss_key].setStyleSheet("border: 2px solid red;")
                        QMessageBox.warning(
                            self,
                            "Invalid Input",
                            f"{mmss_key} must be MMSS (e.g. 0430) if provided.",
                        )
                        return
                    session_data[f"stage_{i}_time_sec"] = sec

            session_data.pop(mmss_key, None)

        # 8) Optional end / sensory fields: attempt numeric casts if present
        optional_numeric_fields = [
            "end_temp_f",
            "agtron",
            "roasted_bean_moisture_pct",
            "clarity",
            "acidity",
            "body",
            "sweetness",
            "overall_rating",
        ]
        for key in optional_numeric_fields:
            raw = session_data.get(key)
            if raw is None:
                continue
            try:
                session_data[key] = float(raw)
            except Exception:
                self.inputs[key].setStyleSheet("border: 2px solid red;")
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    f"{key} must be a number if provided.",
                )
                return

        # 9) Check missing required fields
        if missing_fields:
            msg = "These fields are required:\n" + "\n".join(f"- {f}" for f in missing_fields)
            QMessageBox.warning(self, "Missing Required Fields", msg)
            return

        # 10) Run Core via callback
        try:
            predicted_session, confidence, ml_filled_fields = self._submit_callback(session_data)
        except Exception as e:
            QMessageBox.critical(self, "Core Error", f"Error running Core model:\n{e}")
            return

        # 11) Load roast_data.csv for history
        roast_df: Optional[pd.DataFrame] = None
        try:
            if os.path.exists(ROAST_PATH):
                roast_df = pd.read_csv(ROAST_PATH)
        except Exception as e:
            print("Error loading roast_data.csv:", e)

        # 12) Combined text + curve dialog (like Scout)
        open_core_report_dialog(
            self,
            predicted_session,
            confidence,
            ml_filled_fields,
            roast_df,
        )
        # 13) (no separate curve window needed – included in dialog above)

        # leave the input window open so you can tweak; uncomment to auto-close:
        # self.close()
