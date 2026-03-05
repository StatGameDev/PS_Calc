# PS_Calc — Claude Code Instructions

## BEFORE YOU START: Ask First, Search Later

If a task requires locating files, external data, or unfamiliar formats — ask the
user first. The user is present and can provide exact paths, paste file contents,
or answer format questions in one message. Do not spend tokens searching, grepping
speculatively, or reading large files to answer a question the user can answer
instantly.

Examples of when to ask:
- "Where are the downloaded rocalc JS files?" → ask, don't search ~/Downloads
- "What is the array index for weapon refine in rocalc saves?" → ask
- "Which Hercules function handles X?" → grep battle.c once, then ask if not found

When in doubt: one targeted grep or read is fine. Exploratory multi-file searches
are not. Stop and ask after one failed attempt.

---

## Project Overview

Pre-renewal Ragnarok Online toolkit in Python/PySide6.
Goal: faithful Hercules emulator port with full-featured GUI for players and
theorycrafters. Competitive target: rocalc.com. Key differentiator: transparent
damage pipeline with step-by-step breakdown, formula display, and Hercules source
citation.
Reference: Hercules emulator cloned at ./Hercules/. All formulas must be
traceable to source.

---

## Non-Negotiable Rules

- Pre-renewal only.
- Hercules is the source of truth. One targeted grep before asking. No wikis.
- Every DamageStep must cite its source. hercules_ref = exact file + function.
- Python 3.13. No deprecated APIs.
- GUI: PySide6. No CustomTkinter. No raw Tkinter.
- status.int_ not status.int everywhere.

### Renewal vs Pre-Renewal Guards — CRITICAL

- #ifdef RENEWAL — ignore entirely.
- #ifndef RENEWAL — pre-renewal only, implement this.
- No guard — applies to both.

Always check guards before implementing anything:

    sed -n 'START,ENDp' Hercules/src/map/battle.c | grep -n "RENEWAL"

Known renewal-only mechanics (must NOT appear in pre-renewal code):
LUK->HIT, LUK->FLEE, SC_IMPOSITIO ATK_ADD in battle_calc_base_damage2,
SC_GS_MADNESSCANCEL ATK_ADD in battle_calc_base_damage2.

---

## Hercules Source

./Hercules/src/map/ — battle.c, status.c, skill.c, pc.c

    grep -n "function_name" Hercules/src/map/battle.c
    sed -n 'START,ENDp' Hercules/src/map/battle.c

Always grep first. Never load entire files.

---

## GUI Architecture

### Toolkit

- PySide6 — all widgets, layouts, dialogs.
- pyqtgraph — all graphs and plots (Phase 7+). No matplotlib in the GUI layer.
- QSS — all styling via gui/themes/dark.qss. No inline style strings in widget code.

### Layout System

- QSplitter for the left/right panel split. Snap-to ratios on FOCUS button click.
  Draggable divider for custom splits between snap points.
- QScrollArea for each panel's scrollable content.
- Section base class: collapsible header + content frame. Compact-state visibility
  rules driven by layout_config.json, not hardcoded in widget logic.
- layout_config.json in gui/ defines section order, panel assignment, default
  collapsed state, and compact-hidden/compact-collapsed rules. Adding or moving a
  section requires only a JSON edit — no widget code changes.

### Scaling

- UI_SCALE in gui/app_config.py derived from screen DPI at startup.
- Target resolution: 1920x1080. Minimum supported: 1280x720.
- All font sizes, padding, and fixed dimensions derived from UI_SCALE.

### Threading

- Signals and slots only for cross-thread communication. No polling loops.
- Recalculation triggered by signals from build or combat state changes.

### Panel States

Two named focus states serialised as splitter ratios:

- Builder Focused (~38% right): builder panel expanded with full stat editors,
  equipment, and passive sections. Combat panel compact — summary numbers only,
  step breakdown hidden.
- Combat Focused (~22% left): builder compact — read-only stat grid, truncated
  equipment list, buff/mastery summary line only. Combat panel expanded with full
  step breakdown, target info, and incoming damage.

Divider is freely draggable. FOCUS buttons snap to the nearest named ratio.

### Server Mode

- Standard / Payon Stories toggle in the top bar. State stored per build in JSON.
- PS mode applies server-specific overrides via BattleConfig.
- Title bar displays an indicator when Payon Stories mode is active.

---

## Project Structure

    PS_Calc/
    ├── CLAUDE.md
    ├── main.py
    ├── requirements.txt
    ├── saves/                          ← user builds (JSON)
    │   ├── knight_bash.json            ← scaffold (placeholder stats)
    │   ├── spear_peco.json             ← scaffold (placeholder stats)
    │   ├── ak77_hunter.json            ← rocalc import ([MISMATCH] flagged)
    │   ├── dd_sin.json                 ← rocalc import (dual wield)
    │   ├── nat_crit_sin.json           ← rocalc import
    │   ├── agi_bs.json                 ← rocalc import
    │   ├── combo_monk.json             ← rocalc import
    │   └── ip_rogue.json               ← rocalc import
    ├── tools/
    │   ├── import_item_db.py           ← item_db.conf -> item_db.json
    │   ├── import_mob_db.py            ← mob_db.conf -> mob_db.json
    │   └── import_rocalc_saves.py      ← rocalc localStorage -> build JSON
    ├── Hercules/                       ← reference only, never modify
    ├── core/
    │   ├── config.py                   ← BattleConfig (includes critical_min)
    │   ├── data_loader.py              ← singleton; get_monster, get_items_by_type
    │   ├── build_manager.py            ← save/load/resolve_weapon
    │   ├── models/
    │   │   ├── build.py                ← PlayerBuild
    │   │   ├── status.py               ← StatusData (use int_ not int)
    │   │   ├── weapon.py               ← Weapon + RANGED_WEAPON_TYPES
    │   │   ├── skill.py                ← SkillInstance
    │   │   ├── target.py               ← Target (includes luk)
    │   │   └── damage.py               ← DamageResult + BattleResult
    │   ├── calculators/
    │   │   ├── status_calculator.py
    │   │   ├── battle_pipeline.py      ← _run_branch(is_crit) -> BattleResult
    │   │   └── modifiers/
    │   │       ├── base_damage.py      ← is_crit forces atkmax
    │   │       ├── refine_fix.py
    │   │       ├── skill_ratio.py
    │   │       ├── attr_fix.py
    │   │       ├── defense_fix.py      ← is_crit: idef=idef2=1
    │   │       ├── mastery_fix.py
    │   │       ├── active_status_bonus.py
    │   │       ├── crit_chance.py
    │   │       ├── crit_atk_rate.py
    │   │       ├── size_fix.py
    │   │       └── final_rate_bonus.py
    │   └── data/pre-re/
    │       ├── skills.json
    │       ├── db/
    │       │   ├── item_db.json        ← 2760 items (weapon/armor/card/ammo)
    │       │   └── mob_db.json         ← 1007 mobs
    │       └── tables/
    └── gui/
        ├── app_config.py               ← UI_SCALE, theme constants
        ├── layout_config.json          ← section order, panel assignment, compact rules
        ├── themes/
        │   └── dark.qss                ← master stylesheet
        ├── main_window.py              ← QMainWindow, top bar, PanelContainer
        ├── panel_container.py          ← QSplitter wrapper, FOCUS state logic
        ├── panel.py                    ← QScrollArea wrapper, owns Section list
        ├── section.py                  ← Section base class (collapsible)
        └── sections/
            ├── build_header.py
            ├── stats_section.py
            ├── derived_section.py
            ├── equipment_section.py
            ├── passive_section.py
            ├── combat_controls.py
            ├── summary_section.py
            ├── step_breakdown.py
            ├── target_section.py
            └── incoming_damage.py

### Pipeline Step Order

    BaseDamage -> SkillRatio -> DefenseFix -> CritAtkRate (crit only) ->
    RefineFix -> ActiveStatusBonus -> MasteryFix -> AttrFix -> FinalRateBonus

---

## Implementation Phases

### Phase 0 — Foundation
- 0.1 Environment: PySide6 + pyqtgraph in requirements, app_config.py with UI_SCALE
- 0.2 App skeleton: QMainWindow, correct sizing, dark.qss wired in, app launches
- 0.3 Layout system: PanelContainer (QSplitter), Panel (QScrollArea), Section base
      class, layout_config.json read at startup
- 0.4 Build selector bar: top bar with build dropdown reading saves/, server toggle

### Phase 1 — Character Builder Panel
- 1.1 Build Header section
- 1.2 Base Stats section (spinners, stat point counter)
- 1.3 Derived Stats section (read-only, StatusCalculator-driven)
- 1.4 Equipment section (all slots, edit button -> placeholder modal)
- 1.5 Passive section (Self Buffs, Party, Masteries, Flags sub-groups)

### Phase 2 — Combat Analysis: Output
- 2.1 Combat Controls section (skill/target dropdowns, environment radio buttons)
- 2.2 Summary Card section
- 2.3 Step Breakdown section (table, hover tooltips, formula/source toggles)

### Phase 3 — Combat Analysis: Target & Incoming
- 3.1 Target Info section
- 3.2 Incoming Damage section
- 3.3 Custom Target dialog + Load-from-Build path

### Phase 4 — Modals
- 4.1 Equipment Browser
- 4.2 Skill Browser
- 4.3 Monster Browser

### Phase 5 — Stat Planner Tab
- 5.1 Tab infrastructure on the combat panel
- 5.2 Stat Planner content (budget, projections, what-if mode)

### Phase 6 — Comparison Tab
- 6.1 Side-by-side build comparison
- 6.2 Diff highlighting and delta column

### Phase 7 — Advanced Tab & Graphs
- 7.1 Advanced tab (full step breakdown, always-visible fields and variance stats)
- 7.2 pyqtgraph infrastructure
- 7.3 TTK distribution histogram (median, 10th/90th percentile, normal vs crit overlay)

### Phase 8 — Polish & Config
- 8.1 Layout preset system (Build Crafting / Skill Analysis / Optimization)
- 8.2 Resolution scaling verification (1280x720 through 1920x1080)
- 8.3 Payon Stories server mode fully wired into BattleConfig

---

## Key Data Models

### PlayerBuild
- base_X / bonus_X stat split
- equipped: Dict[str, Optional[int]]
- refine_levels: Dict[str, int]
- weapon_element: Optional[int]
- target_mob_id, active_status_levels, mastery_levels
- is_riding_peco, is_ranged_override, no_sizefix
- is_katar — REMOVED, derived from weapon_type == W_KATAR
- server: str — "standard" or "payon_stories"

### BattleResult

    @dataclass
    class BattleResult:
        normal: DamageResult
        crit: Optional[DamageResult]  # None if not crittable
        crit_chance: float
        hit_chance: float             # placeholder, E1 not yet implemented

### Target — pipeline fields
def_, vit, luk, size, race, element, element_level, is_boss, level

### DamageStep — required fields
name, value, note, formula, hercules_ref

### DataLoader (singleton)

    from core.data_loader import loader
    loader.get_monster(mob_id) -> Target
    loader.get_monster_data(mob_id) -> Optional[Dict]
    loader.get_items_by_type(item_type) -> list

### BuildManager
resolve_weapon(item_id, refine=0, element_override=None) -> Weapon
Missing ID -> WARNING + Unarmed fallback (ATK 0, wlv 1, neutral).

### Build File Fields
See build_manager.py for the canonical schema. Fields: name, job_id, base_level,
server, base_stats, bonus_stats, target_mob_id, equipped, refine, weapon_element,
active_buffs, mastery_levels, flags.

---

## Data Architecture

- Build file: stats, item IDs, refine, buffs, masteries, flags, weapon_element,
  target_mob_id, server.
- item_db.json: intrinsic item properties (ATK, type, wlv, element, DEF, scripts).
- mob_db.json: all Target pipeline fields — never hardcode in builds or GUI.

### Parser Completeness Rule
Scrapers capture ALL fields from .conf files. JSON is the authoritative local copy.
Never filter at scrape time. _scraped_at timestamp on every output.

---

## Coding Conventions

- Modifiers: @staticmethod def calculate(...) — no instantiation.
- result.add_step(...) for every calculation — never silently mutate.
- All magic numbers cite Hercules source in comments.
- No global state outside loader; no sudo.
- GUI: no inline style strings — all styling via dark.qss.
- GUI: no business logic in widget classes — widgets emit signals, core handles
  calculation, results pushed back via signals.

---

## Open Items

### C — Pipeline Gaps

C1. Damage Variance — three discrete uniform sources:
- Weapon ATK range: rnd(atkmin, atkmax) — crit forces atkmax
- Overrefine: rnd(1, overrefine_max) — NOT maxed on crit
- VIT DEF: rnd(0, variance_max-1) — bypassed on crit; current avg off by 0.5
Track as (min, max, scale) tuples for closed-form distribution (scaled uniform sum).
Keep variance sources and deterministic multipliers strictly separated.

C2. FinalRateBonus — short/long_damage_rate are map-level in Hercules, not global
BattleConfig. Verify before fixing.

C3. StatusCalculator — ASPD, HP, SP are placeholders.

### D — Data Infrastructure
D4. Card effects — blocked on D5.
D5. Script parsing — late stage, after GUI stable.

### E — Additional Pipeline Mechanics
E1. Hit/Miss — 80 + HIT - FLEE % hit chance; Perfect Dodge 1+[LUK/10]+bonus %.
    hit_chance placeholder on BattleResult. Implement before output is meaningful.
E2. Damage Bonus/Reduction — card/gear size/race/element multipliers, blocked on D5.
E3. Bane skills — Beast/Demon Bane, Dragonology. After VIT DEF, before RefineFix.
E4. Katar second hit — fraction of primary total. Verify fraction from source.
E5. SC_IMPOSITIO in BATK — likely feeds bonus_batk. Verify against source.
E6. Forged weapon Verys — flat +5/Very after elemental modifier.
E7. Cart Revolution double elemental fix.
E8. GS_GROUNDDRIFT — separate 50*lv neutral component with own elemental fix.

---

## Completed Work

- Pipeline core + all modifiers
- A1-A7: formula fixes (int_ rename, SizeFix, pipeline order, refine position,
  DEX scaling)
- B1-B6: data fixes (SC cleanups, preset migration)
- C4, C5: refineable flag, derived is_ranged/is_katar
- C6: crit system (BattleResult, eligibility whitelist, katar bug fix, dual branch)
- D1-D3: scrapers expanded (2760 items: weapon/armor/card/ammo; all mob fields)
- Display fixes: overrefine step restored; SizeFix avg/min collapse fixed
- Test builds: 6 rocalc saves imported; all equipment slots decoded; dual wield
  resolved; item/DB mismatch flagging in place
- Build save/load fully implemented via build_manager.py