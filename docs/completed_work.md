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

---

## Session C

**C1 — ASC_KATAR percentage mastery (G4)**
`core/calculators/modifiers/mastery_fix.py`: ASC_KATAR block added after the flat mastery step.
Formula from battle.c:927-929 `#else` (pre-renewal): `damage += damage * (10 + 2*skill_lv) / 100`.
Implemented as `dmg.scale(100 + 10 + 2*lv, 100)` — e.g. lv5 → ×1.20, lv10 → ×1.30.
Only fires when `weapon.weapon_type == "Katar"` and `asc_katar_lv > 0`.
`gui/sections/passive_section.py`: ASC_KATAR row added to `_MASTERIES`; `_MASTERY_JOB_FILTER`
dict added to restrict row visibility to job_id=24 (Assassin Cross); `update_job(job_id)` method
hides row and resets spin to 0 for other jobs; wired from `load_build` and `job_changed` signal.

**C2 — ASPD skill buffs (G9, partial)**
`core/calculators/status_calculator.py`: SC ASPD reduction block added after flat `bonus_aspd_add`.
Uses `status_calc_aspd_rate` 1000-scale approach (source confirmed by user testing — 30% reduction
for SC_TWOHANDQUICKEN matches val2=300, not the flag&1 branch `bonus=7` which yields ~7%).
Only the highest single SC reduction applies (no SC-to-SC stacking): `max()` across all active SCs.
Values: SC_TWOHANDQUICKEN/SC_ONEHANDQUICKEN = 300; SC_ADRENALINE = 300 (self assumed);
SC_SPEARQUICKEN = 200+10×level. Gear bonuses (`bonus_aspd_add`, `bonus_aspd_percent`) apply in
subsequent steps and DO stack with SC bonuses.
SC_ASSNCROS deferred: val2 = f(Bard's AGI) — needs party buff input system. Currently does nothing.
`gui/sections/passive_section.py`: 5 ASPD SC checkboxes added to `_SELF_BUFFS` (SC_SPEARQUICKEN
uses `has_level=True` because val2 is level-dependent). See docs/aspd.md for full investigation.

**C3 — bAtkRate pipeline position fix (G10)**
`core/calculators/battle_pipeline.py`: `bAtkRate` step added between BaseDamage and SkillRatio.
Source: battle.c:5330 `#ifndef RENEWAL`: `ATK_ADDRATE(sd->bonus.atk_rate)`.
`core/calculators/modifiers/card_fix.py`: `atk_rate` removed from the CardFix attacker-side
`atk_bonus` sum where it was incorrectly placed (post-defense, post-AttrFix).

---

## Session D — Partial (Hercules investigation + armor_element stub)

**G27 — armor_element field**
`core/models/build.py`: `armor_element: int = 0` added.
`core/build_manager.py`: saved under `flags.armor_element`; loaded with default 0.

**Mob ATK architecture investigation**
Determined two-part mob ATK: weapon component `[atk_min, atk_max-1]` from mob_db +
`batk = str + (str//10)^2` from stats.str (BL_MOB path, no dex/luk).
Source: mob.c:4937 mob_read_db_sub; status.c:3749 status_base_atk #else not RENEWAL.
Key finding: SC buffs (Provoke etc.) modify `rhw.atk/atk2` (weapon component), not batk.
Design decision: pipeline computes baseline internally from mob_db; `mob_atk_bonus_rate`
parameter provides the buff/debuff hook. See current_state.md Session D for full notes.

**G33 confirmed done from Session B** — MDEF in StatusData/StatusCalculator already complete.

---

## Session E — Incoming Pipelines (G7, G26–G29, G31–G32)

**E1 — player_build_to_target() (item 1)**
`core/build_manager.py`: new static method `player_build_to_target(build, status, gear_bonuses) -> Target`.
Maps player's StatusData + GearBonuses into a Target with `is_pc=True`, size=Medium,
race=DemiHuman, element_level=1. Activates G7 (PC VIT DEF branch) automatically.
`sub_size={}` — GearBonuses has add_size (offensive) not sub_size (defensive); stubbed.
New imports: GearBonuses, StatusData, Target at top-level (no circular dependency).

**E2 — IncomingPhysicalPipeline (item 2, G26, G28, G29)**
`core/calculators/incoming_physical_pipeline.py`: new file.
Steps: MobBaseATK → AttrFix → DefenseFix(is_pc=True) → CardFix.calculate_incoming_physical().
Mob ATK computed internally from mob_db (`atk_min/atk_max` + batk from stats.str).
`mob_atk_bonus_rate: int = 0` parameter for future buff/debuff SC effects (mirrors Hercules
SC modification of rhw.atk/atk2). Batk kept separate (not modified by most SCs).
Mob ATK note: "fixed at spawn" — correct framing per Hercules mob_read_db_sub.
DefenseFix called with `build=None`, `GearBonuses()` (mob has no attacker-side gear/cards).
`core/calculators/modifiers/card_fix.py`: new `calculate_incoming_physical(mob_race, mob_element,
mob_size, is_ranged, player_target, dmg, result)`. Keys player's sub_ele/sub_race/sub_size
against mob's actual race/element/size (not hardcoded DemiHuman like the outgoing path).

**E3 — IncomingMagicPipeline (item 3, G31, G32)**
`core/calculators/incoming_magic_pipeline.py`: new file.
Steps: MobMATKRoll → SkillRatio (optional) → AttrFix → DefenseFix.calculate_magic()
→ CardFix.calculate_incoming_magic().
Mob MATK: `int_ + (int_//7)^2` to `int_ + (int_//5)^2` from mob_data stats.int.
`mob_matk_bonus_rate: int = 0` for future buff/debuff support.
Optional `skill: SkillInstance` — when provided, applies skill ratio and resolves element
from skills.json; falls back to mob's natural element. `build=None` safe (SkillRatio unused it).
`core/calculators/modifiers/card_fix.py`: new `calculate_incoming_magic(mob_race, magic_ele_name,
player_target, dmg, result)`. Uses mob's actual race for sub_race lookup (not hardcoded
RC_DemiHuman like `calculate_magic` which assumes player-vs-player).
Empty `GearBonuses()` passed to DefenseFix — mob has no ignore_mdef cards.

**E4 — IncomingDamageSection rebuilt (item 4)**
`gui/sections/incoming_damage.py`: complete rewrite. Old stub (refresh_mob + refresh_status)
replaced with step breakdown panel.
Physical/Magic toggle buttons (mutually exclusive without QButtonGroup).
Summary row: `Physical: min–avg–max  Magic: min–avg–max`.
Step table with Show Source toggle — same pattern as step_breakdown.py.
New public API: `refresh(physical: DamageResult, magic: DamageResult)`.

**E5 — Armor element selector (item 5)**
`gui/sections/equipment_section.py`: new `_armor_element_combo` (QComboBox, 10 elements, default
Neutral). Added after weapon element row. Connects to `equipment_changed` signal.
`load_build()`: reads `build.armor_element` (int 0-9) with signals blocked.
`collect_into()`: writes `build.armor_element` back. Save/load already wired via Session D's
`flags.armor_element` in build_manager.py — no changes needed there.

**E6 — Wire incoming pipelines (item 6)**
`gui/main_window.py`: imports + instances for IncomingPhysicalPipeline, IncomingMagicPipeline.
`_run_battle_pipeline()`: computes gear_bonuses and player_target once; runs both incoming
pipelines when mob_id is set; calls `_incoming_damage.refresh(phys, magic)`.
Old `refresh_mob` + `refresh_status` calls removed.

**New gap added**
G43 [ ]: Incoming pipeline attack type not skill-driven. GUI has no mob skill picker.
Physical pipeline always assumes auto-attack; magic pipeline defaults to mob natural element.
Needs design decision on UI surface before implementation.

---

## Session F — Incoming Config Controls + Unified Target Selector (G43, G30)

_Two sub-sessions (F1 = incoming config; F2 = target selector redesign). Documented together._

**F1-1 — Incoming config controls (G43)**
`gui/sections/incoming_damage.py`: config row added to IncomingDamageSection header.
- Ranged QCheckBox (passes `is_ranged=True` to IncomingPhysicalPipeline → activates
  BF_LONG in CardFix, enabling bLongAtkDef resistance cards).
- Magic element override QComboBox (10 elements + "Mob natural" default).
- Ratio QSpinBox 0–1000% (synthetic skill ratio for IncomingMagicPipeline).
- `get_incoming_config() -> tuple[bool, Optional[int], Optional[int]]` public API.
- `config_changed = Signal()` wired to `_run_battle_pipeline` in main_window.

`core/calculators/incoming_magic_pipeline.py`:
- `ele_override: Optional[int] = None` — substitutes mob natural element when set.
- `ratio_override: Optional[int] = None` — substitutes skill ratio when set.
Both default to None = original behavior preserved.

**F1-2 — dark.qss target label style**
`gui/themes/dark.qss`: `QLabel#combat_target_display` prominent style (13px bold,
dark background). `QPushButton#target_mode_btn:checked` red (#e05555) for Player mode.

**F2-1 — save_build cached_display (G0)**
`core/build_manager.py`: `save_build()` now writes `cached_display: {job_name, hp, def_, mdef}`
alongside the existing schema. Computed at save time from raw (pre-gear-bonus) build.
- `job_name`: `loader.get_job_entry(build.job_id)["name"]` (or "" if missing).
- `hp`: `get_hp_at_level(job_id, base_level) * (100 + base_vit + bonus_vit) // 100 + bonus_maxhp`.
- `def_`: `build.equip_def`.
- `mdef`: `build.equip_mdef`.
Older saves without `cached_display` degrade gracefully ("?" in the browser).

**F2-2 — MonsterBrowserDialog MDef column (G1)**
`gui/dialogs/monster_browser.py`: MDef column inserted at index 5 (after DEF).
Element/Race/Size/Boss shifted to indices 6–9. `_NUMERIC_COLS` updated to include 5.

**F2-3 — PlayerTargetBrowserDialog (G2)**
`gui/dialogs/player_target_browser.py`: new file.
Same QDialog structure as MonsterBrowserDialog.
Columns: Name / Job / Lv / HP / DEF / MDEF. Numeric sort on Lv/HP/DEF/MDEF.
Reads `cached_display` from each `{stem}.json` in saves_dir — no full load.
`selected_build_stem() -> Optional[str]` public API.
Filter search by display name (≥0 chars — immediate, no threshold).
Older saves (missing cached_display) show "?" for stats — graceful.

**F2-4 — CombatControlsSection redesign (G3)**
`gui/sections/combat_controls.py`: full rewrite of the target area.
State added: `_target_type: str = "mob"`, `_target_pvp_stem: Optional[str] = None`,
`_player_build_pairs: list[tuple[str, str]]`.
Mode toggle QPushButton (objectName="target_mode_btn", checkable):
- Unchecked = "Mob" mode: search filters mob list, Browse opens MonsterBrowserDialog.
- Checked = "Player" mode: search filters build display names, Browse opens PlayerTargetBrowserDialog.
Same QListWidget used for both modes. Label renamed to objectName="combat_target_display".
New public methods: `get_target_pvp_stem() -> Optional[str]`, `refresh_target_builds(pairs)`.
`get_target_mob_id()` returns None in Player mode (mob_id meaningful only in Mob mode).
`load_build()`: always resets to Mob mode (pvp target is session-only, not saved).
`collect_into()`: sets `build.target_mob_id = None` in Player mode.
`refresh_target_builds()`: if current pvp_stem absent from new pairs, clears it.

**F2-5 — main_window.py wiring (G4)**
`gui/main_window.py`:
- Added `from core.models.skill import SkillInstance`.
- `_refresh_builds()`: TODO stub replaced; calls `refresh_target_builds(pairs)` after combo refresh.
- `_run_battle_pipeline()`: TODO stub replaced; full pvp path:
  - If `pvp_stem` set: loads pvp build → applies gear bonuses → resolves weapon →
    runs StatusCalculator → calls `player_build_to_target` → sets `target` for outgoing pipeline.
  - Incoming: runs `_pipeline.calculate(pvp_status, pvp_weapon, SkillInstance(), player_target, pvp_eff)`
    and uses `pvp_battle.normal` as `phys_result`. Magic incoming suppressed in PvP mode.
  - Mob path unchanged (fallback when pvp_stem is None).

**Layout change**
`gui/layout_config.json`: target_section moved above summary_section in combat panel.
New order: Combat Controls → Target Info → Summary → Step Breakdown → Incoming Damage.

**Pre-existing bug fixed (opportunistic)**
`gui/sections/incoming_damage.py`: `QComboBox` added to PySide6 imports (was missing since F1,
caused startup crash when magic element combo was introduced).

---

## Session I — PMF Migration (DamageRange → dict[int, float])

**Goal**: Complete the DamageRange → PMF migration started in Session H. Wire all
modifiers and pipelines to use `dict[int, float]` probability mass functions.

**I1 — Modifier conversions (9 files)**
All modifiers converted from `dmg: DamageRange` → `pmf: dict`. Return type `DamageRange` → `dict`.
Pattern applied uniformly:
- `DamageRange` import removed; `from pmf.operations import ...` added
- `dmg.scale(n, d)` → `_scale_floor(pmf, n, d)`
- `dmg.add(n)` → `_add_flat(pmf, n)`
- `dmg.subtract(lo, hi, _)` → `_subtract_uniform(pmf, lo, hi)`
- `dmg.floor_at(1)` → `_floor_at(pmf, 1)`
- `mn, mx, av = pmf_stats(pmf)` used before every `result.add_step()` call
Files: `skill_ratio.py`, `crit_atk_rate.py`, `defense_fix.py`, `active_status_bonus.py`,
`refine_fix.py`, `mastery_fix.py`, `attr_fix.py`, `card_fix.py`, `final_rate_bonus.py`.
All 4 static methods in `card_fix.py` converted (including `calculate_incoming_physical`
and `calculate_incoming_magic`).

**I2 — Pipeline conversions (4 files)**
`battle_pipeline.py`:
- `DamageRange` import removed; `_scale_floor, pmf_stats` added
- `dmg: DamageRange` → `pmf: dict` throughout `_run_branch`
- bAtkRate inline block converted
- All modifier call sites updated to pass `pmf`
- Final: `mn, mx, av = pmf_stats(pmf)`, `result.pmf = pmf`, min/max/avg set from stats

`magic_pipeline.py`:
- MATK base roll: `DamageRange(min, max, avg)` → `_uniform_pmf(matk_min, matk_max)` or `{matk_max: 1.0}` for SC_MAXIMIZEPOWER
- All modifier calls updated; `result.pmf = pmf` at end

`incoming_physical_pipeline.py`:
- Mob ATK roll: `DamageRange(eff_min, eff_max, eff_avg)` → `_uniform_pmf(eff_min, eff_max)`
- DefenseFix and CardFix call signatures updated

`incoming_magic_pipeline.py`:
- Mob MATK roll: `DamageRange(matk_min, matk_max, avg)` → `_uniform_pmf(matk_min, matk_max)`
- All modifier calls updated

**I3 — Orphaned file note**
`core/calculators/modifiers/size_fix.py` still references `DamageRange` but is not
imported anywhere (SizeFix was absorbed into `base_damage.py` in Session A). Not
converted — would only matter if imported, which nothing does.

**Verification**
Poring target, Agi BS: PSCalc 381/388/396 crit, 281/337/395 normal — matches reference
381~396 / 281/338/395 (avg diff is rounding method difference, not a bug).
Knight of Abyss: PSCalc 428/435/443 crit, 80/116/154 normal — matches reference 428~443 / 80/117/154.

---

## Session G — Card Slots + Armor Refine DEF

**G1 — Armor refine DEF scraper (G12)**
`tools/import_refine_db.py`: parses `Hercules/db/pre-re/refine_db.conf` Armors block,
extracts `StatsPerLevel: 66`. Output: `core/data/pre-re/tables/refine_armor.json`.

**G2 — Armor refine DEF in pipeline (G12)**
`core/data_loader.py`: `get_armor_refine_units(refine)` → `refine × 66`.
`core/gear_bonus_aggregator.py`: signature changed to `compute(equipped, refine_levels=None)`.
  - For each IT_ARMOR slot, accumulates raw units: `refine_level × 66`.
  - After loop: `bonuses.def_ += (refinedef_units + 50) // 100` (aggregate rounding).
  - Source: status.c ~1655,1713. Verified: +10 armor → 7 DEF (≈ 2/3 per level, matches in-game).
All 5 call sites updated to pass `build.refine_levels`:
  `battle_pipeline.py`, `magic_pipeline.py`, `main_window.py` (×3).

**G3 — Card slot UI (G13)**
`gui/sections/equipment_section.py`:
  - Added `QVBoxLayout` container in grid col 1: item name on top, card button row below.
  - `_card_ids: dict[str, list[Optional[int]]]` — tracks card IDs per slot.
  - `_card_btns: dict[str, list[QPushButton]]` — card buttons per slot (objectName="card_slot_btn").
  - `_refresh_card_slots(slot_key)`: rebuilds card buttons from item's `slots` count; hides row if 0.
  - `_open_card_browser(slot_key, card_index)`: opens EquipmentBrowserDialog with `item_type_override="IT_CARD"`.
  - `_resolve_card_label()`: strips " Card" suffix, truncates to 10 chars.
  - `collect_into()`: writes `{slot}_card_0` … `{slot}_card_{N-1}` into `build.equipped` after base slots.
  - `load_build()`: reads card keys from `build.equipped`, calls `_refresh_card_slots()` per slot.
  - Card keys are additional entries in `build.equipped` — no `build_manager.py` structural change needed.

**G4 — Equipment browser fixes (G13 + opportunistic)**
`gui/dialogs/equipment_browser.py`:
  - Bug fix: `EQP_ACC_L`/`EQP_ACC_R` → `EQP_ACC` for both accessory slots.
    All IT_ARMOR accessories and IT_CARD accessory cards use `EQP_ACC`; the old filter
    produced an empty intersection (zero items in the browser).
  - Added `item_type_override: Optional[str] = None` parameter. When `"IT_CARD"`, filters
    IT_CARD items using the same `_SLOT_EQP` loc intersection as regular items.
    Window title updated to include "— Cards" suffix. F6 dual-wield merge skipped for cards.

---

## Session H — PMF Foundation

**Goal**: Create the pmf/ package and begin the DamageRange → PMF migration.
Completed during the C1 variance planning session; app intentionally broken until Session I wires all pipelines.

**H1 — pmf/ package**
Created: `pmf/__init__.py`, `pmf/operations.py`, `pmf/statistics.py`, `pmf/single_hit.py`.
PMF represented as `dict[int, float]` (damage value → probability).
Key operations: `_uniform_pmf`, `_scale_floor`, `_add_flat`, `_subtract_uniform`, `_floor_at`, `pmf_stats`.

**H2 — DamageResult.pmf field**
`core/models/damage.py`: `DamageRange` removed; `pmf: dict` field added to `DamageResult`.

**H3 — base_damage.py PMF conversion**
`core/calculators/modifiers/base_damage.py` fully converted to PMF ops (returns `dict[int,float]`).
Crit branch: single spike at atkmax. Normal: `_uniform_pmf(atkmin, atkmax)`.
Overrefine: subtracted via `_subtract_uniform`.

**H4 — requirements.txt + CLAUDE.md**
`requirements.txt`: `scipy>=1.13` added. `CLAUDE.md`: pre-alpha notice added.

---

## Session J1 — Skill combo job filter (G34 partial)

**Goal**: Filter skill combo to current job, handle multi-job skills correctly.
Stopped at G34 due to context limit; G35/G36/G37 deferred to Session J2.

**J1-scraper — `tools/import_skill_tree.py` + `core/data/pre-re/tables/skill_tree.json`**
New scraper reads `Hercules/db/pre-re/skill_tree.conf`, parses job blocks with inheritance
chains, resolves skills recursively (own + all inherited), and emits
`skill_tree.json` — `{job_id_str: [sorted_skill_names]}` for all 33 jobs in the ID mapping.
  - Key insight: `skill_db.conf` (skills.json) has **no job field** — the job→skill mapping
    lives in `skill_tree.conf`. Multi-job shared skills (e.g., SM_BASH for all Swordsman classes)
    are handled correctly by inheritance resolution.
  - Job name → ID mapping: skill_tree.conf uses `Magician` (we show "Mage"), `Whitesmith`
    (we show "Mastersmith"), `Professor` (we show "Scholar") — mapping table in scraper.

**J1-loader — `DataLoader.get_skills_for_job(job_id) → frozenset[str]`**
Loads `skill_tree.json`, returns frozenset of skill names for the given job_id.

**G34 — Skill combo job filter (`combat_controls.py`)**
  - `_repopulate_skill_combo(job_id, preserve_selection)`: rebuilds the skill QComboBox filtered
    to `loader.get_skills_for_job(job_id)`. If the previously selected skill is no longer in the
    filtered set, falls back to Normal Attack (index 0) and emits `combat_settings_changed`.
  - Rogue (17) and Stalker (34) also include all skills with `AllowPlagiarism` in skill_info
    (sourced from skills.json — currently 5 skills match in the DB).
  - "All" QCheckBox in the skill row bypasses the filter (shows all 1168 skills).
  - `update_job(job_id)` public method: stores job_id, calls `_repopulate_skill_combo`.
  - Wired in `main_window.py`: `build_header.job_changed → combat_controls.update_job`.
  - Normal Attack (id=0) always shown at top regardless of filter.

---

## Session J2 — Remaining job filters (G35, G36, G37)

**Scraper fix (prerequisite for G35)**
- `tools/import_item_db.py`: `parse_job_list()` now outputs `list[int]` job IDs using
  `_HERCULES_JOB_TO_IDS` inheritance map. Hercules base-class names expand to all promoted
  descendants (e.g. `"Knight": true` → `[7, 23]`). `item_db.json` re-scraped (2760 items).
- `CLAUDE.md`: Added "IDs Over Name Strings" rule — always store/compare job IDs, not strings.

**G35 — Equipment Browser job filter (`dialogs/equipment_browser.py`)**
- Filter: `job_id in item["job"]` (trivial with new int IDs). IT_CARD always unfiltered.
- "All Jobs" QCheckBox in search row (hidden for cards, unchecked = job-filtered by default).
- Novice (job 0) is also unfiltered (job 0 appears in no item["job"] lists — treated as all-jobs).

**G36 — Monster Browser filter dropdowns (`dialogs/monster_browser.py`)**
- Race, Element, Size QComboBox added above table. Options derived from live mob data.
- `_apply_filters()` ANDs all four controls (name search + 3 dropdowns).

**G37 — Passives job filter (`sections/passive_section.py`)**
- `_SELF_BUFFS` entries extended with `(source_skill, buff_type)` fields.
- `_MASTERIES` renamed `_PASSIVES`; entries extended with `(max_lv, source_skill)`.
  Sub-header renamed "Passives". `BS_HILTBINDING` added.
- `buff_type`: `"self"` = job-filtered via skill tree; `"party"` = always visible;
  all passives = job-filtered.
- `update_job(job_id)`: calls `loader.get_skills_for_job(job_id)`, checks
  `source_skill in job_skills` per entry. Drops hardcoded `_MASTERY_JOB_FILTER`.
- "Show All" QCheckBox in section header bypasses all job filters.
- Corrections: SC_MAXIMIZEPOWER/OVERTHRUST → BS family; SC_SPEARQUICKEN → Crusader/Paladin;
  SC_ONEHANDQUICKEN → Knight/LK (KN_ONEHAND, Soul Link note in code).
- `dark.qss`: added `passive_sub_separator` style.

---

## Session K

**G16 — Katar second hit (`battle.c:5941-5952 #ifndef RENEWAL`)**
- Formula: `damage2 = max(1, damage * (1 + TF_DOUBLE_level * 2) // 100)`. Normal attacks only (skill_id == 0, W_KATAR).
- CardFix does NOT apply to damage2: flag.lh is set after the CardFix block in battle.c.
- Applied post-pipeline: second hit is derived from the first hit's final PMF.
- `BattleResult` gains `katar_second` and `katar_second_crit: Optional[DamageResult]`.
- `BattlePipeline._katar_second_hit()` static method computes the second-hit PMF.
- `summary_section.refresh()` shows "first + second" in Min/Avg/Max cells when `katar_second` is set.
- `TF_DOUBLE` (Double Attack, max lv 10) added to `_PASSIVES` in `passive_section.py`; job-filtered.
- New gap G44: forge toggle should be restricted to forgeable weapon types — needs DB consolidation first.

**G17 — Forged weapon Verys (`status.c:1634-1643, battle.c:5864 #ifndef RENEWAL`)**
- Forge data stored in card[0]=CARD0_FORGE, card[1]=((sc*5)<<8)+ele, card[2/3]=char_id.
- Star value: sc×5; if ≥15 → 40 (3 crumbs); +10 if ranked blacksmith.
- Applied flat per hit (×div) after AttrFix, before CardFix.
- New modifier `core/calculators/modifiers/forge_bonus.py` (ForgeBonus.calculate).
- Pipeline: ForgeBonus inserted between AttrFix and CardFix in `battle_pipeline.py`.
  `div` taken from `skill_data.get("hit", 1)`.
- `Weapon` gets `forge_sc_count: int` and `forge_ranked: bool`.
- `PlayerBuild` gets `is_forged`, `forge_sc_count`, `forge_ranked`, `forge_element`.
- `resolve_weapon` updated: element priority = manual override > forge_element (when is_forged) > item_db.
- `equipment_section.py`: "Forged" QCheckBox on right_hand row. When checked: hides card row, shows
  forge controls (Crumbs spinner 0–3, Ranked checkbox, Ele combo). Loads/saves via PlayerBuild forge fields.
- Known limitation (G44): forge toggle appears on all right_hand weapons; should be restricted to forgeable types.

---

## Session K2  2026-03-08  claude-sonnet-4-6

**G46 — Active Items section** (`gui/sections/active_items_section.py`)
- New collapsible builder section, collapsed by default, compact_mode=hidden.
- Per-stat spinboxes for: STR/AGI/VIT/INT/DEX/LUK, BATK, HIT, FLEE, CRI, Hard DEF, Hard MDEF, ASPD%, MaxHP, MaxSP.
- Optional Source/Notes QLineEdit.
- Header note documents it as a temporary catch-all.
- `active_items_bonuses: Dict[str,int]` added to `PlayerBuild`; saved/loaded under `"active_items"` key.
- Registered in `panel_container.py` `_SECTION_FACTORY`.

**G47 — Manual Stat Adjustments section** (`gui/sections/manual_adj_section.py`)
- Same layout as G46 without the source field.
- Header note clarifies it's a raw escape hatch; known bonuses belong in proper sections.
- `manual_adj_bonuses: Dict[str,int]` added to `PlayerBuild`; saved/loaded under `"manual_adj"` key.
- Registered in `panel_container.py` `_SECTION_FACTORY`.

**G15 — Bonus stat column redesign** (`gui/sections/stats_section.py` rewritten)
- Bonus spinboxes (6 stats + 7 flat bonuses) removed; replaced by read-only `QLabel` with `objectName="stat_bonus_auto"` (italic, muted color via dark.qss).
- `_bonus_values` / `_flat_values` dicts store current computed values; `_update_totals` uses them.
- `update_from_bonuses(gb, ai, ma)` method: sets label text + tooltip per stat from gear/AI/MA breakdown. Tooltip format: `"Gear: +X  |  Active Items: +Y  |  Manual: +Z"`.
- Flat bonuses now include Hard MDEF (was absent); Soft DEF+ removed (not tracked by any source).
- `collect_into` writes only base stats; `load_build` reads only base stats.
- `main_window._run_status_calc` calls `GearBonusAggregator.compute` separately, then `update_from_bonuses`.
- `_collect_build` and `_on_build_selected` zero legacy `bonus_*` fields to prevent double-stacking with gear.
- SC stat effects (Blessing, IncreaseAgi, etc.) not included — StatusCalculator does not yet expose per-SC contributions; deferred.

**Bug fix — `skill_data` scope error in `battle_pipeline.py`**
- `skill_data` was set in `calculate()` but used in `_run_branch()` — different method, out of scope.
- Fix: `skill_data = loader.get_skill(skill.id)` added at the ForgeBonus step inside `_run_branch`.
- Dead `loader.get_skill(skill.id)` call in `calculate()` (result discarded) replaced with comment.
- This bug was latent from Session K G17 and surfaced when pipeline was triggered from new sections.

**Gaps added this session:**
- G45 — StepsBar step tooltip (not yet implemented)
- G46 — Active Items section (implemented this session)
- G47 — Manual Stat Adjustments section (implemented this session)

---

## Session L  2026-03-08  claude-sonnet-4-6

**G45 — StepsBar step tooltips** (`gui/panel.py` StepsBar.refresh)
- Per-row tooltip built from DamageStep fields: name, formula, value/min_value/max_value, hercules_ref.
- Range shown as "Range: X – Y  (avg Z)" when min≠max; "Value: X" when fixed.
- `QToolTip` dark theme rule added to `dark.qss`.

**G40 — StepsBar expanded state persistence** (`gui/panel.py`)
- `_steps_was_expanded: bool` on Panel stores state when StepsBar is hidden.
- `StepsBar.set_expanded_state(expanded)` restores all three internal fields simultaneously (_expanded, _scroll.setVisible, _bar.set_expanded) without emitting signals.
- `Panel.set_steps_bar_visible(show)`: saves/restores expanded state across panel focus switches.
- `panel_container.py` simplified to single `set_steps_bar_visible` call.

**G39 — Inline equipment dropdown** (`gui/sections/equipment_section.py`)
- `_NoWheelCombo(QComboBox)`: wheelEvent override calls event.ignore() — prevents scroll-wheel changing equipment when scrolling the panel.
- `_load_slot_items(slot_key, job_id)`: returns filtered item list by slot loc + job_id; Assassin dual-wield (job_id in {12, 4013}) adds 1H weapons to left_hand.
- `_repopulate_combo(slot_key)`: clears and rebuilds combo with current job filter, preserving selection.
- `_on_inline_changed(slot_key)`: updates _item_ids, refreshes cards, updates left hand state, emits change.
- `update_for_job(job_id)`: repopulates all combos filtered for new job (wired to build_header.job_changed).
- `load_build`: repopulates all combos with build.job_id before restoring selections.
- `_open_browser`: syncs combo after browser pick (adds item dynamically if not in filtered list).
- QSS rule added for `QComboBox#equip_inline_combo` and `:disabled` state.

**Job ID system fix** (scrapers + GUI)
- Root cause: original scrapers used sequential IDs 23-35 for transcendent classes, colliding with Hercules's actual IDs (Job_SuperNovice=23, Job_Gunslinger=24, Job_Ninja=25). Gunslinger/Ninja items with `Job: { Gunslinger: true }` collapsed to job=[] ("all jobs") instead of being properly restricted.
- Fix: all four scrapers updated to use Hercules constants.conf Job_* values throughout.
- Transcendent classes now use 4008-4021; Gunslinger=24, Ninja=25, Super Novice=23.
- `build_header.py`, `new_build_dialog.py`: job list updated; Super Novice/Gunslinger/Ninja added as selectable.
- `_DUAL_WIELD_JOBS` updated to `{12, 4013}`; equipment browser dual-wield check updated.
- `import_item_db.py`, `import_job_db.py`, `import_skill_tree.py`: all JOB_NAME_TO_ID / _HERCULES_JOB_TO_IDS corrected.
- All three JSON files regenerated: item_db.json, job_db.json, skill_tree.json.
- Extended classes (Taekwon=4046, Star_Gladiator=4047, Soul_Linker=4049, Gangsi=4050, etc.) now have proper IDs — their items correctly filter out for all supported main jobs.
- **Breaking**: saved builds with transcendent job_id values (23-35 old IDs) are invalid and must be recreated.

---

## GUI Design — Buffs & Target State  2026-03-09  claude-sonnet-4-6
ctx_used: 71%

Work items completed (design only — no code written):
- Finalized Buffs section architecture: single `buffs_section` with 9 CollapsibleSubGroups:
  Self Buffs, Party Buffs, Ground Effects, Bard Songs, Dancer Dances, Ensembles,
  Applied Debuffs, Guild Buffs, Miscellaneous Effects
- Designed `CollapsibleSubGroup` widget pattern (proposed: `gui/widgets/collapsible_sub_group.py`)
- Designed `target_state_section` for combat panel: Applied Debuffs + Monster State + Status Ailments stub
- Decided: Songs/Dances split into Bard/Dancer sub-groups with separate caster stat panels
  + per-stat override toggle inline per song row
- Decided: Party Buffs = single 2-column grid, all provider roles mixed for column balance
- Decided: Ground Effects = QComboBox (None/Volcano/Deluge/Violent Gale) + level spinner
- Decided: Eternal Chaos = Applied Debuffs sub-group (both Buffs section and Target State)
- Decided: Manual Adjustments → collapsible sub-group inside build_header (not standalone section)
- Decided: Active Items + Miscellaneous Effects both use named-effect toggle pattern (not spinboxes);
  G46's per-stat spinbox implementation is a placeholder to replace in the same session
- Written full spec to docs/gui_plan.md ("Buffs & Target State — UI Design Spec", ~430 lines)
- Updated docs/session_roadmap.md: UI Grouping Design section replaced with gui_plan.md reference

Files read:
| file | lines | est_tok |
|---|---|---|
| docs/gui_plan.md | ~281 | ~1,124 |
| gui/layout_config.json | 94 | ~470 |
| gui/sections/passive_section.py | 429 | ~3,003 |
| gui/section.py | 178 | ~1,246 |
| docs/session_roadmap.md | ~226 | ~904 |
| docs/buffs/README.md | ~116 | ~464 |
| docs/gaps.md (~2 partial) | ~160 | ~640 |
| docs/completed_work.md | ~1,032 | ~4,128 |
| docs/context_log.md | ~845 | ~3,380 |
| **subtotal reads** | **~3,361** | **~15,359** |

Files edited:
| file | lines | est_tok |
|---|---|---|
| docs/gui_plan.md | +430 net | ~1,720 |
| docs/session_roadmap.md | -40 net | ~160 |
| docs/completed_work.md | +this entry | ~400 |
| docs/context_log.md | +this entry | ~250 |

Files created: none

Total est_tokens: ~15,359 reads + ~2,530 edits + 6,000 fixed + ~25,000 conv ≈ 49,000
Notes: Pure design/planning session. Extended design discussion iterated with user across 8
decision points before writing the spec. Active Items named-effect distinction clarified mid-session.
Next session: concrete design for how buffs/scripts communicate with core pipeline systems.

---

## Session M0 — Buff / Debuff UI Scaffolding

**Goal**: Pure GUI structure work. No SC formula implementations. Create all new section and
widget classes; update layout_config.json and build_header; migrate self-buff rows from
passive_section to buffs_section; migrate Manual Adjustments into build_header sub-group.

**M0-1 — CollapsibleSubGroup widget** (`gui/widgets/collapsible_sub_group.py` + `gui/widgets/__init__.py`)
New widget class (NOT a Section) — clickable header with arrow toggle, content QWidget show/hide.
QSS objectNames: `"subgroup_header"`, `"subgroup_arrow"`, `"subgroup_title"`.
API: `add_content_widget(w)`, `add_header_widget(w)`, `toggle()`, `set_collapsed(bool)`, `is_collapsed`.
No signal propagation to PanelContainer. `default_collapsed` as constructor arg.
`_ClickableFrame` inner class provides `set_click_callback` pattern.
dark.qss: 4 new rules for subgroup header/hover/arrow/title styles.

**M0-2 — buffs_section.py** (`gui/sections/buffs_section.py`, ~170 lines)
8 CollapsibleSubGroups. Self Buffs sub-group fully wired (migrated from passive_section):
- SC_AURABLADE, SC_MAXIMIZEPOWER, SC_OVERTHRUST, SC_OVERTHRUSTMAX, SC_TWOHANDQUICKEN,
  SC_SPEARQUICKEN, SC_ONEHANDQUICKEN — 7 rows with QCheckBox (has_level=False) or QSpinBox (has_level=True).
  Job-filtered via `update_job(job_id)` + `loader.get_skills_for_job()` per source_skill.
  `collect_into`: copies existing `active_status_levels`, removes owned SC keys, re-adds active ones.
Sub-groups 2–8 stubbed with placeholder QLabel (content added in Sessions M, M2, N, O).
compact_mode: `_enter_compact_view`/`_exit_compact_view` with active-buff-names summary label.

**M0-3 — player_debuffs_section.py** (`gui/sections/player_debuffs_section.py`, ~75 lines)
Single CollapsibleSubGroup "Player Debuffs", default_collapsed=False.
`collect_into`/`load_build` are no-ops (Session R adds actual toggles).
compact_mode implemented. Signal: `changed = Signal()`.

**M0-4 — PlayerBuild new fields** (`core/models/build.py`)
```python
support_buffs: Dict[str, object] = field(default_factory=dict)   # party/outgoing buffs
player_active_scs: Dict[str, object] = field(default_factory=dict)  # debuffs applied to player
```
BuildManager: save/load round-trip for both fields; SC_ADRENALINE migration block (moves from
`active_status_levels` → `support_buffs` on load for backward compat with old saves).
status_calculator.py: SC_ADRENALINE check now reads from both `active_status_levels` AND `support_buffs`.

**M0-5 — layout_config.json**
`passive_section` display_name: "Passives & Buffs" → "Passives".
`manual_adj_section` entry removed.
Added after passive_section: `buffs_section` (compact_view, default_collapsed=true) and
`player_debuffs_section` (compact_view, default_collapsed=true).

**M0-6 — build_header Manual Adjustments sub-group** (`gui/sections/build_header.py`)
`ManualAdjSection` content reproduced as a `CollapsibleSubGroup` at the bottom of `BuildHeaderSection`.
15 stat spinboxes (same as old ManualAdjSection). `bonuses_changed = Signal()` added.
`load_build` and `collect_into` updated to handle `build.manual_adj_bonuses`.

**M0-7 — passive_section.py rewrite** (`gui/sections/passive_section.py`)
All `_SELF_BUFFS` data and UI code removed. Now contains only masteries (2-column grid) + Flags.
Removed: QCheckBox, QHBoxLayout, loader imports, show-all checkbox, all buff row logic.
`update_job` now only hides/shows mastery rows. `_build_summary` covers masteries + flags only.
`collect_into` no longer touches `active_status_levels`.

**M0-8 — panel_container.py + main_window.py wiring**
`panel_container.py`: ManualAdjSection → BuffsSection + PlayerDebuffsSection in `_SECTION_FACTORY`.
`main_window.py`: ManualAdjSection → BuffsSection + PlayerDebuffsSection typed refs.
Signal wiring: `job_changed → _buffs_section.update_job`, `bonuses_changed → _on_build_changed`,
`_buffs_section.changed → _on_build_changed`, `_player_debuffs.changed → _on_build_changed`.
`_load_build_into_sections` and `_collect_build` updated accordingly.

---

## Session M — Priest/Sage Party Buffs (2026-03-10)

**Goal**: Party buff SCs in StatusCalculator + Party Buffs sub-group UI.

**M-1 — Data models** (`core/models/status.py`, `core/models/target.py`)
Added `def_percent: int = 100` to both. Mirrors `st->def_percent` (status.c:3872).

**M-2 — StatusCalculator** (`core/calculators/status_calculator.py`)
SC_BLESSING/SC_INC_AGI/SC_GLORIA stat bonuses: folded into `bonus_*` via `_apply_gear_bonuses`
(not in StatusCalculator directly — avoids double-count with display pipeline).
SC_ANGELUS: `def_percent = 100 + 5*level`; `def2 *= def_percent//100` for display.
SC_ADRENALINE: reads `support_buffs["SC_ADRENALINE"]` as raw val3 (300/200); backward-compat
fallback to `active_status_levels` for old saves.
Actual SC key confirmed as `SC_INC_AGI` (not SC_INCREASEAGI). SC_MAGNIFICAT: out of scope.

**M-3 — DefenseFix** (`core/calculators/modifiers/defense_fix.py`)
PC branch: `vit_def = vit_def * target.def_percent // 100` after computing range.
Hard DEF (def1) NOT scaled for PC targets in pre-renewal (battle.c:1492 — only mob/pet path).

**M-4 — build_manager.py** (`core/build_manager.py`)
`player_build_to_target`: added `def_percent=status.def_percent`.

**M-5 — base_damage.py** (`core/calculators/modifiers/base_damage.py`)
SC_IMPOSITIO: reads `support_buffs` first, falls back to `active_status_levels` for old saves.

**M-6 — Party Buffs UI** (`gui/sections/buffs_section.py`)
`_PARTY_BUFFS` table + real widgets replacing stub. SC_BLESSING/INC_AGI/ANGELUS/IMPOSITIO:
QSpinBox(0..max) with "Off" as special value. SC_GLORIA: QCheckBox. SC_ADRENALINE:
QCheckBox + QComboBox("Self"→300, "Party member"→200). Full load/collect round-trip to
`build.support_buffs`. `_party_spins/_party_checks/_party_combos` dicts.

**M-7 — Stat bonus display** (`gui/main_window.py`, `gui/sections/stats_section.py`)
`_sc_stat_bonuses(support_buffs)` static method computes SC stat contributions.
`_apply_gear_bonuses` folds SC bonuses into `bonus_str/agi/int/dex/luk`.
`update_from_bonuses` gains 4th `sc: dict` param; tooltip shows "Buffs: +N" source.

---

## Session M2 — Bard/Dancer Songs

**M2-1 — PlayerBuild.song_state** (`core/models/build.py`)
New `song_state: Dict[str, object]` field. Stores shared caster stats ("caster_agi", "caster_dex", etc.), per-song levels (e.g. "SC_ASSNCROS"), and per-stat overrides (e.g. "SC_ASSNCROS_agi": None = use shared). Separate Bard/Dancer namespacing. Save/load in BuildManager with migration: SC_ASSNCROS level moved from `active_status_levels` → `song_state`.

**M2-2 — StatusData new fields** (`core/models/status.py`)
Three new display-only fields for song effects not simulated in the damage pipeline:
- `cast_time_reduction_pct`: from SC_POEMBRAGI val1 (BA_POEMBRAGI)
- `after_cast_delay_reduction_pct`: from SC_POEMBRAGI val2
- `sp_cost_reduction_pct`: from SC_SERVICEFORYU val3

**M2-3 — StatusCalculator song SCs** (`core/calculators/status_calculator.py`)
Seven song SCs implemented — all read from `build.song_state`:
- SC_ASSNCROS: amotion reduction = `(MusLesson/2+10+song_lv+caster_agi/10)*10`; completes G9~
- SC_WHISTLE: FLEE flat bonus `= song_lv+5+(caster_agi+caster_luk)/10+MusLesson/10`
- SC_APPLEIDUN: MaxHP% `= 5+2*song_lv+caster_vit/10+MusLesson`; applied after HP table calc
- SC_POEMBRAGI: cast time `= 3*song_lv+caster_dex/10+2*MusLesson`; after-cast delay formula
- SC_HUMMING: HIT flat bonus `= song_lv+5+(caster_dex+caster_luk)/10+DanceLesson/10`
- SC_FORTUNE: CRI flat bonus `= (10+song_lv+caster_luk/10+DanceLesson)*10` (÷10 for cri units)
- SC_SERVICEFORYU: MaxSP% + sp_cost_reduction_pct

**M2-4 — base_damage.py song SCs** (`core/calculators/modifiers/base_damage.py`)
- SC_DRUMBATTLE: flat WATK bonus `= (song_lv+1)*25` + DEF bonus `= (song_lv+1)*2` on StatusData.def_percent
- SC_NIBELUNGEN: flat WATK bonus `= (song_lv+2)*25`, gated by `weapon.level == 4`
Both read from `build.song_state`. Source: status.c #ifndef RENEWAL lines 4564/4589.
Note: G51 open — in-game tests suggest SC_NIBELUNGEN bypasses DEF. Awaiting Hercules dev clarification.

**M2-5 — Buffs section UI** (`gui/sections/buffs_section.py`)
Full Bard Songs sub-group: shared caster stats table (agi/dex/vit/int/luk + MusLesson level) + per-song rows (SC_ASSNCROS/WHISTLE/APPLEIDUN/POEMBRAGI + Ensembles). Full Dancer Dances sub-group: shared caster stats (DanceLesson) + per-dance rows (SC_HUMMING/FORTUNE/SERVICEFORYU). Ensembles sub-group: SC_DRUMBATTLE/NIBELUNGEN/SIEGFRIED (level spinbox only, no per-stat override). Job visibility filter: Bard Songs hidden unless job_id in Bard/Clown set; Dancer Dances hidden unless Dancer/Gypsy. SC_SIEGFRIED deferred to Session R (incoming elemental resist).

**M2-6 — derived_section.py** (`gui/sections/derived_section.py`)
New display rows for Poem of Bragi (cast time / after-cast delay) and Service for You (SP cost reduction), wired to new StatusData fields.

---

## Session N — Self-Buffs

**N-0 — Source re-verification + ASPD bug fixes** (`core/calculators/status_calculator.py`)
Session N was initially a partial failure due to ASPD formula errors. All implementations re-verified against Hercules source this session. Three ASPD bugs fixed:
1. SC_GS_MADNESSCANCEL ASPD: was in max pool (`max(sc_aspd_reduction, 200)`). Correct: separate `aspd_rate -= 200` applied AFTER `aspd_rate -= max_pool` (status_calc_aspd_rate:5656-5657). MADNESSCANCEL is NOT in the max pool.
2. SC_STEELBODY ASPD: was `amotion += base_amotion * 25 // 1000` (2.5%, wrong scale). Correct: `sc_aspd_rate += 250` (25% slowdown, status_calc_aspd_rate:5670-5671).
3. SC_DEFENDER ASPD: was using `val4//10` from `#ifdef RENEWAL_ASPD` path (wrong formula). Correct: `sc_aspd_rate += val4 = 250-50×lv` (status_calc_aspd_rate:5674-5675). lv1→+200, lv5→0.
Key discovery: `status_calc_aspd` (`bonus -= N` lines 5496-5501) is entirely `#ifdef RENEWAL_ASPD`. Pre-renewal only uses `status_calc_aspd_rate` (no RENEWAL guard). ASPD section restructured to use `sc_aspd_max` + `sc_aspd_rate` single accumulator.

**N-1 — StatusCalculator self-buff SCs** (`core/calculators/status_calculator.py`)
10 SCs added across 6 groups (confirmed from Hercules source):
- Stat mods (before BATK): SC_SHOUT (str+4, status.c:3956), SC_NJ_NEN (str+lv, int+lv, 3962/4148), SC_GS_ACCURACY (agi+4, dex+4, 4023/4219)
- BATK mods: SC_GS_MADNESSCANCEL (batk+100, #ifndef RENEWAL, 4478), SC_GS_GATLINGFEVER (batk+=val3=20+10×lv, #ifndef RENEWAL, 4480)
- CRI mod: SC_EXPLOSIONSPIRITS (cri+=val2=75+25×lv, 4753)
- HIT/FLEE mods: SC_GS_ACCURACY (hit+20, 4811), SC_GS_ADJUSTMENT (hit-30, flee+30, 4809/4878), SC_RG_CCONFINE_M (flee+10, 4874), SC_GS_GATLINGFEVER (flee-=5×lv, 4882)
- ASPD: SC_GS_MADNESSCANCEL (-200 separate), SC_GS_GATLINGFEVER (in max pool, val2=20×lv), SC_STEELBODY (+250), SC_DEFENDER (+val4=250-50×lv)
- MDEF: SC_ENDURE (mdef+=val1=lv when val4=0, 5149)

**N-2 — Self Buffs UI rows** (`gui/sections/buffs_section.py`)
22 new entries added to `_SELF_BUFFS` (total now 29):
- Full calc: SC_ENDURE, SC_SHOUT, SC_STEELBODY, SC_EXPLOSIONSPIRITS, SC_DEFENDER, SC_GS_MADNESSCANCEL, SC_GS_ADJUSTMENT, SC_GS_ACCURACY, SC_GS_GATLINGFEVER, SC_NJ_NEN, SC_RG_CCONFINE_M
- Stubs (no/partial calc): SC_SUB_WEAPONPROPERTY(Magnum Break), SC_AUTOBERSERK, SC_AUTOGUARD, SC_REFLECTSHIELD, SC_CONCENTRATION(stub — card split needed), SC_ENERGYCOAT, SC_CLOAKING, SC_POISONREACT, SC_RUN(TK_RUN)
- Counters (no SC): MO_SPIRITBALL (spirit spheres, 1-5), GS_COINS (coin count, 1-10)
All rows use existing tuple format (sc_key, display, has_lv, min_lv, max_lv, source_skill); no __init__ changes needed — loops iterate _SELF_BUFFS at construction time.

## Session O — Ground Effects

**O-1 — Hercules source verification** (status.c:7779-7800, skill.c:25192)
All three SC formulas confirmed with direct source reads:
- SC_VOLCANO: val2 = skill_lv * 10 (status.c:7780); pre-renewal: val2=0 if armor ≠ Fire (status.c:7781-7783); applied: watk += val2 (status.c:4569-4570)
- SC_VIOLENTGALE: val2 = skill_lv * 3 (status.c:7786); pre-renewal: val2=0 if armor ≠ Wind (status.c:7788-7790); applied: flee += val2 (status.c:4870-4871)
- SC_DELUGE: val2 = deluge_eff[lv-1] = {5,9,12,14,15}% (skill.c:25192, status.c:7793); pre-renewal: val2=0 if armor ≠ Water (status.c:7795-7797); applied: maxhp += maxhp*val2/100 (status.c:5768-5769)
Pre-renewal element check not enforced in code — user's responsibility. SC_DELUGE has no damage pipeline effect (MaxHP only).

**O-2 — SC_VOLCANO** (`core/calculators/modifiers/base_damage.py`)
Added after SC_NIBELUNGEN block. Reads `build.support_buffs["ground_effect"]=="SC_VOLCANO"` + `ground_effect_lv`. Formula: atkmax += lv*10. DamageStep with Hercules ref.

**O-3 — SC_VIOLENTGALE** (`core/calculators/status_calculator.py`)
Added after SC_GS_GATLINGFEVER flee block. Reads `support["ground_effect"]=="SC_VIOLENTGALE"` + `ground_effect_lv`. Formula: status.flee += lv*3.

**O-4 — Ground Effects UI** (`gui/sections/buffs_section.py`)
Replaced stub (sub-group 3) with real widget: QComboBox (none|Volcano|Deluge|Violent Gale) + QSpinBox Lv 1–5 (enabled when combo ≠ none). Module-level `_GROUND_SC_KEYS = [None, "SC_VOLCANO", "SC_DELUGE", "SC_VIOLENTGALE"]`. Storage: `support_buffs["ground_effect"]` (str|None) + `support_buffs["ground_effect_lv"]` (int). `_on_ground_changed` handler enables/disables level spin. load_build + collect_into wired.

## Session GUI-Adj — Widget Adjustment Pass

**Goal**: Tighten GUI widget usage: spinboxes → dropdowns/toggles where appropriate,
suppress mouse-wheel on all dropdowns, widen spinboxes that were clipping their text.
No calculator changes — pure UI session.

**GUI-Adj-1 — Spinbox → dropdown/toggle conversions**
- `passive_section.py`: `BS_HILTBINDING` (max_lv=1) → `QCheckBox`; all other masteries (max_lv=10) → `_NoWheelCombo` dropdowns ("Off", 1–10). Introduced `_get_mastery_value` / `_set_mastery_value` helpers; removed `QSpinBox` entirely from the file.
- `buffs_section.py` (major rewrite): self-buff level spins → `_NoWheelCombo` (`_sc_combos`); party "spin" type → `_NoWheelCombo` (`_party_level_combos`); song/dance level spins → `_NoWheelCombo` (`_song_level_combos`, `_dance_level_combos`); ensemble spins → `_NoWheelCombo` (`_ensemble_combos`); ground level spin → `_NoWheelCombo` (`_ground_lv_combo`); Musical/Dance Lesson spinbox → `_NoWheelCombo` (0–10). Added `_make_level_combo()` and `_set_combo_value()` helpers. Caster stat spins (1–255) and song override spins (1–255) kept as `QSpinBox` but replaced with `_NoWheelSpin` subclass.

**GUI-Adj-2 — No-wheel on all dropdowns**
`_NoWheelCombo` (ignores `wheelEvent`) added to and used in all files containing `QComboBox`:
- `gui/sections/`: `equipment_section`, `passive_section`, `buffs_section`, `combat_controls`, `build_header`, `incoming_damage`
- `gui/`: `main_window`
- `gui/dialogs/`: `new_build_dialog`, `monster_browser`

**GUI-Adj-3 — Refine spinbox sizing + cap**
`equipment_section.py`: refine spinbox max changed from 20 → **10** (pre-renewal cap); width widened 50 → **58px** (prevents "+10" clipping). Combat controls `_level_spin` width 60 → **68px** (prevents "Lv 10" clipping).

## Session P — Passive Skills Completion

**P-0 — hp_regen + sp_regen** (`core/models/status.py`, `core/calculators/status_calculator.py`, `gui/sections/derived_section.py`)
Two new StatusData fields. Natural tick regen formula from status_calc_regen_pc (status.c:2650–2653, no RENEWAL guard):
- hp_regen = 1 + (vit//5) + (max_hp//200)
- sp_regen = 1 + (int_//6) + (max_sp//100); if int_ >= 120: += ((int_-120)//2) + 4
DerivedSection gains "HP Regen" and "SP Regen" rows displaying "{n}/tick".

**P-1 — PassiveSection new rows** (`gui/sections/passive_section.py`)
16 new rows added to `_PASSIVES` (all with source_skill for job-visibility filtering):
SA_DRAGONOLOGY, AC_OWL, CR_TRUST, BS_WEAPONRESEARCH, AC_VULTURE, GS_SINGLEACTION,
GS_SNAKEEYE, TF_MISS, MO_DODGE, BS_SKINTEMPER, AL_DP, SM_RECOVERY, MG_SRECOVERY,
NJ_NINPOU, NJ_TOBIDOUGU. (BS_HILTBINDING and SA_ADVANCEDBOOK were already in UI.)

**P-2 — StatusCalculator passive stat bonuses** (`core/calculators/status_calculator.py`)
Module-level constants `_GUN_WEAPON_TYPES` and `_TF_MISS_JOBL2` added.
Stat passives (before BATK — affect BATK formula):
- BS_HILTBINDING: STR +1 (status.c:1881); BATK +4 (status.c:1914, #ifndef RENEWAL)
- SA_DRAGONOLOGY: INT += (lv+1)//2 (status.c:1882)
- AC_OWL: DEX += lv (status.c:1884)
DEF passive (conditional on target race via loader.get_monster):
- AL_DP: def2 += lv*(3+(base_level+1)*4//100) vs Demon/Undead (battle.c:1494)
HIT/FLEE passives:
- BS_WEAPONRESEARCH: HIT += lv*2 (#ifndef RENEWAL, status.c:2035)
- AC_VULTURE: HIT += lv (#ifndef RENEWAL, status.c:2039–2042; range bonus not tracked)
- GS_SINGLEACTION: HIT += 2*lv (gun types only, status.c:2047)
- GS_SNAKEEYE: HIT += lv (gun types only, status.c:2049–2051; range bonus not tracked)
- TF_MISS: FLEE += lv*4 if JOBL_2 thief {12,17,4013,4018}, else lv*3 (status.c:2064)
- MO_DODGE: FLEE += (lv*3)>>1 (status.c:2066)
ASPD passives (in sc_aspd_rate block):
- SA_ADVANCEDBOOK: sc_aspd_rate -= 5*lv (W_BOOK only, #ifndef RENEWAL_ASPD, status.c:2116)
- GS_SINGLEACTION: sc_aspd_rate -= ((lv+1)//2)*10 (gun types only, status.c:2120)
MaxHP passive:
- CR_TRUST: max_hp += lv*200 (status.c:1927)

**P-3 — StatusCalculator passive regen bonuses** (`core/calculators/status_calculator.py`)
Added after natural regen block; contribute to hp_regen/sp_regen totals:
- SM_RECOVERY: hp_regen += lv*5 + lv*max_hp//500 (status.c:2691)
- MG_SRECOVERY: sp_regen += lv*3 + lv*max_sp//500 (status.c:2694)
- NJ_NINPOU: sp_regen += lv*3 + lv*max_sp//500 (status.c:2695)

**P-4 — GearBonusAggregator.apply_passive_bonuses()** (`core/gear_bonus_aggregator.py`)
New static method augmenting GearBonuses in-place with passive skill bonuses:
- CR_TRUST: sub_ele["Ele_Holy"] += lv*5 (status.c:2187)
- BS_SKINTEMPER: sub_ele["Ele_Neutral"] += lv; sub_ele["Ele_Fire"] += lv*4 (status.c:2189–2192)
- SA_DRAGONOLOGY: add_race["RC_Dragon"] += lv*4; sub_race["RC_Dragon"] += lv*4 (#ifndef RENEWAL, status.c:2197–2210)
Called after compute() in: battle_pipeline.py (attacker gear_bonuses) and both
player_build_to_target() call sites in main_window.py.

**P-5 — NJ_TOBIDOUGU mastery bonus** (`core/calculators/modifiers/mastery_fix.py`)
Added after ASC_KATAR block: flat +3*lv damage for weapon_type=="Shuriken" (battle.c:844).
Note: "Shuriken" string assumed from naming convention — unverified (G55).

**Deferred (new gaps G52–G55):**
- G52: Dual-wield pipeline (AS_RIGHT/AS_LEFT RH+LH multipliers)
- G53: Falcon/Blitz Beat system (HT_STEELCROW)
- G54: Proc/extra-hit system (GS_CHAINACTION, TF_DOUBLE)
- G55: NJ_TOBIDOUGU "Shuriken" weapon_type string verification

---

## Session G54 — Double-Hit Procs + DPS Stat

**G54-1 — BattleResult new fields** (`core/models/damage.py`)
Added `proc_chance`, `double_hit`, `double_hit_crit`, `dps`, `attacks` fields.
`attacks: List[AttackDefinition]` is the extensible DPS distribution — future branches
append here; Markov seam via `state_requirement`/`next_state` on `AttackDefinition`.

**G54-2 — AttackDefinition model** (`core/models/attack_definition.py`) — new file.
Dataclass: avg_damage, pre_delay (ms), post_delay (ms), chance (steady-state weight).
Markov fields `state_requirement`/`next_state` are commented stubs for future.

**G54-3 — DPS calculator** (`core/calculators/dps_calculator.py`) — new file.
`SelectionStrategy` ABC + `FormulaSelectionStrategy` (pass-through) + `calculate_dps()`.
Correct formula: Σ(chance×dmg) / Σ(chance×delay) × 1000 — NOT Σ(chance×dps_i).

**G54-4 — BattlePipeline proc branches + DPS** (`core/calculators/battle_pipeline.py`)
`_run_branch()` gains `proc_hit_count: int = 1` — applied after SkillRatio (battle.c:5567).
`calculate()` proc block: Knife+TF_DOUBLE and Revolver+GS_CHAINACTION, `proc_chance = 5×lv`.
Probability tree (sums to 1.0): normal-hit, normal-miss, crit (auto-hit, no ×h), proc-hit, proc-miss.
Katar second hit summed into normal_avg/crit_avg before attack list construction.
adelay floored at 200ms. `attacks` stored on `BattleResult`.

**G54-5 — Unit tests** (`tests/test_dps.py`) — new file, new `tests/` directory.
Three tests: single attack, crit scaling, unequal-delay regression guard (asserts
Σ(chance×dps) ≠ correct result — prevents future formula regression).

**G54-6 — SummarySection** (`gui/sections/summary_section.py`)
Double row (pre-allocated, hidden until proc_chance > 0): Min/Avg/Max + "X.X% proc".
Crit% label uses effective_crit = crit_chance × (1 − proc_chance/100).
DPS row (always visible): single value spanning cols 1–3, "0.0" before first result.

---

## Session G52 — Dual-Wield Pipeline (PARTIAL — G52 [~])

**G52-1 — AS_RIGHT / AS_LEFT passive rows** (`gui/sections/passive_section.py`)
Added to `_PASSIVES` list with max_lv=5 and source_skill matching the key.
Job-filtered automatically via `get_skills_for_job` (Assassin / Assassin Cross only).

**G52-2 — LH forge fields on PlayerBuild** (`core/models/build.py`)
Added `lh_is_forged`, `lh_forge_sc_count`, `lh_forge_ranked`, `lh_forge_element` after the RH forge block.
Same semantics as RH block; no `weapon_element` override for LH (uses item_db / forge_element).

**G52-3 — Per-slot forge widgets in equipment_section** (`gui/sections/equipment_section.py`)
Converted forge attributes from single-instance to per-slot dicts:
`_forge_toggles`, `_forge_controls_rows`, `_forge_sc_spins`, `_forge_ranked_chks`, `_forge_element_combos`.
Slot loop guard changed from `slot_key == "right_hand"` to `slot_key in ("right_hand", "left_hand")`.
`_on_forge_toggled(slot_key, checked)` — takes slot_key arg; connected via lambda.
`_refresh_card_slots` uses `_forge_toggles.get(slot_key)` for suppression.
`load_build` restores forge state for both slots via `_forge_state` dict.
`collect_into` uses `_get_forge(slot)` helper for both slots.
`_update_left_hand_state` hides LH forge toggle/controls when 2H weapon blocks slot.

**G52-4 — lh_normal / lh_crit on BattleResult** (`core/models/damage.py`)
Added `lh_normal: Optional[DamageResult] = None` and `lh_crit: Optional[DamageResult] = None`.

**G52-5 — Dual-wield branch in BattlePipeline** (`core/calculators/battle_pipeline.py`)
`_DUAL_WIELD_JOBS = frozenset({12, 4013})` at module level.
`_apply_dualwield_rate(source, numerator, hand, skill_lv)` static helper: scales PMF by numerator/100, floors to min 1, adds DamageStep citing battle.c:5923-5938.
`calculate()` dual-wield block: resolves LH weapon, applies RH rate (50+AS_RIGHT×10)/100 to existing normal/crit, runs separate LH branches and applies LH rate (30+AS_LEFT×10)/100.
DPS `normal_avg`/`crit_avg` sums both hands.
BattleResult returned with `lh_normal=lh_normal, lh_crit=lh_crit`.

**G52-6 — SummarySection RH+LH display** (`gui/sections/summary_section.py`)
Normal and Crit rows show "rh + lh" format when `lh_normal` / `lh_crit` present (same pattern as katar second hit).

**G52-7 — LH card browser EQP fix** (`gui/sections/equipment_section.py`, `gui/dialogs/equipment_browser.py`)
`_open_card_browser` checks if left_hand item has `EQP_WEAPON` in its loc; if so passes `eqp_override={"EQP_WEAPON"}` to dialog.
`EquipmentBrowserDialog.__init__` gains `eqp_override: Optional[set] = None` parameter; overrides `valid_eqp` when provided.

**G52-8 — Monster perfect_dodge fix** (`core/calculators/battle_pipeline.py`)
After `calculate_hit_chance()`, set `perfect_dodge = 0.0` when `build.target_mob_id is not None`.
Monsters have no perfect dodge vs player attacks; only player characters have flee2/perfect_dodge.
Applies to both BF_WEAPON and BF_MAGIC call sites.

---

## Session G52-cont — Dual-Wield: Proc Interaction + ASPD (G52 complete)

**G52-9 — Proc + dual-wield interaction** (`core/calculators/battle_pipeline.py`)
Source read: battle.c:4866-4883 (proc check on RH weapon type only), 5567 (`damage_div_fix` doubles
`wd.damage` = RH only), 5923-5932 (ATK_RATER/ATK_RATEL applied after div fix).
Result: proc doubles RH only; LH contributes its normal (undoubled) value to the proc swing.
In the dual-wield block, after computing `lh_normal`/`lh_crit`, `_apply_dualwield_rate(rh_rate,"RH")`
now also applied to `double_hit` and `double_hit_crit` when both are present.
DPS `double_avg` fixed to include `lh_normal.avg` — proc swing is (RH×2 + LH).
Source ref: battle.c:5151-5153 (ATK_RATER/ATK_RATEL macros), 5567 (damage_div_fix), 5920-5940.

**G52-10 — Summary proc row dual-wield display** (`gui/sections/summary_section.py`)
"Double" row now detects `lh_normal is not None` and shows `"RH×2 + LH"` split format,
matching the Normal row's "rh + lh" pattern. Falls back to single value when not dual-wielding.

**G52-11 — ASPD dual-wield formula** (`core/calculators/status_calculator.py`)
Pre-renewal dual-wield ASPD uses `(aspd_base[RH] + aspd_base[LH]) * 7 / 10`, not just `aspd_base[RH]`.
Source: status.c:3699-3701 (#else, not RENEWAL_ASPD):
  `sd->weapontype > MAX_SINGLE_WEAPON_TYPE → (aspd_base[weapontype1] + aspd_base[weapontype2]) * 7 / 10`
The ASPD block now detects dual-wield (job_id in {12,4013} + LH item equipped + weapon_type != "Unarmed")
and applies the two-weapon formula. Single-weapon path unchanged.
Note: the ×7/10 factor is the intrinsic speed penalty for swinging two weapons; AS_RIGHT/AS_LEFT and
SC_ASSNCROS reduce `amotion` on top of this base.
