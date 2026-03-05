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

# Matches the list in build_header.py exactly.
_JOB_NAMES: list[tuple[int, str]] = [
    (0,  "Novice"),
    (1,  "Swordman"),
    (2,  "Mage"),
    (3,  "Archer"),
    (4,  "Acolyte"),
    (5,  "Merchant"),
    (6,  "Thief"),
    (7,  "Knight"),
    (8,  "Priest"),
    (9,  "Wizard"),
    (10, "Blacksmith"),
    (11, "Hunter"),
    (12, "Assassin"),
    (14, "Crusader"),
    (15, "Monk"),
    (16, "Sage"),
    (17, "Rogue"),
    (18, "Alchemist"),
    (19, "Bard"),
    (20, "Dancer"),
    (23, "Lord Knight"),
    (24, "Assassin Cross"),
    (25, "High Wizard"),
    (26, "Sniper"),
    (27, "Mastersmith"),
    (28, "High Priest"),
    (29, "Paladin"),
    (30, "Clown"),
    (31, "Champion"),
    (32, "Scholar"),
    (33, "Creator"),
    (34, "Stalker"),
    (35, "Gypsy"),
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

        self._job_combo = QComboBox()
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
