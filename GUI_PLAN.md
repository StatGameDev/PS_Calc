# PS_Calc GUI Plan
_Load at the start of any GUI session. PHASES_DONE.md contains full Phase 0–4 specs._

---

## Session Plan

| Session | Focus | Exit Criteria |
|---|---|---|
| **1** | Bugs B3+B4+B5 (splitter/target), verify B6+B7 | Layout stable, target refresh working, crit/overrefine verified |
| **2** | C1 Variance + E1 Hit/Miss | Summary card shows min/avg/max and hit chance |
| **3** | C3 ASPD + HP + SP | Derived stats correct for naked builds |
| **4** | D5/D4 Script parsing + gear/card effects + tooltips | Gear/card bonuses live; tooltip descriptions for common bonus types |
| **5** | Enhancements 4.4–4.7 (filter UIs) | All four filter UIs complete |
| **6** | E3 Bane skills + E4 Katar second hit + polish | Correct output for Hunter and Katar Sin builds |

**Pre-Session 4 gate:** grep item_db bonus-type distribution and decide
manual-vs-generated split before writing any parser code.

---

## Known Bugs

**B3 — StepsBar starts in wrong position** ✅ _Fixed Session 1_
Root cause: inner QSplitter not sized on first show (50/50 default).
Fix: `Panel.reset_steps_to_collapsed()` called via `QTimer.singleShot(0, ...)` from
`PanelContainer.set_focus_state` after `set_visible_bar(True)`.

**B4 — Combat panel doesn't expand when Steps expanded** ✅ _Fixed Session 1_
Root cause: StepsBar signals only wired to inner splitter; outer splitter nudge not triggered.
Fix: Added `steps_expand_requested`/`steps_collapse_requested` signals to Panel forwarding
from StepsBar. PanelContainer connects them to `_on_section_expand_requested`/`_on_section_collapse_requested`.

**B5 — Target sections not refreshing on selection** ✅ _Fixed Session 1_
Root cause: `except` block in `_run_battle_pipeline` called `refresh_mob(None)` / `refresh_status(None)`,
blanking the display on any pipeline error.
Fix: Target/incoming refresh moved before try block and removed from except. Pipeline result
becomes `None` on error; `result_updated` still emitted.

**B6 — Basic attack crit eligibility** ✅ _Fixed Session 1_
Root cause: skills.json has no id=0 entry; Normal Attack was absent from skill combo.
Fix: Prepend synthetic "Normal Attack (id=0)" as first combo item in CombatControlsSection.
Runtime: load knight_bash.json, select Normal Attack, verify crit branch in Summary.

**B7 — Overrefine shows as unrefinable** ✅ _Verified Session 1 (no code change)_
Static: Flamberge (1129) refineable=true in item_db.json. resolve_weapon reads it correctly.
get_overrefine(3, 7) = 16. Code path correct — no fix needed.

---

## Pending Enhancements _(Session 5)_

**4.4 — Skill list real names + job filter**
Filter skill combo to current build's job_id. Use skills.json job data; "Show All" toggle.

**4.5 — Equipment Browser job filter**
Filter by `item["job"]` list. "All Jobs" toggle in dialog toolbar.

**4.6 — Monster Browser filter dropdowns**
Race / Element / Size QComboBox above table. AND logic with name search.

**4.7 — Passives and Masteries job filter**
Hide/disable entries irrelevant to loaded job. "Show All" override in section header.

**P1 — Persist StepsBar expanded/collapsed state across focus changes** _(Phase 8 prereq)_
Currently `set_focus_state("combat_focused")` hides the StepsBar entirely, and
`set_focus_state("builder_focused")` always calls `reset_steps_to_collapsed()` via
`QTimer.singleShot`. If the user expanded the step list and then toggled to combat focus
and back, the expanded state is lost.
Required when user-adjustable widget sizes are introduced (Phase 8):
- Add `_steps_expanded: bool` to `StepsBar` (already has `self._expanded`; just needs
  to survive hide/show).
- `Panel.set_visible_bar(True)` should restore the last expanded state rather than
  always resetting to collapsed. Call `_on_steps_expand` or `reset_steps_to_collapsed`
  based on the saved flag.

---

## Session 2 — C1 Variance + E1 Hit/Miss

### C1 Variance (pipeline change)
Three sources expressed as `(min, max, scale)` tuples — keep strictly separated
from deterministic multipliers (Phase 7 histogram depends on this):
- Weapon ATK range: crit forces atkmax.
- Overrefine: rnd(1, max) — NOT clamped on crit.
- VIT DEF: rnd(0, max-1) — bypassed on crit; fix avg-off-by-0.5.

GUI: `summary_section` switches from single avg to `min / avg / max` for normal
and crit columns.

### E1 Hit/Miss (pipeline + summary card)
- Hit chance: `80 + HIT − FLEE`. Verify clamp bounds from source.
- Perfect Dodge: `1 + ⌊LUK/10⌋ + bonus`.
- Surface hit_chance on summary card below damage rows.

---

## Session 3 — C3 Derived Stats

ASPD, HP, SP implemented together (same pattern: table lookup + formula + bonus stub).
1. Base table lookup by job_id + base_level (pc.c / status.c).
2. Stat formula applied.
3. Bonus stubs: `bonus_aspd`, `bonus_maxhp`, `bonus_maxsp` — interface defined here,
   populated in Session 4.

GUI: `derived_section` removes placeholders; shows real ASPD, HP, SP.
Compact view: add HP/SP if space allows; otherwise full view only.

---

## Session 4 — D5/D4 Script Parsing + Gear/Card Effects

### Parser output per item
```python
@dataclass
class ItemEffect:
    bonus_type: str      # e.g. "bStr", "bSubClass"
    params: list         # e.g. [40] or ["Class_Boss", 40]
    description: str     # human-readable, generated or manual override
```

### Description generation
Template table: bonus_type → description pattern with param slots.
~20 common types cover the majority of item_db.
Manual override dict keyed by item_id for exceptions.
Alice Card test case: `bonus2 bSubClass,Class_Boss,40` →
"Receive 40% less damage from Boss monsters."

### Bonus routing
- Numeric bonuses populate Session 3 stubs (bonus_aspd, bonus_maxhp, etc.).
- Flat ATK/HIT/FLEE/CRI bonuses → existing `bonus_*` fields in StatusData.
- Pipeline-level multipliers (size/race/element) → E2 stubs (not fully implemented).

### GUI
Equipment browser and equipment section item names gain tooltip showing generated
description per card slot and gear piece.

---

## Phase 5 — Stat Planner Tab
Tab infrastructure on combat panel. Stat budget, projections, what-if mode.

## Phase 6 — Comparison Tab
Side-by-side build comparison. Diff highlighting and delta column.

## Phase 7 — Advanced Tab & Graphs
Full step breakdown always-visible. pyqtgraph TTK distribution histogram
(median, 10th/90th percentile, normal vs crit overlay).
Requires C1 variance tuple structure to be correct.

## Phase 8 — Polish & Config
Layout presets. Resolution scaling verification (1280×720 – 1920×1080).
`ui_scale_override` in settings JSON. Payon Stories BattleConfig fully wired.

---

## Architecture Reference

### Rules (non-negotiable)
- All styling via `dark.qss`. No inline style strings.
- No business logic in widget classes. Signals only.
- No cross-thread polling. Signals and slots only.

### Signal flow
```
User edits widget
  → section emits change signal
    → MainWindow._on_build_changed()
      → PlayerBuild → StatusCalculator + BattlePipeline → BattleResult
        → MainWindow emits result_updated(BattleResult)
          → combat sections render
```

### Focus states
- `builder_focused` (builder_fraction ≈ 0.62): builder expanded, combat compact.
- `combat_focused` (builder_fraction ≈ 0.22): combat expanded, builder compact.
- Free drag doesn't change compact state — only FOCUS buttons and snap do.
- Step breakdown expand nudge: +5% to combat panel width, not a named state.

### compact_mode values (layout_config.json)
| Value | Behavior |
|---|---|
| `"none"` | No change when panel is compact |
| `"hidden"` | Section hidden entirely |
| `"collapsed"` | Collapses to header; user can re-expand |
| `"compact_view"` | Subclass swaps content via `_enter_compact_view()` |