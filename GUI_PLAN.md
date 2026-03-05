# PS_Calc GUI Implementation Plan
_Reference document for all GUI implementation sessions. Load this file at the start
of any GUI-related session. Update it when decisions change during implementation._

---

## Phase 0 — Foundation

### 0.1 File List

#### Modified

| File | Change |
|---|---|
| `requirements.txt` | Replace `customtkinter` with `PySide6>=6.7`, add `pyqtgraph>=0.13` |
| `core/models/build.py` | Add `server: str = "standard"` field to PlayerBuild |
| `core/build_manager.py` | Serialize/deserialize `server` in save_build / load_build |
| `gui/app_config.py` | Full rewrite: module-level constants (UI_SCALE, THEME_PATH, SAVES_DIR, font sizes) computed from PySide6 screen DPI |
| `gui/main_window.py` | Full rewrite: QMainWindow, top bar, instantiates PanelContainer |
| `main.py` | Replace CTk `app.mainloop()` with `QApplication` + `sys.exit(app.exec())` |

#### Created

| File | Role |
|---|---|
| `gui/layout_config.json` | Authoritative section definitions: order, panel, collapsed/compact rules |
| `gui/themes/dark.qss` | Master QSS stylesheet — all colors, fonts, widget rules; no inline styles |
| `gui/section.py` | Section base class: collapsible header + content frame + compact protocol |
| `gui/panel.py` | Panel (QScrollArea subclass): owns ordered Section list, exposes add_section() |
| `gui/panel_container.py` | PanelContainer (QSplitter subclass): reads layout_config, FOCUS state, drag snap |
| `gui/sections/__init__.py` | Empty package marker |
| `gui/sections/build_header.py` | Stub — Phase 1.1 |
| `gui/sections/stats_section.py` | Stub — Phase 1.2 |
| `gui/sections/derived_section.py` | Stub — Phase 1.3 |
| `gui/sections/equipment_section.py` | Stub — Phase 1.4 |
| `gui/sections/passive_section.py` | Stub — Phase 1.5 |
| `gui/sections/combat_controls.py` | Stub — Phase 2.1 |
| `gui/sections/summary_section.py` | Stub — Phase 2.2 |
| `gui/sections/step_breakdown.py` | Stub — Phase 2.3 |
| `gui/sections/target_section.py` | Stub — Phase 3.1 |
| `gui/sections/incoming_damage.py` | Stub — Phase 3.2 |

`gui/tabs/` and `gui/widgets/` (empty dirs from old CTk scaffold): left in place, no references.

---

### 0.2 layout_config.json — Full Content

Compact behavior is expressed as a single `compact_mode` enum field (not two boolean flags).
Split fractions are working defaults and will be adjusted during implementation.

**`compact_mode` values:**

| Value | Behavior |
|---|---|
| `"none"` | No change when panel is compact |
| `"hidden"` | Entire section widget hidden |
| `"collapsed"` | Collapses to header only; user can still manually expand |
| `"compact_view"` | Subclass swaps to a compact content widget via `_enter_compact_view()` |

```json
{
  "_comment": "compact_mode applies to a section when its owning panel is NOT focused. snap_threshold is the builder_fraction distance within which a manual splitter drag snaps to that named state.",
  "focus_states": {
    "builder_focused": { "builder_fraction": 0.62 },
    "combat_focused":  { "builder_fraction": 0.22 }
  },
  "snap_threshold": 0.05,
  "sections": [
    {
      "key": "build_header",
      "panel": "builder",
      "display_name": "Build",
      "default_collapsed": false,
      "compact_mode": "none"
    },
    {
      "key": "stats_section",
      "panel": "builder",
      "display_name": "Base Stats",
      "default_collapsed": false,
      "compact_mode": "compact_view"
    },
    {
      "key": "derived_section",
      "panel": "builder",
      "display_name": "Derived Stats",
      "default_collapsed": false,
      "compact_mode": "compact_view"
    },
    {
      "key": "equipment_section",
      "panel": "builder",
      "display_name": "Equipment",
      "default_collapsed": false,
      "compact_mode": "compact_view"
    },
    {
      "key": "passive_section",
      "panel": "builder",
      "display_name": "Passives & Buffs",
      "default_collapsed": false,
      "compact_mode": "compact_view"
    },
    {
      "key": "combat_controls",
      "panel": "combat",
      "display_name": "Combat Controls",
      "default_collapsed": false,
      "compact_mode": "none"
    },
    {
      "key": "summary_section",
      "panel": "combat",
      "display_name": "Summary",
      "default_collapsed": false,
      "compact_mode": "none"
    },
    {
      "key": "step_breakdown",
      "panel": "combat",
      "display_name": "Step Breakdown",
      "default_collapsed": false,
      "compact_mode": "compact_view"
    },
    {
      "key": "target_section",
      "panel": "combat",
      "display_name": "Target Info",
      "default_collapsed": false,
      "compact_mode": "compact_view"
    },
    {
      "key": "incoming_damage",
      "panel": "combat",
      "display_name": "Incoming Damage",
      "default_collapsed": true,
      "compact_mode": "hidden"
    }
  ]
}
```

#### Compact-view contracts per section (implemented in Phase 1–3)

**Builder panel — compact when combat-focused (~22% width):**

- `build_header` (`none`): always shows build name and job; no change.
- `stats_section` (`compact_view`): swaps to a read-only 3-column grid of `QLabel` pairs.
  Format: `STR: 80+15`, `AGI: 90+5`, etc. No spinners. Six stats across two rows.
- `derived_section` (`compact_view`): swaps to a compact QLabel stack mirroring the
  in-game stat window. Combined values with `+`:
  `ATK: value`, `DEF: Hard+Soft`, `FLEE: Flee+PFlg`, `HIT: value`, `CRI: value%`.
  stats_section and derived_section together form the compact builder identity block.
- `equipment_section` (`compact_view`): shows weapon name + refine on one line,
  plus a truncated slot-count summary (e.g. "8/10 slots filled"). No per-slot rows.
- `passive_section` (`compact_view`): single summary line — active buff count + active
  mastery count (e.g. "3 buffs · 2 masteries"). No expandable sub-groups.

**Combat panel — compact when builder-focused (~38% width):**

- `combat_controls` (`none`): skill and target selection always accessible.
- `summary_section` (`none`): damage numbers always visible; primary output.
- `step_breakdown` (`compact_view`): collapses to a narrow vertical strip docked to the
  right edge of the content area. The strip shows section name with arrows pointing left only.
  - Clicking the strip expands it: `step_breakdown` emits `expand_requested()`.
  - `PanelContainer` receives the signal and nudges the combat panel wider (~5% of
    total width), arrows point right now. This nudge does NOT change the current focus state or trigger snap.
  - Expanded compact view: step name + avg value rows, stacked vertically,
    alternating row backgrounds from dark.qss. No formula, note, or hercules_ref.
  - Collapsing the strip emits a matching signal; PanelContainer restores the
    pre-nudge ratio.
- `target_section` (`compact_view`): single-line summary: mob name, DEF/VIT, element.
  Exact format decided during Phase 3.1 implementation.
- `incoming_damage` (`hidden`): not shown when combat panel is compact.

---

### 0.3 Section Base Class Interface

```python
class Section(QWidget):
    """
    Collapsible panel unit. All visibility changes go through this class.
    PanelContainer and Panel never call setVisible() directly.

    compact_mode (from layout_config.json):
      "none"         → set_compact_mode is a no-op
      "hidden"       → setVisible(False/True)
      "collapsed"    → collapse to header only; user can re-expand
      "compact_view" → swap content via _enter_compact_view() / _exit_compact_view()
    """

    collapsed_changed = Signal(bool)   # emitted after any collapse state change
    expand_requested  = Signal()       # emitted by step_breakdown compact strip

    def __init__(
        self,
        key: str,
        display_name: str,
        default_collapsed: bool,
        compact_mode: str,             # "none" | "hidden" | "collapsed" | "compact_view"
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Builds header row (arrow QLabel + display_name QLabel) and an empty
        content QFrame. Compact widget (_compact_widget) is None until
        _enter_compact_view() builds it (lazy construction).
        """

    # ── Content API ────────────────────────────────────────────────────────
    def add_content_widget(self, widget: QWidget) -> None:
        """Append widget to full-size content frame's QVBoxLayout."""

    # ── Collapse API ───────────────────────────────────────────────────────
    def set_collapsed(self, collapsed: bool) -> None:
        """Show/hide content frame. Updates arrow indicator. Emits collapsed_changed."""

    def toggle_collapse(self) -> None:
        """Header-click handler → set_collapsed(not self._is_collapsed)."""

    # ── Compact API ────────────────────────────────────────────────────────
    def set_compact_mode(self, compact: bool) -> None:
        """
        Entering compact (compact=True):
          "none"         → return immediately
          "hidden"       → self.setVisible(False)
          "collapsed"    → save _is_collapsed → _pre_compact_collapsed; set_collapsed(True)
          "compact_view" → _enter_compact_view()

        Exiting compact (compact=False):
          "none"         → return immediately
          "hidden"       → self.setVisible(True)
          "collapsed"    → restore _pre_compact_collapsed; clear saved value
          "compact_view" → _exit_compact_view()

        Idempotent: calling twice with the same value is a no-op.
        """

    def _enter_compact_view(self) -> None:
        """
        Base fallback: collapse to header (safe for Phase 0 stubs).
        Concrete subclasses override to:
          1. Build _compact_widget if None (lazy).
          2. Hide _content_frame, show _compact_widget.
          3. Save _is_collapsed to _pre_compact_collapsed.
        """

    def _exit_compact_view(self) -> None:
        """
        Base fallback: restore collapse state.
        Concrete subclasses override to:
          1. Hide _compact_widget, show _content_frame.
          2. Restore _pre_compact_collapsed.
        """

    # ── Properties ────────────────────────────────────────────────────────
    @property
    def is_collapsed(self) -> bool: ...

    @property
    def key(self) -> str: ...
```

**Phase 0 stub convention:** All 10 stub classes inherit `Section` directly, call
`super().__init__(...)`, and add a single `QLabel("Coming in Phase X — <name>")` via
`add_content_widget()`. No `_enter_compact_view()` override needed — the base fallback
(collapse to header) applies. Real subclasses in Phase 1–3 override compact methods only.

---

### 0.4 PanelContainer Interface

**Construction:**

`MainWindow.__init__` opens and parses `gui/layout_config.json`, then passes the dict
to `PanelContainer(layout_config=data)`. No file I/O inside the widget constructor.

Module-level `_SECTION_FACTORY: dict[str, type[Section]]` maps section keys to their
class (imported from `gui/sections/`). Swapping a stub for a real class: update import
only. No changes to Panel, PanelContainer, or layout_config.json.

**Construction sequence:**
1. `super().__init__(Qt.Orientation.Horizontal, parent)`.
2. Parse `focus_states` and `snap_threshold` from layout_config.
3. Create `Panel("builder")` and `Panel("combat")`; `addWidget()` both.
4. For each section entry (in order): factory → section instance → `panel.add_section(sec)`;
   store in `self._sections[key]` and `self._section_panel[key]`.
5. Connect each section's `expand_requested` → `self._on_section_expand_requested`.
6. Connect `splitterMoved` → restart `self._snap_timer` (QTimer, 200 ms, single-shot).
7. Connect `_snap_timer.timeout` → `self._check_snap`.
8. Set `self._pending_focus_state = "builder_focused"` (applied on first show).

**Focus state management:**

```
set_focus_state(state: str):
  if state == self._current_focus: return
  self._current_focus = state
  fraction = self._focus_states[state]["builder_fraction"]
  total = self.width()
  setSizes([int(total * fraction), int(total * (1 - fraction))])
  focused_panel = "builder" if state == "builder_focused" else "combat"
  for key, sec in self._sections.items():
      sec.set_compact_mode(self._section_panel[key] != focused_panel)
  focus_state_changed.emit(state)
```

**FOCUS buttons (called by MainWindow top-bar buttons):**
```
focus_builder() → set_focus_state("builder_focused")
focus_combat()  → set_focus_state("combat_focused")
```

**Drag-to-snap breakpoint:**

`splitterMoved` fires on every pixel — too noisy to snap immediately. Use a debounce timer:
- Each `splitterMoved` event restarts `_snap_timer` (200 ms single-shot).
- `_check_snap()` runs only after the user stops dragging for 200 ms:

```
_check_snap():
  sizes = self.sizes()
  total = sizes[0] + sizes[1]
  if total == 0: return
  ratio = sizes[0] / total
  for state_name, state_data in self._focus_states.items():
      if abs(ratio - state_data["builder_fraction"]) <= self._snap_threshold:
          set_focus_state(state_name)
          return
  # Outside all thresholds: stay at dragged ratio; compact states unchanged
  # (compact state remains as established by the last set_focus_state call)
```

If the dragged position is outside all snap zones, compact states are NOT changed.
They remain as established by the last FOCUS button or previous snap. This is intentional:
dragging freely adjusts the visual split only; compact UI context does not flicker.

**Step breakdown expand nudge:**

```
_on_section_expand_requested():
  self._pre_nudge_sizes = self.sizes()
  delta = int(self.width() * 0.05)
  s = self.sizes()
  setSizes([max(0, s[0] - delta), s[1] + delta])
  # Does NOT call set_focus_state — nudge is NOT a named state
  # Snap timer is NOT restarted for programmatic moves

_on_section_collapse_requested():
  if self._pre_nudge_sizes is not None:
      setSizes(self._pre_nudge_sizes)
      self._pre_nudge_sizes = None
```

**Panel:**

```python
class Panel(QScrollArea):
    def __init__(self, name: str, parent=None): ...
    def add_section(self, section: Section) -> None:
        """Insert section before trailing QSpacerItem in internal QVBoxLayout."""
```

`widgetResizable=True`. Horizontal scrollbar: off. Vertical scrollbar: on-demand.

**First-show sizing:**

PanelContainer overrides `showEvent`: if `_pending_focus_state` is set, calls
`set_focus_state(_pending_focus_state)` and clears it. Ensures `setSizes` runs
after the widget has a real width (not 0 as it is during `__init__`).

---

### 0.5 Top Bar

Fixed-height `QFrame` at the top of `MainWindow`'s central widget, above PanelContainer.
`QHBoxLayout`.

**Widget sequence (left → right):**

```
[QLabel "PS Calc"]  [8px spacer]
[QLabel "Build:"]  [QComboBox build_selector]
[QPushButton "New" — disabled Phase 0]  [QPushButton "Refresh"]
[QSpacerItem stretch]
[QPushButton "Standard" checkable]  [QPushButton "Payon Stories" checkable]
   ← exclusive QButtonGroup →
[QSpacerItem stretch]
[QPushButton "◧ Builder"]  [QPushButton "◨ Combat"]
```

**Build dropdown (`QComboBox`):**
- Init: `sorted(BuildManager.list_builds("saves/"))` → `addItems(stems)`.
- `currentTextChanged` → `MainWindow._on_build_selected(name: str)`. Phase 0: stores name. Phase 1: propagates to all sections.
- Refresh: clears, repopulates, preserves selection if stem still exists.
- "New": `setEnabled(False)` in Phase 0; enabled in Phase 4.

**Server toggle (`QButtonGroup`, exclusive):**
- Two checkable `QPushButton`s: "Standard" (default) and "Payon Stories".
- `buttonToggled` → `MainWindow._on_server_changed(is_payon: bool)`:
  - Updates `self._current_build.server` if a build is loaded.
  - Emits app-level `server_changed(server_str: str)` signal.
  - Window title: appends `" — Payon Stories"` when active; removes when standard.
  - Phase 8: fully wires into BattleConfig with PS-specific overrides.

**FOCUS buttons:**
- "◧ Builder" → `self._panel_container.focus_builder()`
- "◨ Combat"  → `self._panel_container.focus_combat()`

---

### 0.6 Conflicts and Resolutions

**6.1 Full toolkit replacement (hard blocker):**
`gui/main_window.py` (CTk class), `gui/app_config.py` (CTk fields), `main.py`
(`.mainloop()`), `requirements.txt` (`customtkinter`) — all four are full rewrites.
Old MainWindow Treeview display logic is reproduced in `step_breakdown` in Phase 2.

**6.2 `PlayerBuild.server` field absent:**
- `build.py`: add `server: str = "standard"` after existing fields, before `name`.
- `build_manager.py` `save_build`: add `"server": build.server` to serialized dict.
- `build_manager.py` `load_build`: add `server=data.get("server", "standard")`.
- Existing save files without `server` key default to `"standard"`. No migration needed.

**6.3 `app_config.py` — module-level constants, not dataclass:**
`UI_SCALE` must be computed from a live `QApplication`. `app_config.py` must be
imported after `QApplication(sys.argv)` is constructed in `main.py`.

```python
# app_config.py (Phase 0)
from PySide6.QtWidgets import QApplication

UI_SCALE: float = QApplication.primaryScreen().logicalDotsPerInch() / 96.0
THEME_PATH: str = "gui/themes/dark.qss"
SAVES_DIR:  str = "saves"

FONT_SIZE_NORMAL: int = int(13 * UI_SCALE)
FONT_SIZE_SMALL:  int = int(11 * UI_SCALE)
FONT_SIZE_LARGE:  int = int(16 * UI_SCALE)
```

**6.4 Phase 0 stubs — compact_view fallback:**
Stubs use the base `_enter_compact_view()` fallback (collapses to header).
Phase 1–3 real classes override compact methods; no other files change.

**6.5 `gui/__init__.py` absent:**
Works for `python main.py` from repo root. No change needed.
`gui/sections/__init__.py` must be created (empty) for package imports.

**6.6 `gui/tabs/` and `gui/widgets/` empty dirs:**
Left in place. No Phase 0 references.

**6.7 Split fractions are working defaults:**
`builder_focused: 0.62` and `combat_focused: 0.22` are initial placeholders.
Adjust by editing layout_config.json during Phase 1–2 implementation as actual
content demands clarify the right proportions. No code changes needed to adjust.

**6.8 DPI scaling — Phase 0 and Phase 8:**
Phase 0: primary screen DPI only, no re-scaling on window move.
Phase 8: add `ui_scale_override: Optional[float]` in a settings JSON. If set, it
replaces the DPI-derived value. `app_config.py` checks for the override file at import.
No multi-monitor re-scaling on window move (not planned beyond Phase 8).

---

## Phase 1 — Character Builder Panel ✓ DONE

Prerequisite: Phase 0 complete and app launches with stubbed sections visible.

### 1.1 Build Header Section (`build_header.py`) ✓
Content: build name (editable QLineEdit), job QComboBox (all pre-re jobs), base level +
job level spinboxes. Emits `build_name_changed`, `job_changed`, `level_changed`.
compact_mode = "none" → no compact widget needed.

### 1.2 Base Stats Section (`stats_section.py`) ✓
Content: six QSpinBox rows (STR/AGI/VIT/INT/DEX/LUK), each with base + bonus + total
display. Base stat total counter above the grid. Additional "Flat Bonuses" sub-group
(BATK+, HIT+, FLEE+, CRI+, Hard DEF, Soft DEF+, ASPD%) for manually entered gear bonuses.
compact_view: read-only 3-column QLabel grid — `STAT: Base+Bonus` format.

### 1.3 Derived Stats Section (`derived_section.py`) ✓
Content: read-only grid driven by StatusCalculator.refresh(status). Fields: BATK,
DEF (hard+soft), FLEE (+perfect_dodge), HIT, CRI%, ASPD (placeholder), HP/SP (placeholder).
compact_view: compact block showing BATK, DEF, FLEE, HIT, CRI.
main_window._run_status_calc() calls StatusCalculator and pushes StatusData here.

### 1.4 Equipment Section (`equipment_section.py`) ✓
Content: 11-slot grid (right_hand…head_low). Each row: slot label, item name (resolved
via loader.get_item), refine spinner (0–20, refineable slots only), Edit button (disabled
— Phase 4). Weapon Element combo below grid (From Item / Neutral / Water … Undead).
compact_view: weapon name + refine on line 1, slot-count summary on line 2.

### 1.5 Passive Section (`passive_section.py`) ✓
Sub-groups: Self Buffs (SC_AURABLADE/MAXIMIZEPOWER/OVERTHRUST/OVERTHRUSTMAX),
Party Buffs placeholder, Masteries (12 skills, 0–10 spinboxes), Flags
(is_riding_peco checkbox, no_sizefix checkbox, is_ranged_override radio: Auto/Melee/Ranged).
compact_view: single summary line of active buffs · masteries · flags.

Signal flow wired in main_window.py:
- `_on_build_selected` → load file → push to all sections → `_run_status_calc()`
- any section change signal → `_on_build_changed` → collect into build → `_run_status_calc()`
- `get_section(key)` added to PanelContainer for typed section access.

---

## Phase 2 — Combat Analysis: Output ✓ DONE

Prerequisite: Phase 1 sections wired to BattlePipeline via signals.
Recalculation: any build change emits `build_changed` → MainWindow runs pipeline →
pushes BattleResult to combat sections via `result_updated(BattleResult)` signal.

### 2.1 Combat Controls (`combat_controls.py`) ✓
Skill dropdown (populated from skills.json, filters by job_id).
Target dropdown (search QLineEdit → filtered mob list → select → sets target_mob_id).
Environment radio buttons (reserved for future map-level config).
compact_mode = "none" → always accessible.

### 2.2 Summary Card (`summary_section.py`) ✓
Normal range (min–max), avg. Crit range + avg, crit%. Hit% (placeholder 100% until E1).
compact_mode = "none" → always visible.

### 2.3 Step Breakdown (`step_breakdown.py`) ✓
Full view (combat focused): two-column table (Normal | Crit), one row per DamageStep.
Columns: name, min/avg/max value. Hover tooltip: note + formula.
"Show Source" toggle reveals hercules_ref column.

compact_mode="hidden": StepBreakdownSection is completely invisible when builder
is focused. Step data in compact state is handled by StepsBar in Panel instead.

StepsBar (gui/panel.py, combat panel only): panel-level QWidget on the right edge
of the combat panel's QHBoxLayout. Controlled by PanelContainer.set_focus_state —
shown when builder_focused, hidden when combat_focused. Internal toggle:
- Default (collapsed): 22px wide, `_VerticalBarLabel` draws rotated "Steps ▶" text.
- Clicking bar: expands to 220px, shows scrollable step+avg list; arrow → ◀.
- Clicking again: collapses back to 22px; list hidden; arrow → ▶.
- `set_visible_bar(False)` always resets to collapsed before hiding.
- `refresh(result)` connected to MainWindow.result_updated alongside step_breakdown.
- No formula, note, or hercules_ref in compact list.

---

## Phase 3 — Combat Analysis: Target & Incoming ✓ DONE

### 3.1 Target Info (`target_section.py`) ✓
Full view: mob name, ID, level, HP, DEF, MDEF, element (Name/Level), size, race,
is_boss flag, then a "Base Stats" sub-header with STR/AGI/VIT/INT/DEX/LUK.
Data source: `loader.get_monster_data(mob_id)` called from `_run_battle_pipeline()`.
compact_view: single summary line — `"MobName  DEF:X  VIT:X  Element/Lv  Size"`,
with `"Boss"` appended when is_boss.

Future (after magic damage implemented): conditionally swap DEF→MDEF and add INT
for magic skills; display all fields for mixed damage. Compact view adjusts to match.

### 3.2 Incoming Damage (`incoming_damage.py`) ✓
Phase 3: display-only. Two rows: `Mob ATK: min–max` and `Player DEF: hard / soft`.
`refresh_mob(mob_id)` and `refresh_status(status)` called from `_run_battle_pipeline()`.
compact_mode="hidden" — section is hidden when combat panel is compact; no compact_view
override needed. Left hidden in compact mode for now.

Future: when fully implemented, section remains hidden in compact view; the summary
card (summary_section) gains a compact variant of target info instead.

### 3.3 Custom Target dialog + Load-from-Build path
Deferred to Phase 4 (modal work). Modal for custom target entry; "Load from Build"
path for player vs player scenarios.

---

## Phase 4 — Modals ✓ DONE

### 4.0 New Build dialog ✓
Name / job / level form; saves via BuildManager; refreshes build dropdown.

### 4.1 Equipment Browser ✓
Filterable list from loader.get_items_by_type(). Select → fills equipment slot.
Edit buttons enabled. Slot-to-EQP mapping filters items by slot.

### 4.2 Skill Browser ✓
Filterable skill list from skills.json. Select → sets active skill in combat_controls.
"…" Browse button added next to skill combo + level spinner.

### 4.3 Monster Browser ✓
Filterable mob list from mob_db.json. Select → sets target_mob_id.
"Browse…" button added next to target search. Numeric columns sort as integers.

### 4.x — Phase 4 Enhancements (pending)

**4.4 — Skill list real names + job filter** (GUI_TODO #1)
- Skill combo currently shows all 1168 skills including internal/NPC skills.
- Filter skill combo to only show skills available to the current build's job_id.
- Use skills.json job data if present; otherwise expose a "Show All" toggle.

**4.5 — Equipment Browser job filter** (GUI_TODO #6)
- Filter items in EquipmentBrowserDialog by build's job_id using item["job"] list.
- Add "All Jobs" toggle button in the dialog toolbar to disable the filter.

**4.6 — Monster Browser filter dropdowns** (GUI_TODO #12)
- Add Race / Element / Size QComboBox filter dropdowns above the table.
- Filters combine with the name search (AND logic).

**4.7 — Filter Passives and Masteries by job** (GUI_TODO #8)
- Passive section should hide/disable buffs and masteries irrelevant to the loaded job.
- SC_AURABLADE → Knights/Lord Knights only; SM_SWORD → Swordman classes only, etc.
- Add "Show All" override toggle in the section header.

---

## Known Bugs (GUI_TODO — from runtime testing)

**B1 — QFont::setPointSize <= 0 error** ✓ FIXED
Font size constants clamped to `max(1, ...)` in app_config.py.

**B2 — Monster browser numeric sort wrong** ✓ FIXED
ID/Lv/HP/DEF columns now use `_NumericItem` subclass that sorts by `int(text)`.

**B3 — StepsBar starts in wrong position** (GUI_TODO #3)
The StepsBar renders at a mid-panel position on startup instead of flush right.
Investigate: PanelContainer `showEvent` / `set_visible_bar` initial sizing order.
The inner QSplitter in the combat panel may not have its sizes set before show.

**B4 — Combat panel doesn't expand when Steps expanded** (GUI_TODO #4)
Clicking the StepsBar to expand it should nudge the outer splitter.
Investigate: `expand_requested` signal path from StepsBar → Panel → PanelContainer.
Check that `_on_section_expand_requested` in PanelContainer is actually connected.

**B5 — Target sections not refreshing on selection** (GUI_TODO #5)
After selecting a new target via inline search or MonsterBrowserDialog, Target Info
and Incoming Damage sections may not update.
Investigate: `_run_battle_pipeline` is called via `_on_build_changed` which is
triggered by `combat_settings_changed`. Confirm that signal fires and that
`refresh_mob` / `refresh_status` are reached.

**B6 — Basic attack crit eligibility** (GUI_TODO #9)
`crit_chance.py` already includes skill_id=0 in `CRIT_ELIGIBLE_SKILLS`.
Needs runtime verification: confirm normal attack (id=0) produces a non-None
`crit` branch in BattleResult and that Summary shows crit numbers.

**B7 — Overrefine shows as unrefinable** (GUI_TODO #10)
Data inspection: Flamberge (1129) has `refineable: true`, resolve_weapon passes
it correctly, `get_overrefine(3, 7) = 16`. Cannot reproduce statically.
Needs runtime trace: add print in `base_damage.py` at the `weapon.refineable`
check to confirm what value is received when knight_bash.json is loaded.

---

## Phase 5 — Stat Planner Tab

Tab infrastructure on combat panel. Stat budget, projections, what-if mode.

---

## Phase 6 — Comparison Tab

Side-by-side build comparison. Diff highlighting and delta column.

---

## Phase 7 — Advanced Tab & Graphs

Full step breakdown always-visible. pyqtgraph TTK distribution histogram
(median, 10th/90th percentile, normal vs crit overlay).

---

## Phase 8 — Polish & Config

- Layout preset system (Build Crafting / Skill Analysis / Optimization).
- Resolution scaling verification (1280×720 through 1920×1080).
- Manual UI scale override: `ui_scale_override` in settings JSON; checked at startup.
- Payon Stories BattleConfig fully wired.

---

## Future: Horizontal Layout Pass

Sections currently stack vertically in each panel. PySide6 supports placing sections
side by side using horizontal QHBoxLayouts and nested QSplitters with minimal effort,
but no specific arrangements have been planned yet. Revisit after Phase 3 is stable
and content widths are well understood. Candidates: Summary + Target side by side;
Combat Controls + Incoming Damage row.

---

## Architecture Reference

### GUI rules (non-negotiable)
- All styling via `gui/themes/dark.qss`. No inline style strings in widget code.
- No business logic in widget classes. Widgets emit signals; core handles calculation;
  results pushed back via signals.
- Signals and slots only for cross-thread communication. No polling loops.

### Signal flow (Phase 1+)
```
User edits widget
  → section emits change signal
    → MainWindow._on_build_changed()
      → builds PlayerBuild from current section states
        → StatusCalculator + BattlePipeline → BattleResult
          → MainWindow emits result_updated(BattleResult)
            → combat sections receive and render
```

### app_config.py contract
Must be imported after QApplication is created. Provides UI_SCALE, THEME_PATH,
SAVES_DIR, FONT_SIZE_* constants. Phase 8 adds ui_scale_override support.

### core/ is read-only from GUI
GUI imports from core. core never imports from gui. DataLoader singleton is shared.
No core files modified during Phase 1–8 unless pipeline gaps (C/D/E items) are addressed.
