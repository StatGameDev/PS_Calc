# PS_Calc — Session Roadmap
_Gap IDs reference `docs/gaps.md`. Pipeline specs in `docs/pipeline_specs.md`._
_GUI layout and widget specs in `docs/gui_plan.md`._
_Core system architecture in `docs/core_architecture.md`._

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
| A | Target model, CardFix | G1–G3, G5, G6, G8, G11 |
| B | BF_MAGIC outgoing pipeline | G18–G25 |
| C | ASC_KATAR mastery, ASPD buffs, bAtkRate | G4, G9~, G10, G42 |
| D | armor_element field, mob ATK investigation | G27 |
| E | Incoming physical + magic pipelines, player_build_to_target | G7, G26–G29, G31–G32 |
| F | Incoming config controls + unified target selector | G43, G30 |
| G | Card slot UI + armor refine DEF | G12, G13 |
| H | PMF foundation: pmf/ package + damage.py + base_damage.py | — |
| I | PMF migration: all 9 modifiers + 4 pipelines; DamageRange removed | — |
| J1 | Skill combo job filter + skill_tree.json scraper | G34 |
| J2 | Equipment browser / monster browser / passives job filters | G35, G36, G37 |
| K | Katar second hit + forged weapon bonus | G16, G17 |
| K2 | ActiveItems + ManualAdj sections + bonus column redesign + skill_data bugfix | G15, G46, G47 |
| L | StepsBar tooltips + state persistence + inline dropdown + job ID system fix | G39, G40, G45 |
| M0 | Buff/Debuff UI scaffolding: CollapsibleSubGroup widget, buffs_section (8 sub-groups, Self Buffs wired), player_debuffs_section, Manual Adj into build_header, passive_section strip | G49~ |
| Design | Buff Architecture Q1–Q5 resolved; decisions written to core_architecture.md | — |
| M | Party Buffs: SC_BLESSING/INC_AGI/GLORIA/ANGELUS/IMPOSITIO/ADRENALINE; def_percent chain; bonus display "Buffs" column | G49~ |
| M2 | Bard/Dancer songs: song_state on PlayerBuild; SC_ASSNCROS/WHISTLE/APPLEIDUN/POEMBRAGI/HUMMING/FORTUNE/SERVICEFORYU in StatusCalculator; SC_DRUMBATTLE+SC_NIBELUNGEN in base_damage.py; Bard Songs+Dancer Dances+Ensembles UI; job visibility filter | G9, G49~ |
| N | Self-Buffs: 10 SCs in StatusCalculator (stat/BATK/CRI/HIT/FLEE/ASPD/MDEF); 3 ASPD bugs fixed (MADNESSCANCEL not in max pool, STEELBODY/DEFENDER scale corrected); 22 new _SELF_BUFFS rows in buffs_section.py | G49~ |
| O | Ground Effects: SC_VOLCANO (base_damage.py, lv*10 WATK); SC_VIOLENTGALE (status_calculator.py, lv*3 FLEE); SC_DELUGE (UI only, MaxHP no damage effect); Ground Effects sub-group wired (QComboBox+QSpinBox). Endows deferred (manual element override sufficient). | G49~ |
| GUI-Adj | Spinbox→dropdowns/toggles, no-wheel on all combos, refine cap +10 | — |
| P | Passive skills: hp/sp regen in StatusData+StatusCalculator+DerivedSection; 16 new passive_section rows; stat/HIT/FLEE/ASPD/regen passives in StatusCalculator; GearBonusAggregator.apply_passive_bonuses() (sub_ele/add_race/sub_race); NJ_TOBIDOUGU in mastery_fix.py. Deferred: G52 dual-wield, G53 falcon, G54 proc/extra-hit, G55 Shuriken type verify. | G50~ |

---

## Session Q1 — Offensive Skill Ratios (Melee Classes)

**Goal**: Complete skill_ratio.py for melee-class offensive skills.
**Classes**: Swordsman, Crusader, Merchant, Blacksmith, Thief, Acolyte, Monk.
**Source**: skill.c → `calc_skillratio` BF_WEAPON path.
**Estimated tokens**: 35–45k.

---

## Session Q2 — Offensive Skill Ratios (Ranged / Magic Classes)

**Goal**: Complete skill_ratio.py for ranged and magic offensive skills.
**Classes**: Hunter, Wizard, Sage, Rogue, Bard/Dancer offensive skills, Ninja, Gunslinger.
**Source**: skill.c → `calc_skillratio` BF_WEAPON / BF_MAGIC paths.
**Estimated tokens**: 35–45k.

---

## Session G54 — Double-Hit Procs + DPS Stat

**Goal**: Model TF_DOUBLE and GS_CHAINACTION as separate proc-fires branches (like
crit), and add a DPS row to SummarySection.
**Gap ID**: G54.
**No Hercules reads needed** — all formulas confirmed 2026-03-11 (see aspd.md, gaps.md).
**Estimated tokens**: ~20–25k (pure Python + GUI, no investigation).

### Work items

1. **`_run_branch()` proc parameter** — add `proc_hit_count: int = 1` to `BattlePipeline._run_branch()`.
   Pass it into `SkillRatio.calculate()` as a multiplier applied at the same position as
   `hit_count` (i.e. `_scale_floor(pmf, proc_hit_count, 1)` after ratio scale).
   This mirrors `damage_div_fix` at battle.c:5567 (#ifndef RENEWAL).

2. **Proc branch in `BattlePipeline.calculate()`** — after the katar_second block,
   add a proc eligibility check (`skill.id == 0` only):
   - W_DAGGER + `build.mastery_levels.get("TF_DOUBLE", 0)` → `proc_chance = 5 * lv`
   - W_REVOLVER + `build.mastery_levels.get("GS_CHAINACTION", 0)` → same formula
   - If `lv > 0`: run `_run_branch(..., proc_hit_count=2)` for normal and (if eligible) crit branches
     → store as `double_hit` / `double_hit_crit` on `BattleResult`

3. **`BattleResult` fields** — add:
   ```python
   proc_chance: float = 0.0          # percent (0–100); 0 = not eligible
   double_hit: Optional[DamageResult] = None
   double_hit_crit: Optional[DamageResult] = None
   ```

4. **Effective crit chance** — crit and proc are mutually exclusive (battle.c:4926).
   When `proc_chance > 0`, the displayed crit% in SummarySection must be scaled:
   `effective_crit_chance = raw_crit_chance * (1 - proc_chance / 100)`
   Store `effective_crit_chance` on `BattleResult` (or compute in summary_section).

5. **DPS architecture** — create two new files:

   **`core/models/attack_definition.py`**:
   ```python
   @dataclass
   class AttackDefinition:
       avg_damage: float
       pre_delay:  float    # ms — cast/startup time before hit (0 for auto-attacks)
       post_delay: float    # ms — after-delay before next action (adelay)
       chance:     float    # steady-state probability weight; must sum to 1.0 across list
       # Future Markov: state_requirement: Optional[str] = None
       # Future Markov: next_state: Optional[str] = None
   ```

   **`core/calculators/dps_calculator.py`**:
   ```python
   class SelectionStrategy(ABC):
       @abstractmethod
       def compute_weights(self, attacks: list[AttackDefinition]) -> list[AttackDefinition]:
           """Return attacks with chance values representing steady-state probability.
           # Future Markov: replace with eigenvector solution over the state graph."""
           ...

   class FormulaSelectionStrategy(SelectionStrategy):
       """Stateless: AttackDefinition.chance values are the steady-state weights.
       Replace with MarkovSelectionStrategy when turn-sequence modelling is added."""
       def compute_weights(self, attacks):
           return attacks

   def calculate_dps(attacks: list[AttackDefinition],
                     strategy: SelectionStrategy) -> float:
       """Correct formula: Σ(chance_i × damage_i) / Σ(chance_i × (pre_i + post_i)).
       Do NOT use Σ(chance_i × dps_i) — incorrect when delays differ between attacks."""
       weighted   = strategy.compute_weights(attacks)
       total_dmg  = sum(a.chance * a.avg_damage               for a in weighted)
       total_time = sum(a.chance * (a.pre_delay + a.post_delay) for a in weighted)
       if total_time == 0:
           return 0.0
       return total_dmg / total_time * 1000   # ms → per-second
   ```

   **Building the attack list in `BattlePipeline.calculate()`**:
   ```python
   adelay = (2000 - status.aspd * 10) * 2   # ms; pre_delay=0 for auto-attacks
   p = proc_chance / 100
   c = effective_crit_chance / 100
   crit_avg   = result.crit.avg_damage if result.crit else result.normal.avg_damage
   double_avg = result.double_hit.avg_damage if result.double_hit else 0.0
   # Miss modelled as zero-damage variant of normal (keeps delay in denominator correct)
   attacks = [
       AttackDefinition(result.normal.avg_damage, 0, adelay, (1-p-c) * hit_chance/100),
       AttackDefinition(result.normal.avg_damage, 0, adelay, (1-p-c) * (1-hit_chance/100)),  # miss
       AttackDefinition(crit_avg,   0, adelay, c   * hit_chance/100),
       AttackDefinition(double_avg, 0, adelay, p   * hit_chance/100),
   ]
   # Future skills: pre_delay = cast_time_ms, post_delay = skill_adelay_ms.
   result.dps = calculate_dps(attacks, FormulaSelectionStrategy())
   ```
   Add `dps: float = 0.0` to `BattleResult`. Drop `attacks_per_sec` — not needed as a
   stored field; it's an intermediate inside `calculate_dps`.

6. **Unit tests — `tests/test_dps.py`** (create `tests/` directory):
   - Basic: single attack type, verify `dps = damage / delay * 1000`.
   - With crit: verify effective_crit_chance scaling.
   - **Unequal-delay edge case**: two attack types with different total delays; assert
     correct result differs from `Σ(chance_i × dps_i)`. Guards against regression.

7. **`SummarySection.refresh()`** — add two rows to the grid:
   - **"Double" row** (row 3): shown only when `result.double_hit is not None`.
     Min/Avg/Max of `double_hit`; column 4 label: `"X.X% proc"`.
     Crit row's percentage label uses `effective_crit_chance` instead of raw.
   - **"DPS" row** (row 4): always shown; single value spanning cols 1–3: `f"{result.dps:.1f}"`.

---

## Session G52 — Dual-Wield Pipeline

**Goal**: Separate RH and LH damage branches for Assassin / Assassin Cross.
**Gap ID**: G52.
**Estimated tokens**: ~35–45k (requires Hercules reads + significant pipeline work).

### Hercules reads needed (first thing in session)

- `battle.c` ~5910–5940: full dual-wield branch — base multipliers for RH/LH without
  mastery, how AS_RIGHT/AS_LEFT are applied, how LH weapon stats are sourced (`sstatus->lhw`).
- Verify whether LH damage goes through a separate `calc_base_damage2` call or is derived
  from the RH result.

### Work items (pending source verification)

1. **AS_RIGHT / AS_LEFT passive rows** — add to `passive_section.py`, job-filtered to
   `_DUAL_WIELD_JOBS = {12, 4013}` (Assassin, Assassin Cross).

2. **LH weapon in pipeline** — verify that `PlayerBuild.equipped["left_hand"]` is already
   populated for dual-wield jobs (Session 5 F6). Resolve the LH weapon via
   `BuildManager.resolve_weapon()` for the LH slot.

3. **`BattlePipeline.calculate()` dual-wield branch** — detect dual-wield
   (`job_id in _DUAL_WIELD_JOBS` and LH weapon present):
   - RH branch: existing `_run_branch()` result, multiplied by `(50 + 10*AS_RIGHT_lv) // 100`
     at the point confirmed by source (likely SkillRatio/base position).
   - LH branch: `_run_branch()` with LH weapon substituted, multiplied by
     `(30 + 10*AS_LEFT_lv) // 100`.
   - Total: RH + LH stored as separate `DamageResult` fields on `BattleResult`.

4. **`BattleResult` fields** — add `lh_normal`, `lh_crit` (Optional[DamageResult]).

5. **`SummarySection`** — when `lh_normal` is present, show "RH: X + LH: Y = Total: Z"
   for Normal and Crit rows.

---

## Session R — Target Debuff System

**Goal**: Allow debuffs from debuff_skills.md to be applied to the target before the
damage pipeline runs, so they modify the target's effective stats.
**Gap ID**: G48.
**Architecture**: New `target_active_scs: dict[str, int]` on Target dataclass.
`player_active_scs` already stubbed on PlayerBuild (Session M0 prereq). DefenseFix /
a new `target_status_calculator.py` reads these SCs and adjusts target DEF, FLEE, element.
**GUI**: Wire `target_state_section` Applied Debuffs + Monster State sub-groups with actual
debuff toggles (SC_PROVOKE, SC_DECREASEAGI, PR_LEXAETERNA, etc.).
Wire `player_debuffs_section` (already scaffolded in M0) with actual debuff toggles
(SC_ETERNALCHAOS, SC_CURSE, SC_BLIND, SC_DECREASEAGI).
Toggles per debuff (PROVOKE, AGIDISCOUNT, etc.) + level spinbox.
Readback regarding player/target differences in implementation (ideally re-use system for both)
**Estimated tokens**: 30–40k (new architecture + UI).

---

## Session GUI-Rework — Widget Architecture Cleanup

**Goal**: Replace all level-selector widgets with a shared `LevelWidget` class;
consolidate the 9 duplicate `_NoWheelCombo`/`_NoWheelSpin` local definitions into
`gui/widgets/`; fix the `isinstance` guard in `_load_song_group` introduced by the
lesson combo living in the caster-spins dict.

**Motivation**: The GUI-Adj session converted all spinboxes to dropdowns but left each
file with its own copy of `_NoWheelCombo` and a bespoke `_make_level_combo` helper.
Future widget-type changes still require touching every call site.

**Work items** (see `docs/gui_plan.md` → LevelWidget Refactor for full spec):
1. Create `gui/widgets/level_widget.py` — `LevelWidget(QComboBox)` with `value()`,
   `setValue()`, `valueChanged` matching QSpinBox API.
2. Export `LevelWidget`, `NoWheelCombo`, `NoWheelSpin` from `gui/widgets/__init__.py`;
   remove the 9 local `_NoWheelCombo`/`_NoWheelSpin` class definitions.
3. Update `passive_section.py` and `buffs_section.py` to use `LevelWidget`; remove
   `_make_level_combo()` helper.
4. Move `mus_lesson` / `dance_lesson` out of `_bard_caster_spins` / `_dancer_caster_spins`
   into dedicated `_bard_lesson: LevelWidget` / `_dancer_lesson: LevelWidget` attributes
   (eliminates the `isinstance` guard in `_load_song_group`).

**Estimated tokens**: ~20–25k (pure GUI, no Hercules reads).

---

## Deferred (Phase 5+ / Advanced Combat Modelling)

| Item | Reason deferred |
|---|---|
| **G41 — PC VIT DEF discrepancy** | LOW PRIORITY. Hercules comment vs C code disagree. Investigate vs official server data before any fix. Currently following C implementation. |
| **Status ailments** (status_skills.md) | Need turn-sequence / hit-count modelling. Phase 5+. |
| **Combo system** (combo_skills.md) | Requires turn-sequence and stance-state modelling. |
| **Healing calculator** (healing_skill.md) | Separate feature mode; 4 skills. |
| **Rebirth / Star Gladiator / Soul Linker** | Not yet in skill_lists; to be added in a future extension session. |
| **Phases 5–8** | Stat Planner, Comparison, Histogram, Config/Scale tabs. |
