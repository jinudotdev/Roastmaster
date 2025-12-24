# gui/gui_main_window.py

from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox
)

from .gui_inference_scout_input_session import ScoutForm
from .gui_capture_roast_session import CaptureRoastSessionGUI
from .gui_edit_coffee_inventory import CoffeeInventoryWindow
from .gui_inference_core_input_session import CoreInputSessionWindow


class RoastMasterUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RoastMaster Control Panel")
        self.setMinimumWidth(380)

        self.scout_form: Optional[ScoutForm] = None
        self.inventory_window: Optional[CoffeeInventoryWindow] = None

        layout = QVBoxLayout()

        buttons = [
            ("1. Add Roast Data", self.add_roast_data),
            ("2. Add/Remove Coffee from Inventory", self.edit_coffee_inventory),
            ("3. Run Scout (Small) Prediction on Given Data", self.run_scout),
            ("4. Rebuild Scout (Small) Model with Roast Data", self.rebuild_scout),
            ("5. Run Core (Big) Prediction on Given Data", self.run_core),
            ("6. Rebuild Core (Big) Model with Roast Data", self.rebuild_core),
        ]

        for label, handler in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet("padding: 10px; font-size: 13px;")
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        self.setLayout(layout)

        # Keep child windows alive
        self._child_windows = []

    # ----------------------------------------------------------
    # 1) Add Roast Data — full GUI (CaptureRoastSessionGUI)
    # ----------------------------------------------------------
    def add_roast_data(self):
        win = CaptureRoastSessionGUI()
        win.show()
        self._child_windows.append(win)

    # ----------------------------------------------------------
    # 2) Inventory editor — full GUI (CoffeeInventoryWindow)
    # ----------------------------------------------------------
    def edit_coffee_inventory(self):
        if self.inventory_window is None or not self.inventory_window.isVisible():
            self.inventory_window = CoffeeInventoryWindow()
        self.inventory_window.show()
        self.inventory_window.raise_()
        self.inventory_window.activateWindow()

    # ----------------------------------------------------------
    # 3) Run Scout — GUI using real infer_scout
    # ----------------------------------------------------------
    def run_scout(self):
        from scripts_main.infer_scout import infer_scout
        from scripts_utility.master_order import SCOUT_FEATURE_ORDER

        def run_scout_model(session_data: Dict[str, Any]):
            flat_inputs = {key: session_data.get(key) for key in SCOUT_FEATURE_ORDER}
            ml_filled_fields, confidence = infer_scout(flat_inputs)

            predicted_session: Dict[str, Any] = dict(session_data)
            predicted_session.update(flat_inputs)
            predicted_session.update(ml_filled_fields)
            # return everything the GUI needs
            return predicted_session, confidence, ml_filled_fields

        self.scout_form = ScoutForm(run_scout_model)
        self.scout_form.show()
        self.scout_form.raise_()
        self.scout_form.activateWindow()

    # ----------------------------------------------------------
    # 4) Rebuild Scout
    # ----------------------------------------------------------
    def rebuild_scout(self):
        try:
            from scripts_main.train_scout import main as train_scout
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Rebuild Scout",
                f"Could not import train_scout:\n{e}",
            )
            return

        try:
            train_scout()
            QMessageBox.information(
                self,
                "Rebuild Scout",
                "Scout model training completed.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Rebuild Scout Error",
                f"Error while training Scout model:\n{e}",
            )

    # ----------------------------------------------------------
    # 5) Run Core — GUI (CoreInputSessionWindow handles report+curve)
    # ----------------------------------------------------------
    def run_core(self):
        try:
            from scripts_main.infer_core import infer_core
            from scripts_utility.master_order import CORE_FEATURE_ORDER
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Core Model",
                f"Could not import Core inference functions:\n{e}",
            )
            return

        def run_core_model(session_data: Dict[str, Any]):
            # Build flat input dict in the same feature order Core expects
            flat_inputs = {key: session_data.get(key) for key in CORE_FEATURE_ORDER}
            ml_filled_fields, confidence = infer_core(flat_inputs)

            predicted_session: Dict[str, Any] = dict(session_data)
            predicted_session.update(flat_inputs)
            predicted_session.update(ml_filled_fields)

            # CoreInputSessionWindow expects (predicted_session, confidence, ml_filled_fields)
            return predicted_session, confidence, ml_filled_fields

        win = CoreInputSessionWindow(run_core_model)
        win.show()
        win.raise_()
        win.activateWindow()
        self._child_windows.append(win)

    # ----------------------------------------------------------
    # 6) Rebuild Core
    # ----------------------------------------------------------
    def rebuild_core(self):
        try:
            from scripts_main.train_core import main as train_core
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Rebuild Core",
                f"Could not import train_core:\n{e}",
            )
            return

        try:
            train_core()
            QMessageBox.information(
                self,
                "Rebuild Core",
                "Core model training completed.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Rebuild Core Error",
                f"Error while training Core model:\n{e}",
            )
