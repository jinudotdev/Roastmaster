# gui/gui_print_scout_report.py

from typing import Dict, Any, Optional

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


def blue(x: str) -> str:
    """Wrap text in blue HTML span."""
    return f'<span style="color:#1e90ff; font-weight:bold;">{x}</span>'


def _fmt_value(
    session: Dict[str, Any],
    key: str,
    predicted_keys: set,
    *,
    suffix: str = "",
    time_fmt: bool = False,
) -> str:
    """Format a single value, with optional time conversion and blue if predicted."""
    val = session.get(key)

    if val is None or str(val).lower() == "nan":
        txt = "n/a"
    else:
        if time_fmt:
            # seconds -> MM:SS
            try:
                secs = float(val)
                mins = int(secs // 60)
                sec_int = int(secs % 60)
                txt = f"{mins:02d}:{sec_int:02d}"
            except Exception:
                txt = str(val)
        else:
            if isinstance(val, (float, int)):
                txt = f"{float(val):.1f}"
            else:
                txt = str(val)

    if key in predicted_keys and txt != "n/a":
        txt = blue(txt)

    return f"{txt}{suffix}"


def build_scout_report_text(
    session: Dict[str, Any],
    ml_filled_fields: Dict[str, Any],
    confidence: Optional[float] = None,
) -> str:
    """
    Build HTML that mimics the CLI-style Scout output:
      Supplier / country block, then single-line Stage rows.
      Predicted values are blue.
    """
    predicted_keys = set(ml_filled_fields.keys())
    lines: list[str] = []

    lines.append("<h3>Scout Model Prediction</h3>")

    if confidence is not None:
        try:
            lines.append(f"Model Confidence: {float(confidence):.3f}")
        except Exception:
            lines.append(f"Model Confidence: {confidence}")
        lines.append("<br>")

    # Bean / metadata
    lines.append("Supplier: " + _fmt_value(session, "supplier", predicted_keys))
    lines.append("Country: " + _fmt_value(session, "country", predicted_keys))
    lines.append("Region: " + _fmt_value(session, "region", predicted_keys))
    lines.append("Variety: " + _fmt_value(session, "variety", predicted_keys))
    lines.append(
        "Altitude: "
        + _fmt_value(session, "altitude_meters", predicted_keys, suffix=" m")
    )
    lines.append(
        "Batch Weight: "
        + _fmt_value(session, "batch_weight_lbs", predicted_keys, suffix=" lbs")
    )

    lines.append("<br>")

    # Stages 0–9 in one line each, CLI style
    for i in range(10):
        temp_key = f"stage_{i}_temp_f"
        burner_key = f"stage_{i}_burner_pct"
        time_key = f"stage_{i}_time_sec"

        temp_txt = _fmt_value(session, temp_key, predicted_keys)
        burner_txt = _fmt_value(session, burner_key, predicted_keys)
        time_txt = _fmt_value(session, time_key, predicted_keys, time_fmt=True)

        lines.append(
            f"Stage {i} - Temp: {temp_txt} - Burner: {burner_txt} - Time: {time_txt}"
        )

    # Compact: one <br> per line, no extra blank lines
    return "<br>".join(lines)


class ScoutReportDialog(QDialog):
    """
    Combined text + chart window for Scout prediction.
    Left: CLI-style HTML report (with blue predicted values).
    Right: roast curve (historical + predicted).
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        session: Dict[str, Any],
        confidence: Optional[float],
        ml_filled_fields: Dict[str, Any],
        roast_df: Optional[pd.DataFrame] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Scout Prediction – Report & Curve")
        self.resize(1000, 700)

        main_layout = QHBoxLayout(self)

        # ------- Left: Text report -------
        text = QTextEdit()
        text.setReadOnly(True)
        html = build_scout_report_text(session, ml_filled_fields, confidence)
        text.setHtml(html)

        left_layout = QVBoxLayout()
        left_layout.addWidget(text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        left_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        left_container = QWidget()
        left_container.setLayout(left_layout)

        # ------- Right: Curve plot -------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        canvas = FigureCanvasQTAgg(Figure(figsize=(5, 4)))
        right_layout.addWidget(canvas)

        ax = canvas.figure.add_subplot(111)

        # Historical curves
        if roast_df is not None and len(roast_df) > 0:
            for _, row in roast_df.iterrows():
                t, y = extract_curve_from_row(row)
                if t is not None and y is not None and len(t) > 1:
                    ax.plot(t, y, alpha=0.25)

        # Predicted curve
        t_pred, y_pred = extract_curve_from_session(session)
        if t_pred is not None and y_pred is not None and len(t_pred) > 1:
            ax.plot(t_pred, y_pred, linewidth=2)

        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Bean Temp (°F)")
        ax.set_title("Scout Predicted Roast vs Historical Roasts")
        ax.grid(True, alpha=0.2)

        canvas.draw()

        # ------- Assemble -------
        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_container, 1)


def open_scout_report_dialog(
    parent: Optional[QWidget],
    session: Dict[str, Any],
    confidence: Optional[float],
    ml_filled_fields: Dict[str, Any],
    roast_df: Optional[pd.DataFrame] = None,
) -> None:
    dlg = ScoutReportDialog(parent, session, confidence, ml_filled_fields, roast_df)
    dlg.exec()
