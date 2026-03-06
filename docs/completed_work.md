# PS_Calc — Completed Work Log
_Append new entries at the bottom of each section when work is done.
Format: item ID (if applicable), description, and any gotchas worth remembering._

---

## Pipeline Core

**Initial implementation**
Full damage pipeline with all modifiers. Step order (corrected across sessions):
`BaseDamage → SkillRatio → CritAtkRate (crit only) → DefenseFix (skip on crit) → ActiveStatusBonus → RefineFix → MasteryFix → AttrFix → CardFix → FinalRateBonus`
Every modifier is a `@staticmethod def calculate(...)` — no instantiation.
Every calculation calls `result.add_step(...)` — no silent mutation.

**A1 — status.int_ rename**
`status.int` renamed to `status.int_` project-wide. Python keyword collision.
Affects: all modifiers that read INT, status_calculator.py, any future code touching INT.

**A2 — SizeFix**
Size penalty table implemented. Formula source: battle.c.

**A3 — Pipeline step order fix**
Corrected ordering of steps after verifying against Hercules source.

**A4 — Refine position**
RefineFix placed correctly in the pipeline after DefenseFix/CritAtkRate.

**A5 — DEX scaling**
DEX contribution to HIT corrected per Hercules source.

**A6, A7 — Additional formula fixes**
(Details not recorded at time of completion.)

**C4 — refineable flag**
`Weapon.refineable` field added. BuildManager.resolve_weapon passes it through.
`base_damage.py` checks `weapon.refineable` before applying overrefine.
Gotcha: B7 (overrefine shows as unrefinable) is an unresolved runtime bug — the
static data is correct but something in the load path may drop the flag. See B7 in
GUI_PLAN.md Known Bugs.

**C5 — derived is_ranged / is_katar**
`is_ranged` derived from `weapon.weapon_type in RANGED_WEAPON_TYPES` (weapon.py).
`is_katar` derived from `weapon.weapon_type == W_KATAR`.
`PlayerBuild.is_katar` field REMOVED — never hardcode, always derive.

**C6 — Crit system**
`BattleResult` dataclass with dual branch: `normal: DamageResult`, `crit: Optional[DamageResult]`.
`crit` is None when the skill/attack is not crit-eligible.
Eligibility controlled by whitelist in `crit_chance.py` — `CRIT_ELIGIBLE_SKILLS`.
`skill_id=0` (basic attack) is in the whitelist.
Katar bug fix: katar builds get double crit rate (pre-renewal mechanic), implemented
in `crit_chance.py`.
`battle_pipeline.py` runs `_run_branch(is_crit=False)` and conditionally
`_run_branch(is_crit=True)` based on eligibility.
is_crit=True effects: `base_damage.py` forces atkmax; `defense_fix.py` sets idef=idef2=1.

**Display fix — overrefine step**
Overrefine step was being dropped from the step breakdown display. Restored.

**Display fix — SizeFix avg/min collapse**
SizeFix was incorrectly collapsing avg and min values. Fixed.

---

## Data Infrastructure

**B1–B6 — Data fixes**
SC (status condition) cleanups: removed renewal-only SCs from pre-renewal code paths.
Preset migration: (details not recorded at time of completion.)

**D1 — item_db scraper expanded**
`tools/import_item_db.py` now captures ALL fields from item_db.conf.
Output: `core/data/pre-re/db/item_db.json` — 2760 items: weapon, armor, card, ammo.
Rule: never filter at scrape time. `_scraped_at` timestamp on every output.

**D2 — mob_db scraper expanded**
`tools/import_mob_db.py` captures all mob fields including all Target pipeline fields
(def_, vit, luk, size, race, element, element_level, is_boss, level).
Output: `core/data/pre-re/db/mob_db.json` — 1007 mobs.

**D3 — skills data**
`core/data/pre-re/skills.json` — 1168 skills.

---

## Build System

**Build save/load**
Fully implemented in `build_manager.py`.
Schema fields: name, job_id, base_level, server, base_stats, bonus_stats,
target_mob_id, equipped, refine, weapon_element, active_buffs, mastery_levels, flags.
`resolve_weapon(item_id, refine, element_override)` — missing ID logs WARNING and
returns Unarmed fallback (ATK 0, wlv 1, neutral element).

**Test builds — rocalc imports**
6 builds imported via `tools/import_rocalc_saves.py` from rocalc localStorage format.
All 11 equipment slots decoded. Item/DB mismatches flagged with [MISMATCH] in the
build name or a warning on load.

| File | Notes |
|---|---|
| saves/knight_bash.json | Scaffold — placeholder stats |
| saves/spear_peco.json | Scaffold — placeholder stats |
| saves/ak77_hunter.json | rocalc import — [MISMATCH] flagged |
| saves/dd_sin.json | rocalc import — dual wield resolved |
| saves/nat_crit_sin.json | rocalc import |
| saves/agi_bs.json | rocalc import |
| saves/combo_monk.json | rocalc import |
| saves/ip_rogue.json | rocalc import |

Dual wield resolution: dd_sin.json carries two weapons; pipeline correctly reads
both via the build's equipped dict and the W_KATAR/dual-wield path.

---

## GUI — Foundation (Phase 0)

**Toolkit migration**
Full replacement of CustomTkinter with PySide6. Affected: requirements.txt,
main.py (QApplication + sys.exit), gui/app_config.py (full rewrite),
gui/main_window.py (full rewrite). Old CTk MainWindow Treeview logic reproduced
in step_breakdown.py in Phase 2.

**app_config.py**
Module-level constants only — must be imported after QApplication is created.
`UI_SCALE = QApplication.primaryScreen().logicalDotsPerInch() / 96.0`
`FONT_SIZE_NORMAL = max(1, int(13 * UI_SCALE))`
`FONT_SIZE_SMALL  = max(1, int(11 * UI_SCALE))`
`FONT_SIZE_LARGE  = max(1, int(16 * UI_SCALE))`
Clamped to max(1, ...) — prevents QFont::setPointSize <= 0 crash (B1, fixed).
Phase 8: ui_scale_override in settings JSON will replace DPI-derived value.

**layout_config.json**
Authoritative section registry. Fields per entry: key, panel, display_name,
default_collapsed, compact_mode. compact_mode values: none / hidden / collapsed / compact_view.
Focus states: builder_focused (builder_fraction 0.62), combat_focused (0.22).
snap_threshold: 0.05. These are working defaults — adjust JSON only, no code change.
gui/tabs/ and gui/widgets/ (old CTk dirs) left in place, no references.
gui/__init__.py absent — works from repo root. gui/sections/__init__.py required.

**Section base class (gui/section.py)**
Signals: collapsed_changed(bool), expand_requested().
Key methods: add_content_widget, set_collapsed, toggle_collapse, set_compact_mode.
set_compact_mode is idempotent. _compact_widget is lazy (built on first entry).
Base _enter_compact_view / _exit_compact_view collapse to header — safe fallback
for stubs. Concrete subclasses override both.
PlayerBuild.server field added at same time (build.py, build_manager.py).
Existing saves without server key default to "standard" — no migration needed.

**PanelContainer (gui/panel_container.py)**
QSplitter subclass. _SECTION_FACTORY maps keys to classes — swap stub for real
class by updating import only, no other changes.
set_focus_state: sets splitter sizes, calls sec.set_compact_mode() on all sections.
showEvent: applies _pending_focus_state on first show (splitter has no real width
during __init__).
Drag snap: splitterMoved → 200ms debounce timer → _check_snap(). If dragged
position is outside all snap zones, compact states do NOT change (no flicker).
Step nudge: _on_section_expand_requested adds 5% to combat width, stores pre-nudge
sizes. _on_section_collapse_requested restores. NOT a named focus state; snap timer
not restarted for programmatic moves.

**Panel (gui/panel.py)**
QScrollArea subclass. widgetResizable=True. Horizontal scrollbar off, vertical on-demand.
add_section inserts before trailing QSpacerItem in internal QVBoxLayout.
StepsBar lives here (combat panel only) — see Phase 2.

**Top bar**
Left→right: [PS Calc] [Build: label] [build QComboBox] [New] [Refresh]
[stretch] [Standard] [Payon Stories] (exclusive QButtonGroup) [stretch] [◧ Builder] [◨ Combat]
Server toggle: buttonToggled → _on_server_changed → updates build.server, emits
server_changed, appends "— Payon Stories" to window title when active.

---

## GUI — Builder Panel (Phase 1)

**1.1 build_header.py**
Build name (QLineEdit), job QComboBox (all pre-re jobs), base + job level spinboxes.
Emits: build_name_changed, job_changed, level_changed. compact_mode="none".

**1.2 stats_section.py**
Six QSpinBox rows (STR/AGI/VIT/INT/DEX/LUK). Base + bonus + total per row.
Stat point counter above grid.
"Flat Bonuses" sub-group: BATK+, HIT+, FLEE+, CRI+, Hard DEF, Soft DEF+, ASPD%.
compact_view: read-only 3-column QLabel grid, STAT: Base+Bonus format.

**1.3 derived_section.py**
Read-only, driven by StatusCalculator. Fields: BATK, DEF (hard+soft),
FLEE (+perfect_dodge), HIT, CRI%, ASPD (placeholder), HP/SP (placeholder).
compact_view: BATK, DEF, FLEE, HIT, CRI block.
Placeholders will be replaced in Session 3 (ASPD/HP/SP).

**1.4 equipment_section.py**
11-slot grid: right_hand, left_hand, body, head_top, head_mid, head_low, shoes,
garment, accessory1, accessory2, ammo.
Per row: slot label, item name (resolved via loader), refine spinner (refineable
slots only, 0–20), Edit button.
Weapon Element combo below grid: From Item / Neutral / Water … Undead.
compact_view: weapon name + refine on line 1, slot-count summary on line 2.

**1.5 passive_section.py**
Sub-groups: Self Buffs (SC_AURABLADE, SC_MAXIMIZEPOWER, SC_OVERTHRUST,
SC_OVERTHRUSTMAX), Party Buffs (placeholder), Masteries (12 skills, 0–10
spinboxes), Flags (is_riding_peco checkbox, no_sizefix checkbox,
is_ranged_override radio: Auto / Melee / Ranged).
compact_view: single summary line "N buffs · N masteries · [flags]".

**Phase 1 signal flow (main_window.py)**
_on_build_selected → load file → push to all sections → _run_status_calc()
Any section change → _on_build_changed → collect into PlayerBuild → _run_status_calc()
get_section(key) added to PanelContainer for typed access from MainWindow.

---

## GUI — Combat Output (Phase 2)

**2.1 combat_controls.py**
Skill dropdown (populated from skills.json, job filter). Target search
(QLineEdit → filtered mob list → select → sets target_mob_id).
Environment radio buttons (reserved, not yet wired). compact_mode="none".

**2.2 summary_section.py**
Normal range min–max, avg. Crit range + avg, crit%. Hit% (placeholder 100%
until E1 implemented). compact_mode="none".
Will be updated in Session 2 to show min/avg/max after variance work.

**2.3 step_breakdown.py**
Two-column table (Normal | Crit), one row per DamageStep.
Columns: step name, min/avg/max value. Hover tooltip: note + formula.
"Show Source" toggle reveals hercules_ref column.
compact_mode="compact_view" — but StepsBar in panel.py handles compact display,
not this widget.

**StepsBar (gui/panel.py)**
Combat panel only. Shown when builder_focused, hidden when combat_focused.
Collapsed state: 22px wide, _VerticalBarLabel draws rotated "Steps ▶" text.
Expanded state: 220px, scrollable list of step name + avg value, alternating row
backgrounds. No formula, note, or hercules_ref.
set_visible_bar(False) always resets to collapsed before hiding.
refresh(result) connected to MainWindow.result_updated alongside step_breakdown.

---

## GUI — Target & Incoming (Phase 3)

**3.1 target_section.py**
Full view: mob name, ID, level, HP, DEF, MDEF, element (name + level), size, race,
is_boss flag, base stats sub-section (STR/AGI/VIT/INT/DEX/LUK).
Data source: loader.get_monster_data(mob_id) called from _run_battle_pipeline().
compact_view: single line "MobName  DEF:X  VIT:X  Element/Lv  Size  [Boss]".
Future: swap DEF↔MDEF and add INT for magic skills when magic damage is implemented.

**3.2 incoming_damage.py**
Display-only. Two rows: Mob ATK min–max, Player DEF hard/soft.
refresh_mob(mob_id) + refresh_status(status) called from _run_battle_pipeline().
compact_mode="hidden". Future: summary_section gains compact target info variant
and this section stays hidden in compact view.

**3.3 Custom Target dialog**
Deferred into Phase 4 scope. Not yet implemented.

---

## GUI — Modals (Phase 4)

**4.0 New Build dialog**
Name / job / level form. Saves via BuildManager. Refreshes build dropdown.

**4.1 Equipment Browser dialog**
Filterable item list via loader.get_items_by_type(). Slot-to-EQP mapping filters
items by slot type. Select → fills equipment slot. Edit buttons in equipment
section now enabled.

**4.2 Skill Browser dialog**
Filterable from skills.json. "…" browse button added next to skill combo + level
spinner in combat_controls. Select → sets active skill.

**4.3 Monster Browser dialog**
Filterable from mob_db.json. "Browse…" button added next to target search.
Numeric columns (ID, Lv, HP, DEF) sort as integers via _NumericItem subclass (B2, fixed).

**Fixed bugs during Phase 4**
B1 (QFont::setPointSize <= 0): font size constants clamped to max(1, ...) in app_config.py.
B2 (monster browser numeric sort): _NumericItem subclass sorts by int(text).

---

## GUI — Session 1 Stabilisation

**B3 — StepsBar initial position**
Root cause: `set_focus_state("builder_focused")` made StepsBar visible via `set_visible_bar(True)`,
but no `setSizes` was called on the inner QSplitter — Qt defaulted to 50/50, placing the bar
at mid-panel. Fix: Added `Panel.reset_steps_to_collapsed()` (sets inner splitter to
`[total - _BAR_W, _BAR_W]`). Called via `QTimer.singleShot(0, ...)` from
`PanelContainer.set_focus_state` after `set_visible_bar(True)`, deferring until after
layout geometry is computed.

**B4 — Steps expand doesn't nudge outer splitter**
Root cause: StepsBar `expand_requested`/`collapse_requested` were connected only to
`Panel._on_steps_expand`/`_on_steps_collapse` (inner splitter resize). The outer splitter
nudge in `PanelContainer._on_section_expand_requested` was not reached.
Fix: Added `Panel.steps_expand_requested`/`steps_collapse_requested` signals that forward
from StepsBar. `PanelContainer.__init__` connects these to the outer-splitter nudge handlers.

**B5 — Target sections blank after pipeline error**
Root cause: `_run_battle_pipeline` except block called `refresh_mob(None)` and
`refresh_status(None)`, clearing the mob display on any pipeline exception.
Fix: Target/incoming refresh calls kept before the try block. Except block now sets
`result = None` and falls through to a single `result_updated.emit(result)` call.
Mob info stays visible regardless of pipeline success.

**B6 — Normal Attack absent from skill dropdown**
Root cause: `skills.json` has no id=0 entry; `loader.get_all_skills()` never returns
Normal Attack. Without it, crit branch was unreachable for the most common use case.
Fix: Synthetic `"Normal Attack  (id=0)"` prepended as the first item in the
`CombatControlsSection` skill combo, with `userData={"id": 0, "name": "Normal Attack"}`.

**B7 — Overrefine showing 0 — RESOLVED (not a bug)**
Session 3 investigation: all tested weapons were event/costume variants (_C suffix)
with `refineable: false` in item_db.json. The code correctly suppresses overrefine
for non-refineable weapons. The test builds (agi_bs.json) used wrong item IDs.
Debug print removed. No code change needed.

---

## GUI — Session 2 (Partial)

**C1a — VIT DEF avg off-by-0.5**
Fixed in `defense_fix.py`. Both PC and monster branches changed:
`(variance_max - 1) // 2` → `variance_max // 2`.
Rationale: avg of `rnd()%n` is `(n-1)/2`; floor gave 0.5 below exact for even n;
`variance_max//2` rounds half-up, correctly representing the expected value.

**C1 (full variance distribution) — deferred, needs design**
`DamageRange(min, max, avg)` cannot reconstruct the full probability distribution
needed for Phase 7 histogram. Three independent uniform RVs (weapon ATK, overrefine,
VIT DEF) must be convolved. Requires a planning session in web Claude to choose
between exact convolution, Irwin-Hall approximation, or Monte Carlo before
any code changes. See GUI_PLAN.md Session 2 handover for full spec.

**E1 Hit/Miss — deferred to Session 3**
Hercules formulas verified (see GUI_PLAN.md Session 2 handover for complete spec
including required file changes). Not implemented this session due to context limit.

---

## Session 3 — E1 Hit/Miss + C3 ASPD/HP/SP

**B7 resolution** — see B7 entry in Session 1 section above.

**E1 — Hit/Miss**
`core/models/target.py` — added `agi: int = 0` for mob_FLEE calculation.
`core/data_loader.py` — `get_monster()` now populates `target.agi` from `stats.agi`.
`core/config.py` — added `min_hitrate: int = 5`, `max_hitrate: int = 100`.
`core/models/damage.py` — added `perfect_dodge: float = 0.0` to `BattleResult`.
`core/calculators/modifiers/hit_chance.py` — new file:
  `calculate_hit_chance(status, target, config) -> tuple[float, float]`
  Returns (hit_chance_pct, perfect_dodge_pct).
  `mob_FLEE = mob.level + mob.agi` (status.c mob flee formula)
  `hitrate = clamp(80 + player_HIT - mob_FLEE, min_hitrate, max_hitrate)`
  `perfect_dodge_pct = (target.luk + 10) / 10.0` (flee2/10 as %)
  Source: battle.c:4469/5024/4799 (#ifndef RENEWAL)
  TODO: unmodelled modifiers noted in the function docstring (skill per-level HIT
  bonuses, SC_FOGWALL, arrow_hit, agi_penalty_type).
`core/calculators/battle_pipeline.py` — calls `calculate_hit_chance`, replaces
  `hit_chance=100.0` placeholder in `BattleResult`.
`gui/sections/summary_section.py` — Hit row now shows hit% and perfect_dodge%.

**C3 — ASPD / HP / SP**
`tools/import_job_db.py` — new scraper for `Hercules/db/pre-re/job_db.conf`.
  Extracts BaseASPD (per weapon_type), HPTable, SPTable for 33 pre-renewal jobs.
  Resolves Inherit / InheritHP / InheritSP chains.
  Maps job_db.conf weapon keys → item_db weapon_type strings.
  Output: `core/data/pre-re/tables/job_db.json` (33 jobs, 150-level tables).
`core/data_loader.py` — added `get_job_entry(job_id)`, `get_aspd_base(job_id, weapon_type)`,
  `get_hp_at_level(job_id, level)`, `get_sp_at_level(job_id, level)`.
`core/models/build.py` — added 3 Session 4 stubs:
  `bonus_aspd_add: int = 0` — flat amotion reduction from bAspd items
  `bonus_maxhp: int = 0` — flat MaxHP addend from items/cards
  `bonus_maxsp: int = 0` — flat MaxSP addend from items/cards
`core/calculators/status_calculator.py` — real ASPD/HP/SP formulas (replaces placeholders):
  ASPD: `amotion = aspd_base - aspd_base*(4*agi+dex)//1000 + bonus_aspd_add`
        peco penalty: `amotion += 500 - 100*KN_CAVALIERMASTERY_lv`
        aspd_percent modifier: `amotion *= (1000 - pct*10) // 1000`
        clamped to [2000 - max_aspd*10, 2000]; displayed = (2000-amotion)//10
  MaxHP: `HPTable[job_id][level-1] * (100 + vit) // 100 + bonus_maxhp`
  MaxSP: `SPTable[job_id][level-1] * (100 + int_) // 100 + bonus_maxsp`
  Source: status.c status_base_amotion_pc + status_calc_pc_ (#ifndef RENEWAL_ASPD)

---

## Session 4 — B8 Save button + D5/D4 Script parsing + Gear bonuses

**B8 — Save button**
`gui/main_window.py` — added `_save_btn` QPushButton in `_build_top_bar()`.
  Enabled when a named build is loaded; disabled otherwise.
  `_on_save_build()`: calls `_collect_build()` then `BuildManager.save_build(build, path)`.
  Overwrites existing file without confirmation.

**Pre-Session 4 gate — bonus distribution (2144 items with scripts)**
- bonus (arity 1): 73 unique types. Top damage-relevant: bStr/Agi/Vit/Int/Dex/Luk,
  bAllStats, bBaseAtk(94), bHit(60), bFlee(79), bCritical(82), bMaxHP(85), bMaxSP(82),
  bDef(72), bAspdRate(86), bCritAtkRate(16), bLongAtkRate(8), bAspd.
- bonus2 (arity 2): 38 unique types. Top: bAddRace(205), bSubEle(200), bSubRace(142),
  bSkillAtk(96), bIgnoreDefRate(65), bAddSize(37) — E2 stubs (race/size/element mults).
- bonus3 (arity 3): 9 unique types. bAutoSpell(142) — procs, not damage calc.
- Decision: ~15 bonus types routed to existing PlayerBuild fields.
  bonus2/bonus3 race/size/element multipliers stored in GearBonuses for E2.
  Description templates cover top ~25 types.

**D5 — Item Script Parser**
`core/models/item_effect.py` — new `ItemEffect` dataclass:
  `bonus_type: str, arity: int, params: list, description: str`
`core/item_script_parser.py` — new `parse_script(script: str) -> list[ItemEffect]`
  Regex-based parser for bonus/bonus2/bonus3 calls in Hercules script strings.
  Description template table: ~35 bonus1, ~25 bonus2, 9 bonus3 types.
  Verified test cases:
  - Alice Card: `bonus2 bSubRace,RC_Boss,40` → "Reduces damage from Boss monsters by 40%."
  - Picky Card: `bonus bStr,1; bonus bBaseAtk,10` → str_=1, batk=10
  - bAllStats,2 → all 6 stats += 2

**D4 — Gear Bonus Aggregator**
`core/models/gear_bonuses.py` — new `GearBonuses` dataclass.
  Flat stat fields: str_, agi, vit, int_, dex, luk, batk, hit, flee, flee2, cri,
  crit_atk_rate, long_atk_rate, def_, maxhp, maxsp, aspd_percent, aspd_add.
  E2 stub dicts: add_race, sub_ele, sub_race, add_size, add_ele, ignore_def_rate, skill_atk.
  all_effects: List[ItemEffect] for tooltip use.
`core/gear_bonus_aggregator.py` — new `GearBonusAggregator.compute(equipped) -> GearBonuses`.
  Iterates all equipped slots, parses scripts, routes effects via _BONUS1_ROUTES dict.

**Wiring (main_window.py)**
`gui/main_window.py` — `_apply_gear_bonuses(build) -> PlayerBuild`:
  Calls `GearBonusAggregator.compute(build.equipped)`, returns `dataclasses.replace(build, ...)`
  with all bonus_* fields augmented by gear bonuses.
  Original build unchanged → save_build always writes clean manual values.
  Called in `_run_status_calc()` and `_run_battle_pipeline()` before StatusCalculator.

---

## Session 5 — F2/F5/F6 Equipment Correctness + Derived Section Live Stats

**F2 — Armor base DEF from item_db**
`gui/sections/equipment_section.py` + `gui/main_window.py`: armor DEF now read from
`item_db.json` and summed into `StatusCalculator` hard DEF input.

**F5 — 2H weapon locks left hand**
When a 2H weapon is equipped, the L. Hand slot is disabled and cleared.
Enforced in `equipment_section.py` on item select and on load.

**F6 — Assassin dual-wield restriction**
L. Hand slot enabled only for Assassin (job_id 12) and Assassin Cross (job_id 24).
All other jobs have the slot locked with a tooltip explanation.
Enforced in `equipment_section.py` driven by `build.job_id`.

**Derived section live stats**
`gui/sections/derived_section.py` updated to display live ASPD, MaxHP, MaxSP from
`StatusData`. Previously these showed placeholder values.

---

## Session A — Pipeline Gaps G1/G2/G3/G5/G6/G8/G11

**W1 — Target model extended (G6)**
`core/models/target.py`: 9 new fields added for PvP/incoming-damage support:
`sub_race, sub_ele, sub_size` (Dict[str,int]); `near_attack_def_rate`,
`long_attack_def_rate`, `magic_def_rate`, `mdef_`, `int_`, `armor_element`, `flee`.
All default to 0 / {}. Mobs unaffected (defaults apply).

**W2 — GearBonuses + aggregator + parser extended**
`core/models/gear_bonuses.py`: 4 new fields: `near_atk_def_rate`, `long_atk_def_rate`,
`magic_def_rate`, `atk_rate`.
`core/gear_bonus_aggregator.py`: 4 new routes in `_BONUS1_ROUTES`.
`core/item_script_parser.py`: 4 new description templates.

**W3 — loader.get_monster() populates mdef_ and int_ (G28 partial)**
`core/data_loader.py`: `Target.mdef_` ← `entry["mdef"]`; `Target.int_` ← `stats["int"]`.

**W4 — SC_IMPOSITIO fixed (G1)**
`core/calculators/modifiers/base_damage.py`: SC_IMPOSITIO level×5 added to `atkmax`
after weapon ATK, before atkmin. Previously misclassified as renewal-only.
Source: status.c #ifndef RENEWAL ~line 4562.

**W5 — Arrow ATK for bow builds (G3)**
`base_damage.py`: for Bow weapon type, fetches ammo `atk` from item_db and adds to
`atkmax`. Missed entirely in original implementation.

**W6 — CardFix implemented (G2, G8, G11)**
`core/calculators/modifiers/card_fix.py`: new file.
Attacker side: add_race + add_ele + add_size (with RC_All/Ele_All/Size_All) + atk_rate
+ long_atk_rate (BF_LONG). Boss/NonBoss RC keys included.
Target side (is_pc only): sub_ele + sub_size + sub_race + near/long_attack_def_rate.
Wired in `battle_pipeline.py` after AttrFix, before FinalRateBonus.
Gotcha: atk_rate consumed here but Hercules applies it before SkillRatio (G10 ~partial).

**W7 — VIT DEF PC formula confirmed (G7)**
No code change. `defense_fix.py` formula already matches battle.c:1487-1488.
Branch activates in Session D when `player_build_to_target()` is implemented.

**W8 — ignore_def wired (G5)**
`defense_fix.py`: reads `gear_bonuses.ignore_def_rate[race_rc]` + `[boss_rc]`.
Partial ignore reduces hard DEF proportionally; 100%+ zeroes it.

**W9 — GearBonuses + CardFix wired in pipeline**
`battle_pipeline.py`: `gear_bonuses = GearBonusAggregator.compute(build.equipped)`
hoisted to top of `_run_branch()`. `DefenseFix` and `CardFix` receive `gear_bonuses`.

**Docs maintenance**
Root planning files moved/deleted: `GUI_PLAN.md` → `docs/gui_plan.md`,
`COMPLETED_WORK.md` → `docs/completed_work.md`, `PHASES_DONE.md` → `docs/phases_done.md`,
`GUI_TODO.md` deleted, `MODELS.md` deleted.
`CLAUDE.md` updated: pipeline order, SC_IMPOSITIO note, card_fix.py entry, new docs refs,
end-of-session maintenance checklist added.

---

## Session B — MATK + BF_MAGIC Outgoing Pipeline

**B1 — MATK in StatusCalculator (G18)**
`core/models/status.py`: added `matk_min`, `matk_max`, `mdef`, `mdef2` fields.
`status_calculator.py`: `matk_min = int_ + (int_//7)**2`, `matk_max = int_ + (int_//5)**2`.
Gotcha: roadmap text had typo for matk_max (`int_**2 + ...`); Hercules source is `int_ + (int_//5)**2`.
Both test values (295/460 for INT=99) confirmed against source.

**B2 — MDEF in StatusCalculator (G25)**
`status.mdef = build.equip_mdef` (hard, from bMdef scripts).
`status.mdef2 = int_ + vit//2` (soft, status.c:3867 #else not RENEWAL).
`core/models/build.py`: added `equip_mdef: int = 0`.
`core/models/gear_bonuses.py`: added `mdef_: int = 0` + `ignore_mdef_rate: Dict`.
`core/gear_bonus_aggregator.py`: added `bMdef` route + `bIgnoreMdefRate` arity-2 route.
`gui/main_window.py`: wired `equip_mdef` in `_apply_gear_bonuses`.
Note: IT_ARMOR items have no raw `mdef` field in item_db.json — equip MDEF comes from bMdef scripts only.

**B3 — MATK + MDEF rows in derived_section (G21)**
`gui/sections/derived_section.py`: MATK row (shows "min–max"), MDEF row (shows "hard + soft").

**B4 — Magic skill ratios (G22)**
`core/calculators/modifiers/skill_ratio.py`: `_BF_MAGIC_RATIOS` dict (15 pre-renewal spells from
battle.c:1631-1785). `calculate_magic()` returns `(dmg, hit_count_raw)` — raw sign preserved.
Key discovery: `damage_div_fix` macro (battle.c:3823): positive div → actual multi-hit (dmg × N);
negative div → cosmetic multi-hit (dmg unchanged, div negated for display only).
WZ_FIREPILLAR has negative number_of_hits → cosmetic, no multiplication.
`hit_count` is returned separate from ratio so MagicPipeline can apply after defense+attr_fix.

**B5 — DefenseFix.calculate_magic (G20, G24)**
`core/calculators/modifiers/defense_fix.py`: `calculate_magic()` added.
Formula: `damage * (100-mdef)/100 - mdef2` (magic_defense_type=0 default, battle.c:1585).
`mdef2` computed inline from `target.int_ + (target.vit >> 1)` (not stored on Target).
`ignore_mdef_rate` wired: reads `gear_bonuses.ignore_mdef_rate[race_rc + boss_rc]`.

**B6 — CardFix.calculate_magic (G23)**
`core/calculators/modifiers/card_fix.py`: `calculate_magic()` added.
Target-side only (mob target gets info-only step).
Applies: sub_ele(magic element), sub_race(RC_DemiHuman), magic_def_rate.
Attacker-side magic bonuses correctly omitted — #ifdef RENEWAL in Hercules.

**B7 — MagicPipeline (G19)**
`core/calculators/magic_pipeline.py`: new file.
Step order (exact per battle_calc_magic_attack):
  MATK roll → SkillRatio (per-hit) → DefenseFix (per-hit) → AttrFix (per-hit) → Hit count ×N → CardFix(magic) → FinalRateBonus
SC_MAXIMIZEPOWER: uses matk_max (no roll) when active.
Skill element from skills.json `element` field ("Ele_Fire" → strip prefix → "Fire" for attr_fix lookup).
`BattleResult.magic: Optional[DamageResult]` added to damage.py; mirrored to `.normal` for GUI.
`battle_pipeline.py`: routes `attack_type == "Magic"` skills to MagicPipeline.
Note: matk_percent and skillatk_bonus are stubs (no GearBonuses fields yet).
