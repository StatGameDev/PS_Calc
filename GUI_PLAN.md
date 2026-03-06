# PS_Calc GUI Plan
_Load at the start of any GUI session. PHASES_DONE.md contains full Phase 0–4 specs._

---

## Session Plan

| Session | Focus | Exit Criteria |
|---|---|---|
| **1** | Bugs B3+B4+B5 (splitter/target), verify B6+B7 | Layout stable, target refresh working, crit/overrefine verified |
| **2** | C1 Variance + E1 Hit/Miss | ⚠️ Partial — C1a avg fix done; E1 deferred; C1 distribution needs planning session |
| **3** | E1 Hit/Miss + C3 ASPD + HP + SP | Hit chance in summary card; derived stats correct for naked builds |
| **4** | D5/D4 Script parsing + gear/card effects + tooltips | ✅ Done — gear/card bonuses live; tooltip descriptions generated |
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

**B8 — No Save button in GUI** ✅ _Fixed Session 4_
"Save" QPushButton added to top bar. Disabled when no build loaded or build name is empty.
`_on_save_build()`: collects build from sections, then `BuildManager.save_build(build, path)`.
Overwrites without confirmation. No "Save As" (Phase 8 polish).

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

## Session 2 — C1 Variance + E1 Hit/Miss _(partial)_

### Done
- **C1a** — VIT DEF avg off-by-0.5 fixed in `defense_fix.py`: `variance_max//2`.
- **B7 debug** — runtime print added to `base_damage.py`; run app to see actual
  weapon.level/refine values and confirm root cause before removing.

### C1 Variance — Handover (needs web-Claude planning session)

`DamageRange(min, max, avg)` is insufficient for Phase 7 histogram.
The final damage distribution is a **convolution of three independent uniform
random variables** (weapon ATK range, overrefine roll, VIT DEF roll), each
subtracted or added at different pipeline stages. The min and max are propagated
correctly, but `avg` is an approximation only. To support a damage histogram:

- **Option A — Exact convolution**: keep variance sources as `(lo, hi, step)` tuples;
  convolve at each stage. O(n²) in the range size, feasible for small overrefine but
  not for high-ATK weapons.
- **Option B — Irwin-Hall approximation**: sum of n uniform → approximately normal
  for large n. Fast, but loses tail accuracy.
- **Option C — Monte Carlo**: simulate k=10k rolls. Simple, correct, fast enough.
- **Architectural constraint**: deterministic multipliers (SkillRatio, AttrFix, etc.)
  must be applied to the *entire distribution*, not just avg. They scale the range.

Defer to web-Claude planning session. Do NOT change `DamageRange` until design is
settled — the tuple structure is the right starting point.

### E1 Hit/Miss — Deferred to Session 3

Verified Hercules formulas:
- `hitrate = 80 + player_HIT − mob_FLEE`, clamped to `[min_hitrate, max_hitrate]`
  (defaults 5/100). `#ifndef RENEWAL`, battle.c:4469/5024.
- `mob_FLEE = mob.level + mob.agi` (standard status formula).
- `perfect_dodge_chance = (target.luk + 10) / 10 %` — `rnd()%1000 < flee2`
  where `flee2 = luk + 10`, battle.c:4799.
- hitrate has further modifiers not modelled: skill per-level bonuses, SC_FOGWALL
  (−50 for ranged normal), arrow_hit, agi_penalty_type. Add TODO when implementing.

Required changes for E1:
1. `core/models/target.py` — add `agi: int = 0`
2. `core/data_loader.py` — `get_monster()` populate `agi` from `stats.agi`
3. `core/config.py` — add `min_hitrate: int = 5`, `max_hitrate: int = 100`
4. `core/models/damage.py` — add `perfect_dodge: float = 0.0` to `BattleResult`
5. `core/calculators/modifiers/hit_chance.py` — new: `calculate_hit_chance(status, target, config)`
6. `core/calculators/battle_pipeline.py` — call calculate_hit_chance, set result fields
7. `gui/sections/summary_section.py` — show hit% + perfect dodge% in Hit row

---

## Session 3 — E1 Hit/Miss + C3 Derived Stats ✅ DONE

**E1** — implemented. See COMPLETED_WORK.md Session 3 for full detail.
Unmodelled hitrate modifiers (documented in hit_chance.py TODO):
- Skill per-level HIT bonuses
- SC_FOGWALL: −50 hitrate for ranged normal attacks
- arrow_hit: ammo HIT bonus
- agi_penalty_type: AoE hit penalty
These require script parsing (Session 4) or separate modifier handling.

**C3** — implemented. Real ASPD/HP/SP in StatusCalculator.
Bonus stubs defined (`bonus_aspd_add`, `bonus_maxhp`, `bonus_maxsp`) — populated Session 4.
`derived_section` still shows placeholder ASPD/HP/SP labels — update needed (Session 4 or 5).

---

## Session 4 — D5/D4 Script Parsing + Gear/Card Effects ✅ DONE

**Implemented:**
- `core/models/item_effect.py` — `ItemEffect(bonus_type, arity, params, description)`
- `core/item_script_parser.py` — `parse_script(script) -> list[ItemEffect]`
  - Regex parser for bonus/bonus2/bonus3. Template table: ~35/25/9 types.
- `core/models/gear_bonuses.py` — `GearBonuses` dataclass (flat fields + E2 stub dicts)
- `core/gear_bonus_aggregator.py` — `GearBonusAggregator.compute(equipped) -> GearBonuses`
- `gui/main_window.py` — `_apply_gear_bonuses()` applies parsed bonuses as a clean overlay;
  save_build always writes manual-only values.

**Verified:** Alice Card `bSubRace,RC_Boss,40` → "Reduces damage from Boss monsters by 40%."
Picky Card `bStr,1 + bBaseAtk,10` → str_=1, batk=10 correctly routed.

**Not implemented (future sessions):**
- Tooltips in Equipment Browser / Equip Section UI (Session 5)
- bonus2/bonus3 E2 routing (race/size/element mults → pipeline) — blocked on E2 design
- bSkillAtk, bIgnoreDefRate pipeline routing (Session 6)
- Manual override dict for exceptional items

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