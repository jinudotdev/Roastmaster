# gui/gui_print_core_report.py

from typing import Dict, Any, Optional
import math
from scripts_utility.capture import seconds_to_mmss
import pandas as pd
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from .gui_curve_plot import (
    extract_curve_from_row,
    extract_curve_from_session,
)


def _blue_html(text: str) -> str:
    return f'<span style="color:#1e90ff; font-weight:bold;">{text}</span>'


def _is_blank_or_nan(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == "" or v.strip().lower() == "nan"
    if isinstance(v, float):
        return math.isnan(v)
    return False


def _fmt_value(
    value: Any,
    key: str,
    predicted_keys: set[str],
    suffix: str = "",
    round_to: Optional[int] = None,
) -> str:
    if _is_blank_or_nan(value):
        txt = "n/a"
    else:
        if isinstance(value, (float, int)) and round_to is not None:
            value = round(float(value), round_to)
        txt = str(value)

    if key in predicted_keys and txt != "n/a":
        txt = _blue_html(txt)

    if suffix and txt != "n/a":
        txt = f"{txt}{suffix}"

    return txt


def _season_from_day(day: int) -> str:
    # Same logic as CLI
    if 80 <= day < 172:
        return "Spring"
    elif 172 <= day < 266:
        return "Summer"
    elif 266 <= day < 355:
        return "Fall"
    else:
        return "Winter"


def build_core_report_html(
    session_data: Dict[str, Any],
    confidence: Optional[Dict[str, float]],
    ml_filled_fields: Dict[str, Any],
) -> str:
    predicted_keys: set[str] = set(ml_filled_fields.keys()) if ml_filled_fields else set()

    lines: list[str] = []
    lines.append("<h3>Core Model Prediction</h3>")

    # --- Confidence (short version) ---
    if isinstance(confidence, dict) and confidence:
        vals = list(confidence.values())
        mean_val = sum(vals) / len(vals)
        lines.append(f"<b>Avg confidence (all targets):</b> {mean_val:.3f}<br>")

    # --- Bean summary header (like CLI "Using: ...") ---
    supplier = session_data.get("supplier")
    country = session_data.get("country")
    region = session_data.get("region")
    variety = session_data.get("variety")
    process = session_data.get("process_method")
    altitude = session_data.get("altitude_meters")
    purchase_date = session_data.get("purchase_date")

    summary_parts = []
    if supplier:
        summary_parts.append(str(supplier))
    if country:
        summary_parts.append(str(country))
    if region:
        summary_parts.append(str(region))
    if variety:
        if process:
            summary_parts.append(f"({variety}, {process})")
        else:
            summary_parts.append(f"({variety})")
    elif process:
        summary_parts.append(f"({process})")
    if altitude:
        summary_parts.append(f"{altitude}m")
    if purchase_date:
        summary_parts.append(f"purchased {purchase_date}")

    if summary_parts:
        lines.append("Using: " + " – ".join(summary_parts) + "<br><br>")

    # --- Metadata ---
    meta_fields = [
        ("supplier", "Supplier Name"),
        ("country", "Country"),
        ("altitude_meters", "Altitude"),
        ("variety", "Variety"),
        ("region", "Region"),
    ]
    for key, label in meta_fields:
        lines.append(
            f"<b>{label}:</b> "
            f"{_fmt_value(session_data.get(key), key, predicted_keys)}<br>"
        )

    # --- Roast Day & Bean Age ---
    roast_day = session_data.get("roast_date")
    bean_age = session_data.get("bean_age_days_at_roast")

    if roast_day is not None and not _is_blank_or_nan(roast_day):
        try:
            day_int = int(roast_day)
            season = _season_from_day(day_int)
            rd_txt = _fmt_value(day_int, "roast_date", predicted_keys)
            lines.append(f"<b>Roast Day of Year:</b> {rd_txt} ({season})<br>")
        except Exception:
            rd_txt = _fmt_value(roast_day, "roast_date", predicted_keys)
            lines.append(f"<b>Roast Day of Year:</b> {rd_txt}<br>")

    if bean_age is not None and not _is_blank_or_nan(bean_age):
        lines.append(
            f"<b>Bean Age in Days:</b> "
            f"{_fmt_value(bean_age, 'bean_age_days_at_roast', predicted_keys)}<br>"
        )

    lines.append("<br>")

    # --- Environment ---
    env_fields = [
        ("room_temp_f", "Room Temp", "", None),
        ("humidity_pct", "Room Humidity", "", None),
        ("bean_temp_start_f", "Bean Temp", "", None),
        ("green_bean_moisture_pct", "Bean Humidity", "", None),
        ("batch_weight_lbs", "Batch Weight", " lbs", None),
    ]
    for key, label, suffix, rnd in env_fields:
        lines.append(
            f"<b>{label}:</b> "
            f"{_fmt_value(session_data.get(key), key, predicted_keys, suffix=suffix, round_to=rnd)}<br>"
        )

    lines.append("<br>")

    # --- Stages 0–9 + Turning Point after Stage 0 ---
    for i in range(10):
        temp_key = f"stage_{i}_temp_f"
        burner_key = f"stage_{i}_burner_pct"
        time_key = f"stage_{i}_time_sec"

        temp_val = session_data.get(temp_key)
        burner_val = session_data.get(burner_key)
        time_val = session_data.get(time_key)

        # Convert seconds → MM:SS like CLI
        if time_val is not None and not _is_blank_or_nan(time_val):
            try:
                time_str = seconds_to_mmss(float(time_val))
            except Exception:
                time_str = str(time_val)
        else:
            time_str = None

        lines.append(f"<b>Stage {i}:</b>")
        lines.append(
            f" Temp: {_fmt_value(temp_val, temp_key, predicted_keys, round_to=1)}"
            f" – Burner: {_fmt_value(burner_val, burner_key, predicted_keys, round_to=1)}"
            f" – Time: {_fmt_value(time_str, time_key, predicted_keys)}<br>"
        )

        # Turning point printed once after Stage 0
        if i == 0:
            tp_temp_key = "turning_point_temp_f"
            tp_time_key = "turning_point_time_sec"

            tp_temp = session_data.get(tp_temp_key)
            tp_time = session_data.get(tp_time_key)

            # zero values treated as None like CLI
            if tp_temp in (0, 0.0):
                tp_temp = None
            if tp_time in (0, 0.0):
                tp_time = None

            if tp_time is not None and not _is_blank_or_nan(tp_time):
                try:
                    tp_time_str = seconds_to_mmss(float(tp_time))
                except Exception:
                    tp_time_str = str(tp_time)
            else:
                tp_time_str = None

            lines.append(
                f"&nbsp;&nbsp;Turning Point – Temp: "
                f"{_fmt_value(tp_temp, tp_temp_key, predicted_keys, round_to=1)}"
                f" – Time: {_fmt_value(tp_time_str, tp_time_key, predicted_keys)}<br>"
            )

    lines.append("<br>")

    # --- End of Roast ---
    end_fields = [
        ("end_temp_f", "End of Roast"),
        ("agtron", "Agtron"),
        ("roasted_bean_moisture_pct", "Post Roast Moisture"),
    ]
    for key, label in end_fields:
        val = session_data.get(key)
        lines.append(
            f"<b>{label}:</b> "
            f"{_fmt_value(val, key, predicted_keys, round_to=1)}<br>"
        )

    # --- Sensory Scores ---
    lines.append("<br>")
    sens_fields = [
        ("clarity", "Clarity"),
        ("acidity", "Acidity"),
        ("body", "Body"),
        ("sweetness", "Sweetness"),
        ("overall_rating", "Overall"),
        ("comments", "Comments"),
    ]
    for key, label in sens_fields:
        lines.append(
            f"<b>{label}:</b> "
            f"{_fmt_value(session_data.get(key), key, predicted_keys)}<br>"
        )

    return "".join(lines)


class CoreReportDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        session_data: Dict[str, Any],
        confidence: Optional[Dict[str, float]],
        ml_filled_fields: Dict[str, Any],
        roast_df: Optional[pd.DataFrame] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Core Prediction – Report & Curve")
        self.resize(1000, 700)

        main_layout = QHBoxLayout(self)

        # ------- Left: text report -------
        text = QTextEdit()
        text.setReadOnly(True)
        html = build_core_report_html(session_data, confidence, ml_filled_fields)
        text.setHtml(html)

        left_layout = QVBoxLayout()
        left_layout.addWidget(text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        left_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        left_container = QWidget()
        left_container.setLayout(left_layout)

        # ------- Right: curve plot -------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        canvas = FigureCanvasQTAgg(Figure(figsize=(5, 4)))
        right_layout.addWidget(canvas)

        ax = canvas.figure.add_subplot(111)

        # Historical curves (if any)
        if roast_df is not None and len(roast_df) > 0:
            for _, row in roast_df.iterrows():
                t, y = extract_curve_from_row(row)
                if t is not None and y is not None and len(t) > 1:
                    ax.plot(t, y, alpha=0.25)

        # Predicted curve from this Core session
        t_pred, y_pred = extract_curve_from_session(session_data)
        if t_pred is not None and y_pred is not None and len(t_pred) > 1:
            ax.plot(t_pred, y_pred, linewidth=2)

        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Bean Temp (°F)")
        ax.set_title("Core Predicted Roast vs Historical Roasts")
        ax.grid(True, alpha=0.2)

        canvas.draw()

        # ------- Assemble -------
        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_container, 1)


def open_core_report_dialog(
    parent: Optional[QWidget],
    session_data: Dict[str, Any],
    confidence: Optional[Dict[str, float]],
    ml_filled_fields: Dict[str, Any],
    roast_df: Optional[pd.DataFrame] = None,
) -> None:
    dlg = CoreReportDialog(parent, session_data, confidence, ml_filled_fields, roast_df)
    dlg.exec()  # modal, exactly like Scout
