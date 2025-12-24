# gui/gui_capture_roast_session.py

import os
import csv
from uuid import uuid4
from datetime import date, datetime
from typing import Dict, Any, Optional

import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QScrollArea, QLabel, QComboBox
)

from scripts_utility.paths import DATA_FILE
from scripts_utility.master_order import MASTER_ORDER


INV_FILE = os.path.join("data", "coffee_inventory.csv")


def mmss_to_seconds(mmss_str: Optional[str]) -> Optional[float]:
    """Convert MMSS (e.g. '0400') to seconds, None if blank/invalid."""
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


class CaptureRoastSessionGUI(QWidget):
    """
    GUI version of the "Add Roast Data" flow from main.py:
      - optional inventory selection for bean metadata
      - Stage 0 (charge)
      - Turning point
      - Stages 1–9
      - Sensory scores
    Appends a row to roast_data.csv with MASTER_ORDER columns.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Roast Data")
        self.resize(900, 750)

        self.inputs: Dict[str, QLineEdit] = {}
        self.inventory_combo: QComboBox

        outer_layout = QVBoxLayout()

        # ==========================
        # Inventory selection (top)
        # ==========================
        inv_row = QHBoxLayout()
        inv_label = QLabel("Use inventory coffee (optional):")
        inv_row.addWidget(inv_label)

        self.inventory_combo = QComboBox()
        self.inventory_combo.addItem("— None —", userData=None)

        if os.path.exists(INV_FILE):
            try:
                inv_df = pd.read_csv(INV_FILE)
                for _, row in inv_df.iterrows():
                    supplier = row.get("supplier", "?")
                    country = row.get("country", "?")
                    region = row.get("region", "")
                    desc = f"{supplier} - {country} {region}".strip()

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

                    self.inventory_combo.addItem(desc, userData=row.to_dict())
            except Exception as e:
                print("Error loading coffee_inventory.csv:", e)

        inv_row.addWidget(self.inventory_combo)
        outer_layout.addLayout(inv_row)

        # ==========================
        # Scrollable form
        # ==========================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        form_layout = QFormLayout()
        inner.setLayout(form_layout)

        scroll.setWidget(inner)
        outer_layout.addWidget(scroll)

        def add_field(key: str, label: str, placeholder: str = ""):
            box = QLineEdit()
            if placeholder:
                box.setPlaceholderText(placeholder)
            self.inputs[key] = box
            form_layout.addRow(label, box)

        # -------------------------------
        # Roast date
        # -------------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Roast Info"))
        form_layout.addRow(QLabel(""))

        add_field("roast_date", "Roast Date [Blank = Today] (YYYY-MM-DD)")

        # -------------------------------
        # Stage 0 (Charge)
        # -------------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Stage 0 - at Charge (time is always 00:00)"))
        form_layout.addRow(QLabel(""))

        add_field("stage_0_temp_f", "Stage 0 - Bean Temp (°F) [Required]", "400")
        add_field("stage_0_burner_pct", "Stage 0 - Burner % [Optional]")

        # -------------------------------
        # Turning Point
        # -------------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Turning Point"))
        form_layout.addRow(QLabel(""))

        add_field("turning_point_temp_f", "Turning Point - Bean Temp (°F)")
        add_field(
            "turning_point_time_mmss",
            "Turning Point - Time (MMSS, e.g. 1230 for 12:30)"
        )

        # -------------------------------
        # Stages 1–9
        # -------------------------------
        for i in range(1, 10):
            form_layout.addRow(QLabel(""))
            if i == 1:
                form_layout.addRow(QLabel("Stage 1"))
            elif i == 9:
                form_layout.addRow(QLabel("Stage 9 (End Stage)"))
            else:
                form_layout.addRow(QLabel(f"Stage {i}"))

            form_layout.addRow(QLabel(""))

            temp_label = (
                f"Stage {i} - Bean Temp (°F) [Required]"
                if i == 9
                else f"Stage {i} - Bean Temp (°F) [Optional]"
            )
            add_field(f"stage_{i}_temp_f", temp_label)
            add_field(f"stage_{i}_burner_pct", f"Stage {i} - Burner % [Optional]")
            add_field(
                f"stage_{i}_time_mmss",
                "Time (MMSS, e.g. 1230 for 12:30)"
            )

        # -------------------------------
        # Sensory scores
        # -------------------------------
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel("Sensory Scores (optional, 1–10, 10 is best)"))
        form_layout.addRow(QLabel(""))

        add_field("clarity", "Clarity")
        add_field("acidity", "Acidity")
        add_field("body", "Body")
        add_field("sweetness", "Sweetness")
        add_field("overall_rating", "Overall")

        # (CLI has Comments, but MASTER_ORDER doesn’t, so we skip it here)

        # -------------------------------
        # Buttons
        # -------------------------------
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Roast")
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self.on_save)
        btn_cancel.clicked.connect(self.close)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        outer_layout.addLayout(btn_row)

        self.setLayout(outer_layout)

    # ----------------------------------------------------------
    # SAVE
    # ----------------------------------------------------------
    def on_save(self):
        # Reset styles
        for box in self.inputs.values():
            box.setStyleSheet("")

        session_data: Dict[str, Any] = {}

        # Pull form values
        for key, box in self.inputs.items():
            txt = box.text().strip()
            session_data[key] = txt if txt != "" else None

        # Roast date blank → today
        roast_date_str = session_data.get("roast_date")
        if not roast_date_str:
            roast_date = date.today()
            session_data["roast_date"] = roast_date.isoformat()
        else:
            rd = parse_date_yyyy_mm_dd(roast_date_str)
            roast_date = rd if rd is not None else date.today()
            session_data["roast_date"] = roast_date.isoformat()

        # Required fields: Stage 0 temp, Stage 9 temp
        missing = []
        for req_key in ("stage_0_temp_f", "stage_9_temp_f"):
            if not session_data.get(req_key):
                missing.append(req_key)
                self.inputs[req_key].setStyleSheet("border: 2px solid red;")

        if missing:
            msg = (
                "These fields are required:\n" +
                "\n".join(f"- {k}" for k in missing)
            )
            QMessageBox.warning(self, "Missing Required Fields", msg)
            return

        # Inventory metadata -> session_data
        inv_row = self.inventory_combo.currentData()
        if isinstance(inv_row, dict):
            # map inventory columns to roast_data fields
            if "supplier" in inv_row:
                session_data["supplier"] = inv_row["supplier"]
            if "country" in inv_row:
                session_data["country"] = inv_row["country"]
            if "region" in inv_row:
                session_data["region"] = inv_row["region"]
            if "altitude_meters" in inv_row:
                session_data["altitude_meters"] = inv_row["altitude_meters"]
            if "variety" in inv_row:
                session_data["variety"] = inv_row["variety"]
            if "process_method" in inv_row and not pd.isna(inv_row["process_method"]):
                session_data["process_method"] = inv_row["process_method"]
            if "purchase_date" in inv_row:
                session_data["purchase_date"] = inv_row["purchase_date"]

        # bean_age_days_at_roast (if we have both dates)
        purchase_date = parse_date_yyyy_mm_dd(session_data.get("purchase_date"))
        if purchase_date and roast_date:
            session_data["bean_age_days_at_roast"] = (roast_date - purchase_date).days

        # Stage times MMSS → seconds
        # Stage 0 time is always 0
        session_data["stage_0_time_sec"] = 0.0

        for i in range(1, 10):
            mmss_key = f"stage_{i}_time_mmss"
            mmss_val = session_data.get(mmss_key)
            if mmss_val:
                session_data[f"stage_{i}_time_sec"] = mmss_to_seconds(mmss_val)
            # Remove *_time_mmss placeholders
            session_data.pop(mmss_key, None)

        # Turning point time MMSS → turning_point_time_sec
        tp_mmss = session_data.get("turning_point_time_mmss")
        if tp_mmss:
            session_data["turning_point_time_sec"] = mmss_to_seconds(tp_mmss)
        session_data.pop("turning_point_time_mmss", None)

        # Build record in MASTER_ORDER
        csv_file = DATA_FILE.with_suffix(".csv")

        if csv_file.exists():
            with csv_file.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                line_count = max(0, len(rows) - 1)  # minus header if present
        else:
            line_count = 0

        try:
            safe_record = {
                field: (
                    str(session_data.get(field, "NaN"))
                    if session_data.get(field) not in (None, "")
                    else "NaN"
                )
                for field in MASTER_ORDER
            }
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error building record:\n{e}")
            return

        # Inject id if missing
        if "id" in MASTER_ORDER:
            if not session_data.get("id"):
                safe_record["id"] = str(uuid4())

        # Inject line_number if field exists
        if "line_number" in MASTER_ORDER:
            safe_record["line_number"] = str(line_count + 1)

        if len(safe_record) != len(MASTER_ORDER):
            QMessageBox.critical(
                self,
                "Save Error",
                f"Record has {len(safe_record)} fields, expected {len(MASTER_ORDER)}.",
            )
            return

        try:
            file_exists = csv_file.exists()
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            # IMPORTANT: newline="" to avoid row-gluing / extra blank lines
            with csv_file.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=MASTER_ORDER, delimiter=",")
                if not file_exists:
                    writer.writeheader()
                writer.writerow(safe_record)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error writing CSV:\n{e}")
            return

        QMessageBox.information(
            self,
            "Roast Saved",
            f"Roast appended to {csv_file} as line {line_count + 1}.",
        )
        self.close()
