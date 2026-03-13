# PS_Calc — Completed Phase Specs (Archive)
_Phases 0–4 are complete. Load this file only when referencing a specific
implementation decision from a completed phase._

---

## Phase 0 — Foundation ✓

### 0.1 File Changes
**Modified:** requirements.txt (PySide6>=6.7, pyqtgraph>=0.13), core/models/build.py
(server field), core/build_manager.py (serialize server), gui/app_config.py (full
rewrite, UI_SCALE from DPI), gui/main_window.py (QMainWindow), main.py (QApplication).

**Created:** gui/layout_config.json, gui/themes/dark.qss, gui/section.py,
gui/panel.py, gui/panel_container.py, gui/sections/__init__.py, all 10 section stubs.

### 0.2 layout_config.json
```json
{
  "focus_states": {
    "builder_focused": { "builder_fraction": 0.62 },
    "combat_focused":  { "builder_fraction": 0.22 }
  },
  "snap_threshold": 0.05,
  "sections": [
    { "key": "build_header",      "panel": "builder", "default_collapsed": false, "compact_mode": "none" },
    { "key": "stats_section",     "panel": "builder", "default_collapsed": false, "compact_mode": "compact_view" },
    { "key": "derived_section",   "panel": "builder", "default_collapsed": false, "compact_mode": "compact_view" },
    { "key": "equipment_section", "panel": "builder", "default_collapsed": false, "compact_mode": "compact_view" },
    { "key": "passive_section",   "panel": "builder", "default_collapsed": false, "compact_mode": "compact_view" },
    { "key": "combat_controls",   "panel": "combat",  "default_collapsed": false, "compact_mode": "none" },
    { "key": "summary_section",   "panel": "combat",  "default_collapsed": false, "compact_mode": "none" },
    { "key": "step_breakdown",    "panel": "combat",  "default_collapsed": false, "compact_mode": "compact_view" },
    { "key": "target_section",    "panel": "combat",  "default_collapsed": false, "compact_mode": "compact_view" },
    { "key": "incoming_damage",   "panel": "combat",  "default_collapsed": true,  "compact_mode": "hidden" }
  ]
}
```

### 0.3 Section Base Class Interface
```python
class Section(QWidget):
    collapsed_changed = Signal(bool)
    expand_requested  = Signal()

    def __init__(self, key, display_name, default_collapsed, compact_mode, parent=None)
    def add_content_widget(self, widget: QWidget) -> None
    def set_collapsed(self, collapsed: bool) -> None
    def toggle_collapse(self) -> None
    def set_compact_mode(self, compact: bool) -> None
    def _enter_compact_view(self) -> None   # base: collapse to header
    def _exit_compact_view(self) -> None    # base: restore collapse state
```
`set_compact_mode` is idempotent. Base `_enter/_exit_compact_view` collapse to header
(safe fallback). Concrete subclasses override both methods; lazy-build `_compact_widget`.

### 0.4 PanelContainer Interface
Construction: MainWindow reads layout_config.json, passes dict to PanelContainer.
`_SECTION_FACTORY` maps keys to classes — swap stub for real class by updating import only.

Key methods:
- `set_focus_state(state)` — sets sizes, calls `sec.set_compact_mode()` on all sections
- `focus_builder()` / `focus_combat()` — called by top-bar FOCUS buttons
- `showEvent` — applies `_pending_focus_state` on first show (ensures real width)
- Drag snap: `splitterMoved` → 200ms debounce timer → `_check_snap()`. Outside snap
  zone: compact states unchanged (no flicker).
- Step nudge: `_on_section_expand_requested` → +5% to combat; `_on_section_collapse_requested`
  restores. NOT a named focus state. Snap timer not restarted.

### 0.5 Top Bar (left → right)
```
[PS Calc label] [Build: label] [build QComboBox] [New btn] [Refresh btn]
[stretch] [Standard btn] [Payon Stories btn] (exclusive QButtonGroup) [stretch]
[◧ Builder btn] [◨ Combat btn]
```
Server toggle: `buttonToggled` → `_on_server_changed` → updates build.server,
emits server_changed, appends "— Payon Stories" to title when active.

### 0.6 Key Decisions
- `app_config.py` must be imported after `QApplication` is created (UI_SCALE needs live screen).
- `gui/__init__.py` absent — works from repo root. `gui/sections/__init__.py` required.
- Phase 8: `ui_scale_override` in settings JSON replaces DPI-derived UI_SCALE.
- Split fractions (0.62 / 0.22) are working defaults, adjust via layout_config.json only.

---

## Phase 1 — Character Builder Panel ✓

### 1.1 Build Header (build_header.py)
Build name (QLineEdit), job QComboBox (all pre-re jobs), base + job level spinboxes.
Emits: build_name_changed, job_changed, level_changed. compact_mode="none".

### 1.2 Base Stats (stats_section.py)
Six QSpinBox rows (STR/AGI/VIT/INT/DEX/LUK) with base + bonus + total display.
Stat point counter above grid. "Flat Bonuses" sub-group: BATK+, HIT+, FLEE+, CRI+,
Hard DEF, Soft DEF+, ASPD%.
compact_view: read-only 3-column QLabel grid, `STAT: Base+Bonus` format.

### 1.3 Derived Stats (derived_section.py)
Read-only, driven by StatusCalculator. Fields: BATK, DEF (hard+soft),
FLEE (+perfect_dodge), HIT, CRI%, ASPD (placeholder → Session 3), HP/SP (placeholder → Session 3).
compact_view: compact block showing BATK, DEF, FLEE, HIT, CRI.

### 1.4 Equipment (equipment_section.py)
11-slot grid (right_hand … head_low). Per row: slot label, item name, refine spinner
(0–20, refineable slots only), Edit button. Weapon Element combo below grid.
compact_view: weapon name + refine, slot-count summary.

### 1.5 Passives (passive_section.py)
Sub-groups: Self Buffs (SC_AURABLADE/MAXIMIZEPOWER/OVERTHRUST/OVERTHRUSTMAX),
Party Buffs placeholder, Masteries (12 skills, 0–10 spinboxes), Flags
(is_riding_peco, no_sizefix, is_ranged_override: Auto/Melee/Ranged).
compact_view: single line "3 buffs · 2 masteries · [flags]".

Signal flow: `_on_build_selected` → push to sections → `_run_status_calc()`.
Any change → `_on_build_changed` → collect build → `_run_status_calc()`.
`get_section(key)` on PanelContainer for typed access.

---

## Phase 2 — Combat Output ✓

### 2.1 Combat Controls (combat_controls.py)
Skill dropdown (skills.json, job filter), target search (QLineEdit → mob list → mob_id).
Environment radio buttons reserved. compact_mode="none".

### 2.2 Summary Card (summary_section.py)
Normal range min–max, avg. Crit range + avg, crit%. Hit% (placeholder → E1).
compact_mode="none". Will switch to min/avg/max after Session 2 variance work.

### 2.3 Step Breakdown (step_breakdown.py)
Two-column table (Normal | Crit), one row per DamageStep. Hover tooltip: note + formula.
"Show Source" toggle → hercules_ref column.
compact_mode="compact_view" → handled by StepsBar in panel.py (not this section).

StepsBar (panel.py, combat panel only):
- Collapsed: 22px, rotated "Steps ▶" label. Click → 220px, scrollable step+avg list.
- `set_visible_bar(False)` always resets to collapsed first.
- `refresh(result)` connected alongside step_breakdown to result_updated.
- No formula/note/hercules_ref in compact list.

---

## Phase 3 — Target & Incoming ✓

### 3.1 Target Info (target_section.py)
Full: mob name, ID, level, HP, DEF, MDEF, element, size, race, is_boss, base stats grid.
Data: `loader.get_monster_data(mob_id)` from `_run_battle_pipeline()`.
compact_view: `"MobName  DEF:X  VIT:X  Element/Lv  Size [Boss]"`.
Future: swap DEF↔MDEF for magic skills when magic damage is implemented.

### 3.2 Incoming Damage (incoming_damage.py)
Display-only: Mob ATK min–max, Player DEF hard/soft.
`refresh_mob(mob_id)` + `refresh_status(status)` from `_run_battle_pipeline()`.
compact_mode="hidden". Future: summary_section gains compact target variant instead.

### 3.3 Custom Target dialog
Deferred to Phase 4. Modal for custom target entry + Load-from-Build path.

---

## Phase 4 — Modals ✓

### 4.0 New Build dialog
Name / job / level form → BuildManager.save → refresh build dropdown.

### 4.1 Equipment Browser
Filterable by item type, slot-to-EQP mapping. Select → fills slot. Edit buttons enabled.

### 4.2 Skill Browser
Filterable from skills.json. "…" button next to skill combo. Select → sets active skill.

### 4.3 Monster Browser
Filterable from mob_db.json. "Browse…" button next to target search.
Numeric columns (ID/Lv/HP/DEF) sort via `_NumericItem` subclass.
