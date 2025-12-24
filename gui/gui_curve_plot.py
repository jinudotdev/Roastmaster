# gui/gui_curve_plot.py

from typing import Optional, Dict, Any, List

import pandas as pd
from PySide6.QtWidgets import QMainWindow
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


def extract_curve_from_row(row: pd.Series) -> tuple[List[float], List[float]]:
    """
    Build time/temperature lists from a roast_data row.
    Always returns lists (may be empty); caller decides whether to plot.
    """
    times: List[float] = []
    temps: List[float] = []

    for i in range(10):
        t_key = f"stage_{i}_time_sec"
        y_key = f"stage_{i}_temp_f"
        t = row.get(t_key)
        y = row.get(y_key)
        if pd.notna(t) and pd.notna(y):
            times.append(float(t) / 60.0)
            temps.append(float(y))

    return times, temps


def extract_curve_from_session(session_data: Dict[str, Any]) -> tuple[List[float], List[float]]:
    """
    Build time/temperature lists from a predicted_session dict.
    Always returns lists (may be empty); caller decides whether to plot.
    """
    times: List[float] = []
    temps: List[float] = []

    for i in range(10):
        t_key = f"stage_{i}_time_sec"
        y_key = f"stage_{i}_temp_f"
        t = session_data.get(t_key)
        y = session_data.get(y_key)
        if t is not None and y is not None:
            times.append(float(t) / 60.0)
            temps.append(float(y))

    return times, temps


class CurvePlotWindow(QMainWindow):
    def __init__(self, roast_df: Optional[pd.DataFrame], predicted_session: Dict[str, Any]):
        super().__init__()
        self.setWindowTitle("Roast Curve – Scout Prediction vs History")

        canvas = FigureCanvasQTAgg(Figure(figsize=(6, 4)))
        self.setCentralWidget(canvas)
        ax = canvas.figure.add_subplot(111)

        # Historical curves
        if roast_df is not None and len(roast_df) > 0:
            for _, row in roast_df.iterrows():
                t, y = extract_curve_from_row(row)
                if len(t) >= 2:
                    ax.plot(t, y, color="black", alpha=0.35)

        # Predicted curve
        if predicted_session:
            t_pred, y_pred = extract_curve_from_session(predicted_session)
            if len(t_pred) >= 2:
                ax.plot(t_pred, y_pred, color="red", linewidth=2)

        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Bean Temp (°F)")
        ax.set_title("Scout Predicted Roast vs Historical Roasts")
        ax.grid(True, alpha=0.2)

        canvas.draw()
