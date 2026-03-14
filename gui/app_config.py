import json
import re

from PySide6.QtWidgets import QApplication

# Must be imported AFTER QApplication(sys.argv) is constructed in main.py.
UI_SCALE: float = QApplication.primaryScreen().logicalDotsPerInch() / 96.0
THEME_PATH: str = "gui/themes/dark.qss"
SAVES_DIR: str = "saves"

FONT_SIZE_NORMAL: int = max(1, int(13 * UI_SCALE))
FONT_SIZE_SMALL: int = max(1, int(11 * UI_SCALE))
FONT_SIZE_LARGE: int = max(1, int(16 * UI_SCALE))

_SETTINGS_PATH = "settings.json"
_SCALE_MIN = 0.7
_SCALE_MAX = 1.5
_SCALE_STEP = 0.1

_raw_qss: str = ""


def _load_override() -> float:
    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return float(json.load(f).get("ui_scale_override", 1.0))
    except Exception:
        return 1.0


_ui_scale_override: float = _load_override()


def scale_override() -> float:
    return _ui_scale_override


def effective_scale() -> float:
    return UI_SCALE * _ui_scale_override


def set_scale_override(value: float) -> None:
    global _ui_scale_override
    _ui_scale_override = max(_SCALE_MIN, min(_SCALE_MAX, round(value, 2)))
    try:
        existing: dict = {}
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        existing["ui_scale_override"] = _ui_scale_override
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    except OSError:
        pass


def load_qss() -> None:
    """Read the raw QSS from disk; must be called once after QApplication exists."""
    global _raw_qss
    try:
        with open(THEME_PATH, "r", encoding="utf-8") as f:
            _raw_qss = f.read()
    except FileNotFoundError:
        _raw_qss = ""


def apply_qss_scale(raw: str, scale: float) -> str:
    """Return QSS with all font-size: Npx values multiplied by scale."""
    def replace(m: re.Match) -> str:
        return f"font-size: {max(1, round(int(m.group(1)) * scale))}px"
    return re.sub(r"font-size:\s*(\d+)px", replace, raw)


def get_scaled_qss() -> str:
    """Return the loaded QSS scaled to the current effective scale."""
    return apply_qss_scale(_raw_qss, effective_scale())
