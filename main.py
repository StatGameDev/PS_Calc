import os
import sys

from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    # When frozen by PyInstaller, set CWD to the exe directory so that all
    # relative paths (gui/themes, saves/, settings.json, core/data) resolve correctly.
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))

    app = QApplication(sys.argv)

    # app_config must be imported AFTER QApplication is constructed —
    # it reads the primary screen DPI at module level.
    import gui.app_config as app_config
    from gui.main_window import MainWindow

    app_config.load_qss()
    scaled = app_config.get_scaled_qss()
    if scaled:
        app.setStyleSheet(scaled)
    else:
        print(f"WARNING: stylesheet not found at '{app_config.THEME_PATH}' — running unstyled.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
