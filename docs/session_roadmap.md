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

---

## Session F — Mob skill picker + PvP incoming

**Goal**: Make incoming damage section fully configurable: attack type, ranged flag, PvP.
**Gap IDs**: G43, G30
**Estimated tokens**: ~30–38k (GUI design + wiring; no Hercules greps needed)
**Files to load at start**: `docs/current_state.md`, `docs/gaps.md`

### Design decision (discuss with user before coding)

**G43 simplest working approach** (recommend):
Extend `IncomingDamageSection` header with two additions:
- Physical row: "Ranged" QCheckBox (passes `is_ranged=True` to IncomingPhysicalPipeline →
  activates BF_LONG in CardFix, enabling bLongAtkDef resistance cards)
- Magic row: Element override QComboBox (10 elements, default "mob natural") + optional
  skill ratio QSpinBox 0–1000% (passes to IncomingMagicPipeline as a synthetic SkillInstance)

This avoids needing a mob-skill database. Full mob skill picker is Phase 8 territory.

**G30 simplest working approach**:
Add "PvP Attacker" QComboBox to `IncomingDamageSection` (populated from
`BuildManager.list_builds()`). When a second build is selected, run `BattlePipeline`
with attacker=second build's PlayerBuild, target=`player_build_to_target(current_build)`.
Display result alongside physical incoming. No new pipeline code needed — reuses everything.

### Work items (in order):

1. **G43 — Extend IncomingDamageSection**
   - Add Ranged checkbox; wire to `_on_inputs_changed` → emit `incoming_config_changed(is_ranged, ele_override, ratio_override)`
   - Add magic element override combo + ratio spinbox
   - `main_window.py`: pass `is_ranged` to `IncomingPhysicalPipeline`, `ele_override` + ratio to `IncomingMagicPipeline`
   - `IncomingMagicPipeline`: accept `ele_override: Optional[int]` — use instead of mob natural element when set; accept `ratio_override: Optional[int]` — substitute as skill ratio when set

2. **G30 — PvP attacker combo**
   - Add "PvP Attacker" QComboBox to IncomingDamageSection (below existing content, hidden when empty)
   - Populate from `BuildManager.list_builds()` on open; refresh signal
   - When selection changes: load attacker build → run `BattlePipeline.calculate(attacker_build, player_target, gear_bonuses_attacker, ...)` → display in Physical result panel

### Tests:

**G43 Ranged**
- User: Select mob with known ATK. Equip Raydric Archer Card (bLongAtkDef,20) on player.
  Check "Ranged" → incoming physical drops 20%. Uncheck → returns.

**G43 Magic override**
- User: Select Fire-element mob. Player wears Pasana Card (armor_element=Fire → 0 damage).
  Override magic element to Water → damage is non-zero (player is Water-vulnerable or neutral).

**G30 PvP**
- User: Load agi_bs.json as current build. Select nat_crit_sin.json as PvP attacker.
  Incoming physical step breakdown shows Sin's pipeline (BaseDamage, CardFix attacker+target).

---

## Session F1 — Unified target selector (G30 continuation)

**Goal**: Restructure CombatControls target area; add player build target support; MDef in monster browser.
**Gap IDs**: G30 (target selector redesign)
**Estimated tokens**: ~40–50k (new dialog + combat_controls rewrite + save format + wiring)
**Files to load at start**: `docs/current_state.md`

### Work items (see current_state.md for full code patterns):

1. **G0** — Extend `BuildManager.save_build()` with `cached_display: {job_name, hp, def_, mdef}`
2. **G1** — `monster_browser.py`: insert MDef column after DEF (shift Element/Race/Size/Boss +1)
3. **G2** — New `gui/dialogs/player_target_browser.py` (columns: Name/Job/Lv/HP/DEF/MDEF; reads `cached_display` from JSON)
4. **G3** — Restructure `CombatControlsSection`: mode toggle btn + unified search/list + player entries; `get_target_pvp_stem()`, `refresh_target_builds(pairs)`
5. **G4** — `main_window.py`: replace `TODO(Session F1)` stubs; wire pvp target for both outgoing and incoming

### Tests:
- Mob mode: existing behavior unchanged; monster browser shows MDef column
- Player mode: search filters builds; Browse opens player browser; selecting a build drives outgoing pipeline (player → player_target) and incoming physical (pvp_attacker → player)
- Mode memory: switching Mob↔Player remembers last selection in each mode

---

## Session F2 — F1 overflow (if needed)

If Session F1 runs long, remaining items from F1 carry here.

---

## Session G — Card slots + Armor refine DEF

**Goal**: Complete the equipment system: card sub-slots, armor refine DEF table.
**Gap IDs**: G13, G12 (these two are the same F3 feature — see note in gaps.md)
**Estimated tokens**: ~35–45k (G13 is UI-heavy; G12 needs one config file read + scraper)
**Risk**: If `equipment_section.py` is large, card slot UI alone may fill the session.
  Split plan: if context is tight after G12, defer G13 UI to Session G-part-2.

**Files to load at start**: `docs/gaps.md`, `docs/gui_plan.md` (Equipment System Gaps section)

### Work items (in order):

1. **G12 — Armor refine scraper + pipeline step**
   a. Read `Hercules/db/pre-re/refine_db.conf` — grep for armor refine section
   b. Write `tools/import_refine_db.py`:
      - Parse armor refine DEF table (per refine level, by item grade/type)
      - Output: `core/data/pre-re/tables/refine_armor.json`
   c. Extend `GearBonusAggregator.compute()`:
      - For each armor-class slot (armor, garment, footgear, accessory_l, accessory_r):
        load `refine_armor[grade][refine_level]` and add to `GearBonuses.def_`
      - Use `build.refine_levels[slot]` (already saved/loaded)
   d. Confirm pipeline picks it up via existing `_apply_gear_bonuses()` path in `main_window.py`

2. **G13 — Card slot UI**
   a. In `equipment_section.py`, after each item row, dynamically add 0–N card sub-buttons:
      - `num_slots = loader.get_item(item_id).get("slots", 0)`
      - Each button: small label showing card name (or "—"), opens `EquipmentBrowserDialog`
        filtered to `item_type == IT_CARD`
      - Key scheme: `{slot}_card_0` … `{slot}_card_{N-1}` in `build.equipped`
   b. `GearBonusAggregator.compute()`: already handles any key in `build.equipped` — no change needed
   c. `load_build()` in `equipment_section.py`: read card keys from `build.equipped`; call `_refresh_card_slots()` after item loads
   d. Save schema: card keys are just additional entries in `build.equipped` dict — no `build_manager.py` structural change

### Tests:

**G12**
- User: Equip Full Plate (+0) → note hard DEF. Set refine slider to +10 → DEF increases by correct amount per armor refine table. Cross-check vs irowiki.

**G13**
- User: Equip 4-slot Composite Bow → 4 card sub-slot buttons appear under weapon row.
  Equip Hydra Card (slot 0) → step breakdown shows ×1.20 vs DemiHuman.
  Save → reload → cards persist in correct slots.
  Equip 0-slot item → no card buttons appear.

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