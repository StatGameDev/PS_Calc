from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from core.build_manager import BuildManager
from core.models.build import PlayerBuild


class _NoWheelCombo(QComboBox):
    """QComboBox that ignores scroll wheel events."""
    def wheelEvent(self, event) -> None:
        event.ignore()

# Matches the list in build_header.py exactly.
_JOB_NAMES: list[tuple[int, str]] = [
    (0,    "Novice"),
    (1,    "Swordman"),
    (2,    "Mage"),
    (3,    "Archer"),
    (4,    "Acolyte"),
    (5,    "Merchant"),
    (6,    "Thief"),
    (7,    "Knight"),
    (8,    "Priest"),
    (9,    "Wizard"),
    (10,   "Blacksmith"),
    (11,   "Hunter"),
    (12,   "Assassin"),
    (14,   "Crusader"),
    (15,   "Monk"),
    (16,   "Sage"),
    (17,   "Rogue"),
    (18,   "Alchemist"),
    (19,   "Bard"),
    (20,   "Dancer"),
    (23,   "Super Novice"),
    (24,   "Gunslinger"),
    (25,   "Ninja"),
    (4008, "Lord Knight"),
    (4009, "High Priest"),
    (4010, "High Wizard"),
    (4011, "Mastersmith"),
    (4012, "Sniper"),
    (4013, "Assassin Cross"),
    (4015, "Paladin"),
    (4016, "Champion"),
    (4017, "Scholar"),
    (4018, "Stalker"),
    (4019, "Creator"),
    (4020, "Clown"),
    (4021, "Gypsy"),
]


class NewBuildDialog(QDialog):
    """Create a blank PlayerBuild and save it. Returns created_build_name() on accept."""

    def __init__(self, saves_dir: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Build")
        self.setMinimumWidth(340)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._saves_dir = saves_dir
        self._created_name: Optional[str] = None

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(8)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. my_knight")
        form.addRow("Name:", self._name_edit)

        self._job_combo = _NoWheelCombo()
        for job_id, job_name in _JOB_NAMES:
            self._job_combo.addItem(job_name, userData=job_id)
        form.addRow("Job:", self._job_combo)

        self._level_spin = QSpinBox()
        self._level_spin.setRange(1, 99)
        self._level_spin.setValue(1)
        form.addRow("Base Level:", self._level_spin)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = btn_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setEnabled(False)
        layout.addWidget(btn_box)

        self._name_edit.textChanged.connect(self._on_name_changed)
        self._ok_btn.clicked.connect(self._create_build)
        btn_box.rejected.connect(self.reject)

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_name_changed(self, text: str) -> None:
        self._ok_btn.setEnabled(bool(text.strip()))

    def _create_build(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            return
        job_id = self._job_combo.currentData()
        level = self._level_spin.value()
        build = PlayerBuild(name=name, job_id=job_id, base_level=level)
        path = os.path.join(self._saves_dir, f"{name}.json")
        BuildManager.save_build(build, path)
        self._created_name = name
        self.accept()

    # ── Public API ─────────────────────────────────────────────────────────

    def created_build_name(self) -> Optional[str]:
        return self._created_name
