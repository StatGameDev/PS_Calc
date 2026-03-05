from PySide6.QtWidgets import QApplication

# Must be imported AFTER QApplication(sys.argv) is constructed in main.py.
UI_SCALE: float = QApplication.primaryScreen().logicalDotsPerInch() / 96.0
THEME_PATH: str = "gui/themes/dark.qss"
SAVES_DIR: str = "saves"

FONT_SIZE_NORMAL: int = int(13 * UI_SCALE)
FONT_SIZE_SMALL: int = int(11 * UI_SCALE)
FONT_SIZE_LARGE: int = int(16 * UI_SCALE)
