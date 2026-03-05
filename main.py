import sys

from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # app_config must be imported AFTER QApplication is constructed —
    # it reads the primary screen DPI at module level.
    from gui.app_config import THEME_PATH
    from gui.main_window import MainWindow

    try:
        with open(THEME_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"WARNING: stylesheet not found at '{THEME_PATH}' — running unstyled.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
