# gui/gui_inference_scout_input_session.py

from typing import Dict, Any, Optional, List, Callable, Tuple
import os
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFormLayout, QLineEdit, QPushButton,
    QMessageBox
)

from .gui_paths import ROAST_FILE, INV_FILE
from .gui_print_scout_report import open_scout_report_dialog


def mmss_to_seconds(mmss_str: Optional[str]) -> Optional[float]:
    """Convert MMSS string (e.g. '1230' -> 12*60 + 30) to seconds."""
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


class ScoutForm(QWidget):
    """
    GUI replacement for CLI option 3: Run Scout (Small) Prediction.

    run_scout_callback must accept a dict of session_data and return:
        (predicted_session, confidence, ml_filled_fields)
    """

    def __init__(
        self,
        run_scout_callback: Callable[[Dict[str, Any]], Any],
    ):
        super().__init__()
        self.setWindowTitle("Run Scout (Small) Prediction")
        self.run_scout_callback = run_scout_callback

        # keep references so child windows don't get GC'd
        self.child_windows: List[QWidget] = []

        main_layout = QVBoxLayout()

        # -----------------------------
        # Inventory dropdown (optional)
        # -----------------------------
        inv_row_layout = QHBoxLayout()
        inv_label = QLabel("Use inventory coffee (optional):")
        inv_row_layout.addWidget(inv_label)

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

        inv_row_layout.addWidget(self.inventory_combo)
        main_layout.addLayout(inv_row_layout)

        # -----------------------------
        # Main form
        # -----------------------------
        self.process_method_combo = QComboBox()
        self.process_method_combo.addItem("")  # blank
        self.process_method_combo.addItems(["washed", "natural", "honey", "other"])

        form = QFormLayout()
        self.inputs: Dict[str, QLineEdit] = {}

        def add_field(
            key: str,
            label: str,
            required: bool,
            default: Optional[str] = None,
        ):
            box = QLineEdit()
            self.inputs[key] = box

            # show default in gray (placeholder)
            if default is not None:
                box.setPlaceholderText(str(default))

            label_text = f"{label} *" if required else label
            form.addRow(label_text, box)

        # Process method row (if no inventory process)
        form.addRow("Process Method * (if no inventory)", self.process_method_combo)

        # Environment / metadata (with your usual defaults)
        add_field("room_temp_f", "Room Temp (°F)", True, "70")
        add_field("humidity_pct", "Humidity (%)", True, "50")
        add_field("room_bean_temp_f", "Starting Bean Temp (°F)", True, "70")
        add_field("green_bean_moisture_pct", "Green Bean Moisture (%)", True, "10")
        add_field("batch_weight_lbs", "Batch Weight (lbs)", True, "200")

        # Stage defaults (temps + key anchor times)
        stage_defaults = {
            0: "400",
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

        time_defaults = {
            1: "0400",
            6: "0800",
            9: "1100",
        }

        for i in range(10):
            add_field(
                f"stage_{i}_temp_f",
                f"Stage {i} Temp (°F)",
                True,
                stage_defaults.get(i),
            )

            if i in time_defaults:
                add_field(
                    f"stage_{i}_time_mmss",
                    f"Stage {i} Time (MMSS, e.g. {time_defaults[i]})",
                    True,
                    time_defaults[i],
                )

        main_layout.addLayout(form)

        # Submit button
        btn = QPushButton("Run Scout Prediction")
        btn.clicked.connect(self.on_submit)
        main_layout.addWidget(btn)

        self.setLayout(main_layout)

    # ----------------------------------------------------------
    # SUBMIT
    # ----------------------------------------------------------
    def on_submit(self):
        # Reset borders
        for box in self.inputs.values():
            box.setStyleSheet("")
        self.process_method_combo.setStyleSheet("")

        required_keys = (
            ["room_temp_f", "humidity_pct", "room_bean_temp_f",
             "green_bean_moisture_pct", "batch_weight_lbs"]
            + [f"stage_{i}_temp_f" for i in range(10)]
            + ["stage_1_time_mmss", "stage_6_time_mmss", "stage_9_time_mmss"]
        )

        data: Dict[str, Optional[str]] = {}
        missing: List[str] = []

        # use placeholder (default) when field left empty
        for key, box in self.inputs.items():
            val = box.text().strip()
            placeholder = box.placeholderText().strip()
            if val != "":
                final_val = val
            elif placeholder != "":
                final_val = placeholder
            else:
                final_val = None

            if key in required_keys and final_val is None:
                missing.append(key)
                box.setStyleSheet("border: 2px solid red;")

            data[key] = final_val

        # Process method logic
        inv_row = self.inventory_combo.currentData()
        explicit_pm = self.process_method_combo.currentText().strip()

        inv_pm = None
        if isinstance(inv_row, dict):
            inv_pm = inv_row.get("process_method", None)

        pm_required = False
        if inv_pm is None or (isinstance(inv_pm, float) and pd.isna(inv_pm)) or inv_pm == "":
            pm_required = True

        if pm_required and explicit_pm == "":
            missing.append("process_method")
            self.process_method_combo.setStyleSheet("border: 2px solid red;")

        if missing:
            msg = "These fields are required:\n" + "\n".join(f"- {k}" for k in missing)
            QMessageBox.warning(self, "Missing Required Fields", msg)
            return

        # -----------------------------
        # Build session_data
        # -----------------------------
        session_data: Dict[str, Any] = {}

        # Inventory metadata
        if isinstance(inv_row, dict):
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

        if "process_method" not in session_data:
            session_data["process_method"] = explicit_pm

        def float_or_none(v: Optional[str]) -> Optional[float]:
            if v is None:
                return None
            try:
                return float(v)
            except ValueError:
                return None

        # environment
        session_data["room_temp_f"] = float_or_none(data["room_temp_f"])
        session_data["humidity_pct"] = float_or_none(data["humidity_pct"])
        session_data["room_bean_temp_f"] = float_or_none(data["room_bean_temp_f"])
        session_data["green_bean_moisture_pct"] = float_or_none(data["green_bean_moisture_pct"])
        session_data["batch_weight_lbs"] = float_or_none(data["batch_weight_lbs"])

        # stage temps
        for i in range(10):
            k = f"stage_{i}_temp_f"
            session_data[k] = float_or_none(data[k])

        # Anchor times MMSS → seconds
        session_data["stage_1_time_sec"] = mmss_to_seconds(data.get("stage_1_time_mmss"))
        session_data["stage_6_time_sec"] = mmss_to_seconds(data.get("stage_6_time_mmss"))
        session_data["stage_9_time_sec"] = mmss_to_seconds(data.get("stage_9_time_mmss"))

        # -----------------------------
        # Run model
        # -----------------------------
        try:
            predicted_session, confidence, ml_filled_fields = self.run_scout_callback(session_data)
        except Exception as e:
            QMessageBox.critical(self, "Scout Error", f"Error running Scout model:\n{e}")
            return


        # -----------------------------
        # Load roast_data.csv for history
        # -----------------------------
        roast_df: Optional[pd.DataFrame] = None
        try:
            if os.path.exists(ROAST_FILE):
                roast_df = pd.read_csv(ROAST_FILE)
        except Exception as e:
            print("Error loading roast_data.csv:", e)

        # -----------------------------
        # Combined text + curve dialog
        # -----------------------------
        open_scout_report_dialog(
            self,
            predicted_session,
            confidence,
            ml_filled_fields,
            roast_df,
        )
