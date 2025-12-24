# gui/gui_edit_coffee_inventory.py

import os
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt


INVENTORY_PATH = os.path.join("data", "coffee_inventory.csv")

COLUMNS = [
    "id",
    "supplier",
    "country",
    "region",
    "altitude_meters",
    "variety",
    "process_method",
    "purchase_date",
]


def load_inventory_df() -> pd.DataFrame:
    if os.path.exists(INVENTORY_PATH):
        try:
            df = pd.read_csv(INVENTORY_PATH)
            # ensure all columns exist
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS]
        except Exception:
            # fall back to empty
            pass
    return pd.DataFrame(columns=COLUMNS)


def save_inventory_df(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(INVENTORY_PATH), exist_ok=True)
    df.to_csv(INVENTORY_PATH, index=False)


class InventoryAddDialog(QDialog):
    """
    Modal dialog to add a new coffee inventory row.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Coffee to Inventory")

        self.inputs = {}

        layout = QVBoxLayout()
        form = QFormLayout()

        def add_line(key: str, label: str):
            box = QLineEdit()
            self.inputs[key] = box
            form.addRow(label, box)

        add_line("supplier", "Supplier")
        add_line("country", "Country")
        add_line("region", "Region")
        add_line("altitude_meters", "Altitude (m)")
        add_line("variety", "Variety")

        # Process method as dropdown
        self.process_box = QComboBox()
        self.process_box.addItem("")  # blank
        self.process_box.addItems(["Natural", "Washed", "Honey", "Wet-Hulled", "Other"])
        form.addRow("Process Method", self.process_box)

        add_line("purchase_date", "Purchase Date (YYYY-MM-DD)")

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("Add")
        btn_cancel = QPushButton("Cancel")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)
        self.setLayout(layout)

    def get_data(self) -> dict:
        data = {}
        for k, box in self.inputs.items():
            data[k] = box.text().strip()

        pm = self.process_box.currentText().strip()
        data["process_method"] = pm if pm != "" else None

        return data


class CoffeeInventoryWindow(QWidget):
    """
    GUI editor for coffee inventory: list/add/remove.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coffee Inventory")
        self.resize(800, 400)

        self.df: pd.DataFrame = load_inventory_df()

        main_layout = QVBoxLayout()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        # Use the explicit enum for Pylance / type checkers
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add Coffee")
        btn_remove = QPushButton("Remove Selected")
        btn_close = QPushButton("Close")

        btn_add.clicked.connect(self.on_add)
        btn_remove.clicked.connect(self.on_remove)
        btn_close.clicked.connect(self.close)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addWidget(btn_close)

        main_layout.addLayout(btn_row)
        self.setLayout(main_layout)

        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.df))
        for row_idx, (_, row) in enumerate(self.df.iterrows()):
            for col_idx, col in enumerate(COLUMNS):
                val = "" if pd.isna(row.get(col)) else str(row.get(col))
                item = QTableWidgetItem(val)
                if col == "id":
                    # ID should not be editable
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def on_add(self):
        dlg = InventoryAddDialog(self)
        # Use DialogCode.Accepted for type checker happiness
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new = dlg.get_data()

        # basic required fields check
        if not new["supplier"] or not new["country"]:
            QMessageBox.warning(
                self,
                "Missing data",
                "Supplier and Country are required.",
            )
            return

        # Determine next id
        if self.df.empty:
            next_id = 1
        else:
            try:
                next_id = int(self.df["id"].max()) + 1
            except Exception:
                next_id = 1

        row = {
            "id": next_id,
            "supplier": new["supplier"],
            "country": new["country"],
            "region": new["region"],
            "altitude_meters": new["altitude_meters"],
            "variety": new["variety"],
            "process_method": new["process_method"],
            "purchase_date": new["purchase_date"],
        }

        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        save_inventory_df(self.df)
        self.refresh_table()

    def on_remove(self):
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.information(self, "Remove", "No row selected.")
            return

        # Remove based on unique IDs of selected rows
        row_indices = sorted({idx.row() for idx in selected}, reverse=True)
        ids_to_remove = []

        for r in row_indices:
            id_item = self.table.item(r, 0)  # id column
            if id_item:
                try:
                    ids_to_remove.append(int(id_item.text()))
                except ValueError:
                    continue

        if not ids_to_remove:
            return

        # Confirm
        if QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove {len(ids_to_remove)} coffee(s) from inventory?",
        ) != QMessageBox.StandardButton.Yes:
            return

        self.df = self.df[~self.df["id"].isin(ids_to_remove)].reset_index(drop=True)
        save_inventory_df(self.df)
        self.refresh_table()
