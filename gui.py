# gui.py – tiny launcher

import sys
from PySide6.QtWidgets import QApplication
from gui.gui_main_window import RoastMasterUI


def main():
    app = QApplication(sys.argv)
    win = RoastMasterUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
