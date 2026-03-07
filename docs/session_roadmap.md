# PS_Calc — Session Roadmap
_Revised after Session E. Sessions A–E complete — see docs/completed_work.md for history._
_Gap IDs reference docs/gaps.md. Pipeline specs in docs/pipeline_specs.md._

---

## Context Budget Reference (from actual session data)

| Session type | Est. tokens | Typical ctx% |
|---|---|---|
| Pure GUI / no Hercules | 20–30k | 40–60% |
| Mixed implementation | 30–40k | 60–80% |
| Investigation-heavy | 40–50k | 80–100% |

**Planning rule**: If a session requires Hercules greps, budget 1–2 greps max alongside
implementation. Never plan investigation + large GUI change + doc maintenance together.
Hit-limit risk rises sharply past 3 Hercules reads in one session.

Fixed overhead per session (CLAUDE.md + system + conversation): ~6k tokens.
Doc maintenance (gaps.md + completed_work.md + context_log.md update): ~3–5k.

---

## Completed Sessions (reference only)

| Session | Primary work | Key gaps closed |
|---|---|---|
| 1–5 | Foundation, GUI Phases 0–4, data scrapers | B3–B9, C3, D1–D5, E1, F2, F5, F6 |
| A | Target model, CardFix, G1/G2/G3/G5/G6/G8/G11 | G1–G3, G5, G6, G8, G11 |
| B | BF_MAGIC outgoing pipeline | G18–G25 |
| C | ASC_KATAR mastery, ASPD buffs, bAtkRate | G4, G9~, G10, G42 |
| D | armor_element field, mob ATK architecture investigation | G27 |
| E | Incoming physical + magic pipelines, player_build_to_target | G7, G26–G29, G31–G32 |
| F | Incoming config controls (ranged/ele/ratio) + unified target selector (Mob↔Player) | G43, G30 |

---

## Session G — Card slots + Armor refine DEF ✓ DONE

**Goal**: Complete the equipment system: card sub-slots, armor refine DEF table.
**Gap IDs**: G12, G13 — both completed.

### What was done:

- **G12**: `tools/import_refine_db.py` scraper + `refine_armor.json` (stats_per_level=66).
  `DataLoader.get_armor_refine_units(r)`. `GearBonusAggregator.compute(equipped, refine_levels)`
  accumulates raw units per IT_ARMOR slot, applies `(total+50)//100` aggregate rounding.
  Source: status.c ~1655,1713. Verified: +10 → 7 DEF (≈ 2/3 per level, matches in-game).
  5 call sites updated in battle_pipeline.py, magic_pipeline.py, main_window.py.

- **G13**: Card sub-slot buttons in `equipment_section.py`. Dynamic count from `item["slots"]`.
  `_refresh_card_slots()` inserts QPushButton (objectName="card_slot_btn", width=72) per slot.
  `_open_card_browser()` opens `EquipmentBrowserDialog(item_type_override="IT_CARD")`.
  `collect_into` / `load_build` round-trip via `{slot}_card_{n}` keys in `build.equipped`.
  Card labels: strip " Card" suffix, truncate to 10 chars.

- **Opportunistic bug fix**: `equipment_browser.py` `EQP_ACC_L`/`EQP_ACC_R` → `EQP_ACC`.
  Both regular accessories and accessory cards use `EQP_ACC` in item_db; old filter produced
  zero results (broken since Phase 1). Also added `item_type_override` param to dialog.

---

## Session H — Job filters (four filter UIs)

**Goal**: Filter skill combo, equipment browser, monster browser, and passives by job.
**Gap IDs**: G34, G35, G36, G37
**Estimated tokens**: ~20–28k (pure GUI, no Hercules; similar pattern × 4)

**Files to load at start**: `docs/gaps.md`

### Work items (in order):

1. **G34 — Skill combo job filter (`combat_controls.py`)**
   Filter `skills.json` entries to jobs matching `build.job_id`.
   Special case: Rogue (job_id 22) and Stalker (job_id 40) include skills with
   `skill_info: ["AllowPlagiarism"]` from any job — add these to their pool.
   Add "Show All" toggle (QCheckBox in section header).

2. **G35 — Equipment Browser job filter (`dialogs/equipment_browser.py`)**
   Filter by `item["job"]` list. Add "All Jobs" toggle in dialog toolbar.
   Trigger: caller passes `job_id` to dialog constructor; dialog filters on open.

3. **G36 — Monster Browser filter dropdowns (`dialogs/monster_browser.py`)**
   Add Race / Element / Size QComboBox above the table.
   Filter logic: AND all active non-"All" dropdowns with name search.
   Numeric column sort already works via `_NumericItem` — no change.

4. **G37 — Passives/Masteries job filter (`passive_section.py`)**
   Hide/disable entries irrelevant to current job.
   Pattern already exists for ASC_KATAR (`_MASTERY_JOB_FILTER` dict + `update_job()`).
   Extend: add job filter maps for all self-buff SCs and mastery skills.
   Add "Show All" override checkbox in Passives section header.

---

## Session I — Polish + pipeline completions

**Goal**: Gear bonus visibility, Katar second hit, forged weapon Verys, minor polish.
**Gap IDs**: G15, G16, G17, G39, G40
**Estimated tokens**: ~28–38k (G16 and G17 each need one Hercules grep; rest is pure GUI)

**Note on Hercules greps**: Grep `battle.c` for G16 and G17 at session start before any
GUI work, so results are in context when needed. Each is a short targeted section.

### Work items (in order):

1. **G16 — E4 Katar second hit**
   Grep: `grep -n "katar" Hercules/src/map/battle.c | grep -i "second\|dual\|hit"`
   Then read the relevant section. Implement as second hit branch result
   (similar to crit branch in `battle_pipeline.py`).

2. **G17 — E6 Forged weapon Verys**
   Grep: `grep -n "[Vv]ery" Hercules/src/map/battle.c | head -20`
   After AttrFix: check `build.equipped` weapon for Verystrong/Verydexterous gemstones;
   add +5 ATK per gemstone. Requires identifying how Hercules stores gemstone count.

3. **G15 — F4 Gear bonus visibility**
   Decide with user: tooltip vs separate "From Gear" row.
   Recommended: add tooltip on each stat total label showing breakdown
   `"Base: X  +Bonuses: Y  +Gear: Z"`. Avoids layout changes.
   In `stats_section.py`: store `gear_bonuses` reference when `apply_gear_bonuses()` is called;
   use it to populate tooltip text on `_total_labels`.

4. **G40 — P1 StepsBar state persistence**
   `Panel.set_visible_bar(True)` currently always calls `reset_steps_to_collapsed()`.
   Add `_steps_was_expanded: bool = False` to `Panel`.
   On hide: save `_steps_was_expanded = self._steps_bar._expanded`.
   On show: restore that state instead of always collapsing.

5. **G39 — F7 Inline equipment dropdown** _(if context allows)_
   Low priority. Add inline QComboBox as quick-select alternative to Edit button.
   Populate from `loader.get_items_by_slot(slot)`. On change: set item ID directly.

---

## Session J — Party buffs

**Goal**: Implement confirmed Bard/Dancer song SCs in StatusCalculator + new Party Buffs UI panel.
**Gap IDs**: G9~ (SC_ASSNCROS), new items for SC_POEMBRAGI, SC_APPLEIDUN, DC_FORTUNEKISS, DC_SERVICEFORYOU
**Estimated tokens**: ~35–45k (new UI sub-section + multiple formula implementations + possible new StatusData fields)

**All confirmed formulas are in `docs/BARD_DANCER_SONGS.md` — no Hercules research needed for these six.**
BA_WHISTLE and DC_HUMMING still need a targeted grep before implementation.

### Design decision (discuss with user before coding):

Add a "Party Buffs" collapsible sub-group to `passive_section.py` (placeholder already exists).
The sub-group needs a "song caster" input panel: AGI, DEX, VIT, INT, LUK spinboxes + song level
per active song + BA_MUSICALLESSON / DC_DANCINGLESSON passive levels.

Alternatively: expose SCs as toggles with manual val2 sliders (simpler; avoids caster stat inputs).
Tradeoff: caster stat inputs are accurate and educational; manual sliders are faster to implement.

### Work items (in order):

1. **Party Buffs UI panel** — add caster stat inputs + per-song enable/level controls to `passive_section.py`

2. **SC_ASSNCROS — complete G9~**
   Formula (from BARD_DANCER_SONGS.md): `val2 = (MusLesson_lv/2 + 10 + song_lv + caster_agi/10) * 10`
   Wire into `status_calculator.py` ASPD reduction block (already scaffolded; currently does nothing).

3. **SC_APPLEIDUN** — MaxHP %: `val1 = 5 + 2*song_lv + caster_vit/10 + MusLesson_lv`
   Apply as `max_hp = max_hp * (100 + val1) // 100` in StatusCalculator.

4. **DC_FORTUNEKISS** — CRI: `val1 = (10 + song_lv + caster_luk/10 + DanceLesson_lv) * 10`
   Apply as flat cri bonus (note: 10× scale → divide by 10 when adding to cri).

5. **DC_SERVICEFORYOU** — MaxSP% + SP cost reduction:
   `val1 = 15 + song_lv + caster_int/10 + DanceLesson_lv/2` (MaxSP%)
   `val2 = 20 + 3*song_lv + caster_int/10 + DanceLesson_lv/2` (SP cost %)
   MaxSP: same pattern as APPLEIDUN. SP cost reduction: new `status.sp_cost_reduction` field if needed.

6. **SC_POEMBRAGI** — cast time + after-cast delay reduction. Requires new StatusData fields
   (`cast_time_reduction_pct`, `after_cast_delay_reduction_pct`) and display rows in derived_section.
   `val1 = 3*song_lv + caster_dex/10 + 2*MusLesson_lv` (cast time %)
   `val2 = (song_lv<10 ? 3*song_lv : 50) + caster_int/5 + 2*MusLesson_lv` (after-cast %)

7. **BA_WHISTLE + DC_HUMMING** — HIT/FLEE/HIT bonuses. Grep first, implement after.

---

## Deferred (requires design session before implementation)

| Item | Reason deferred |
|---|---|
| **C1 — Full variance distribution** | Requires Monte Carlo/convolution design session. Do NOT change `DamageRange` structure until settled. See `docs/gui_plan.md` Session 2 handover. |
| **G41 — PC VIT DEF discrepancy** | LOW PRIORITY. Hercules comment vs C code disagree. Investigate vs official server data before any fix. Currently following C implementation. |
| **Phases 5–8** | Stat Planner, Comparison, Histogram, Config/Scale tabs. |